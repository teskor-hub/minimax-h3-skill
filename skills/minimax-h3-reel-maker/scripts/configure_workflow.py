"""Create a local H3 package from photos, a prompt and optionally an aligned source.

Never starts ComfyUI, submits jobs, installs dependencies or contacts a server.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import uuid
from PIL import Image
from workflow_api import convert, link_index, required_ancestry, resolution_dimensions
from check_prompt_dialogue import lint_dialogue

SKILL = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            result.update(block)
    return result.hexdigest()

def disconnect(workflow, target_id, input_name):
    nodes = {n["id"]: n for n in workflow["nodes"]}
    slot = next(x for x in nodes[target_id]["inputs"] if x["name"] == input_name)
    edge = slot.get("link")
    slot["link"] = None
    workflow["links"] = [l for l in workflow["links"] if l[0] != edge]
    for node in workflow["nodes"]:
        for output in node.get("outputs", []):
            output["links"] = [i for i in (output.get("links") or []) if i != edge]

def prune(workflow):
    nodes = {str(n["id"]): n for n in workflow["nodes"]}
    links = link_index(nodes, workflow)
    outputs = {i for i, n in nodes.items() if n["type"] == "SaveVideo"}
    keep = required_ancestry(nodes, links, outputs)
    keep.update(i for i, n in nodes.items() if n["type"] == "MarkdownNote")
    workflow["nodes"] = [n for n in workflow["nodes"] if str(n["id"]) in keep]
    workflow["links"] = [l for l in workflow["links"] if str(l[1]) in keep and str(l[3]) in keep]
    valid = {l[0] for l in workflow["links"]}
    for node in workflow["nodes"]:
        for output in node.get("outputs", []):
            output["links"] = [i for i in (output.get("links") or []) if i in valid]
    workflow["last_node_id"] = max(n["id"] for n in workflow["nodes"])
    workflow["last_link_id"] = max(valid)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["auto", "control", "refs"], default="auto")
    parser.add_argument("--source", type=Path, help="Already aligned 24 FPS source clip; only for control mode")
    parser.add_argument("--images", type=Path, nargs="+", required=True, help="Images in exact Picture order")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--megapixels", type=float, choices=[0.2, 1.0], default=1.0)
    parser.add_argument("--slug", required=True, help="Unique reel/attempt name: letters, numbers, underscores or hyphens")
    parser.add_argument("--out", type=Path, required=True, help="New package directory; must not already exist")
    parser.add_argument("--object-info", type=Path, help="Optional object_info JSON from the intended ComfyUI installation")
    args = parser.parse_args()
    mode = ("control" if args.source else "refs") if args.mode == "auto" else args.mode
    if mode == "control" and not args.source:
        parser.error("control mode requires an aligned source; with photos only, use --mode refs or omit --mode")
    if mode == "refs" and args.source:
        parser.error("refs mode uses photos only; omit --source")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.slug):
        parser.error("--slug must contain only letters, numbers, underscores or hyphens")
    minimum = 3 if mode == "control" else 1
    if not minimum <= len(args.images) <= 5:
        parser.error(f"{mode} mode needs {minimum} to 5 ordered photos in this package")
    if not (124 <= args.frames <= 362 and (args.frames - 5) % 17 == 0):
        parser.error("Use an exact 17k+5 length from 124 to 362 frames")
    out = args.out.resolve()
    if out.exists():
        parser.error("Output exists; use a new attempt directory")
    prompt = args.prompt.read_text(encoding="utf-8-sig").strip()
    if "REPLACE_WITH" in prompt or not prompt.endswith("non_diegetic_music:\nN/A"):
        parser.error("Supply a complete prompt ending with non_diegetic_music: then N/A on the next line")
    cited = set(map(int, re.findall(r"<Picture (\d+)>", prompt)))
    if cited != set(range(1, len(args.images) + 1)):
        parser.error("Prompt Picture labels must account for every connected photo, without missing or extra labels")
    errors, dialogue_events = lint_dialogue(prompt)
    if errors:
        parser.error("Dialogue check failed: " + "; ".join(errors))
    width, height = resolution_dimensions(args.megapixels)
    source_info = None
    if args.source:
        result = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(args.source.resolve())], check=True, capture_output=True, text=True, encoding="utf-8")
        if result.stderr.strip():
            parser.error("Source decode produced errors: " + result.stderr.strip())
        source_info = json.loads(result.stdout)
        video = next(s for s in source_info["streams"] if s["codec_type"] == "video")
        measured = (video["width"], video["height"], int(video["nb_read_frames"]), video["avg_frame_rate"])
        if measured != (width, height, args.frames, "24/1"):
            parser.error(f"Source must already be aligned to {(width, height, args.frames, '24/1')}; found {measured}. Do not silently trim, stretch or duplicate frames.")
    template = SKILL / "assets" / ("01_REF_CONTROLNET_TS.json" if mode == "control" else "02_REF_ONLY.json")
    workflow = load(template)
    nodes = {n["id"]: n for n in workflow["nodes"]}
    links = {l[0]: l for l in workflow["links"]}
    for index in range(len(args.images), 5):
        disconnect(workflow, 136, f"ref_images.ref_image_{index}")
    nodes[138]["widgets_values"][0] = prompt + "\n"
    nodes[138]["title"] = args.slug + " — complete prompt"
    nodes[115]["widgets_values"] = ["9:16 (Portrait Widescreen)", args.megapixels, 32]
    nodes[136]["widgets_values"][1:4] = [width, height, args.frames]
    for node in nodes.values():
        if node["type"] == "SaveVideo":
            node["widgets_values"][0] = f"h3_reels/{args.slug}/" + {92: "generated", 181: "pose_control", 183: "depth_control"}[node["id"]]
        if node["type"] == "MarkdownNote":
            node["title"] = args.slug + " — " + mode
            node["widgets_values"] = [f"Mode: {mode}. {args.frames} frames / 24 FPS = {args.frames / 24:.6f} seconds. {len(args.images)} ordered references. Locally configured; live ComfyUI inputs and final GPU quality are not verified."]
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = out.parent / (".preparing_" + args.slug + "_" + uuid.uuid4().hex[:8])
    stage.mkdir()
    media = stage / "comfy_input" / args.slug
    media.mkdir(parents=True)
    refs = []
    for index, original in enumerate(args.images, 1):
        original = original.resolve()
        with Image.open(original) as image:
            image.load()
            size = list(image.size)
        name = f"picture_{index:02d}" + original.suffix.lower()
        target = media / name
        shutil.copy2(original, target)
        socket = next(s for s in nodes[136]["inputs"] if s["name"] == f"ref_images.ref_image_{index - 1}")
        node = nodes[links[socket["link"]][1]]
        node["widgets_values"][0] = args.slug + "/" + name
        node["title"] = f"Picture {index} — " + original.name
        assert digest(original) == digest(target)
        refs.append(dict(picture=index, path="comfy_input/" + args.slug + "/" + name, size=size, sha256=digest(target)))
    audio_conditioning = False
    if args.source:
        source_name = "source_aligned" + args.source.suffix.lower()
        shutil.copy2(args.source, media / source_name)
        nodes[164]["widgets_values"] = [args.slug + "/" + source_name]
        audio_conditioning = any(s["codec_type"] == "audio" for s in source_info["streams"])
        if not audio_conditioning:
            disconnect(workflow, 136, "ref_audios.ref_audio_0")
    workflow["extra"] = dict(controlnet_enabled=mode == "control", handoff=dict(mode=mode, template=False, source_video_required=mode == "control", source_audio_conditioning=audio_conditioning, live_gpu_tested=False))
    prune(workflow)
    if mode == "refs":
        forbidden = {"LoadVideo", "GetVideoComponents", "GetImageSizeAndCount", "ComfyMath", "TSPoseKeypointSmoother"}
        unexpected = [n["type"] for n in workflow["nodes"] if n["type"] in forbidden or any(term in n["type"].lower() for term in ("controlnet", "dwpose", "depthanything"))]
        if unexpected:
            raise ValueError("Photos-only graph contains source/control dependencies: " + ", ".join(unexpected))
        final_video = next(n for n in workflow["nodes"] if n["type"] == "CreateVideo")
        fps_socket = next(s for s in final_video["inputs"] if s["name"] == "fps")
        if fps_socket.get("link") is not None or final_video["widgets_values"][0] != 24:
            raise ValueError("Photos-only output must use a direct 24 FPS value")
    payload = convert(workflow, False, args.object_info)
    schema = payload["extra_data"]["workflow_api_conversion"]["object_info_validation"]
    if schema["status"] == "failed":
        raise ValueError("Live snapshot schema mismatch; no finished package published: " + "; ".join(schema["errors"]))
    write(stage / "workflow.json", workflow)
    write(stage / "api.json", payload)
    (stage / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    write(stage / "package.json", dict(mode=mode, frames=args.frames, fps=24, width=width, height=height, references=refs, source_audio_conditioning=audio_conditioning, generated_audio_connected=True, source_probe=source_info, schema_validation=schema, dialogue_events=dialogue_events, status="OFFLINE_PREPARED_NOT_RENDERED"))
    assert stage.resolve().parent == out.parent and not out.exists()
    stage.rename(out)
    print(json.dumps(dict(status="OFFLINE_PREPARED", mode=mode, references=len(refs), frames=args.frames, source_video_required=mode == "control", output=str(out)), ensure_ascii=True))

if __name__ == "__main__":
    main()
