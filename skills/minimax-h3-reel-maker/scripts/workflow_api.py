#!/usr/bin/env python3
"""Convert the saved 015 Hybrid ComfyUI workflow family into an API payload.

The converter deliberately supports the nodes used by
01_WORKFLOW_015_HYBRID.json.  It does not start ComfyUI or submit a prompt.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from pose_smoother import assert_pose_smoother


# Saved-workflow widgets are positional.  These orders come from the 015
# workflow and the matching 005 API export; values such as RandomNoise's
# trailing "fixed" are UI controls and intentionally have no API input.
WIDGET_INPUTS: dict[str, tuple[str, ...]] = {
    "VAELoader": ("vae_name",),
    "KSamplerSelect": ("sampler_name",),
    "UNETLoader": ("unet_name", "weight_dtype"),
    "CLIPLoader": ("clip_name", "type", "device"),
    "PathchSageAttentionKJ": ("sage_attention", "allow_compile"),
    "BasicScheduler": ("scheduler", "steps", "denoise"),
    "PrimitiveStringMultiline": ("value",),
    "LoadImage": ("image",),
    "RandomNoise": ("noise_seed",),
    "CreateVideo": ("fps", "bit_depth"),
    "SaveVideo": ("filename_prefix", "format", "codec"),
    "MiniMaxH3ReferenceToVideo": ("prompt", "width", "height", "length", "ref_image_size"),
    "H3FunControlLoader": ("control_net_name",),
    "LoadVideo": ("file",),
    "ImageScale": ("upscale_method", "width", "height", "crop"),
    "DepthAnythingV2Preprocessor": ("ckpt_name", "resolution"),
    "DWPreprocessor": (
        "detect_hand", "detect_body", "detect_face", "resolution", "bbox_detector",
        "pose_estimator", "scale_stick_for_xinsr_cn",
    ),
    "TSPoseKeypointSmoother": (
        "filter_extra_people", "smooth_alpha", "gap_frames", "min_run_frames",
        "conf_thresh_body", "conf_thresh_hands", "render_resolution", "smooth_hands",
        "smooth_face",
    ),
    "H3FunControlApply": ("strength", "start_percent", "end_percent"),
    "ComfyMathExpression": ("expression",),
    "ImageFromBatch": ("batch_index", "length"),
    "PrimitiveInt": ("value",),
    "ResolutionSelector": ("aspect_ratio", "megapixels", "multiple"),
    # These 015 nodes receive every API input through workflow links.
    "VAEDecode": (),
    "VAEDecodeAudio": (),
    "BasicGuider": (),
    "SamplerCustomAdvanced": (),
    "GetVideoComponents": (),
    "GetImageSizeAndCount": (),
}

SKIP_TYPES = {"MarkdownNote"}
DYNAMIC_INPUT_PREFIXES = {
    "MiniMaxH3ReferenceToVideo": ("ref_images.", "ref_videos.", "ref_video_audios.", "ref_audios."),
    "ComfyMathExpression": ("values.",),
}


class WorkflowError(RuntimeError):
    pass


RESOLUTION_ASPECT_RATIO = "9:16 (Portrait Widescreen)"
RESOLUTION_MULTIPLE = 32


def resolution_dimensions(megapixels: float) -> tuple[int, int]:
    """Return the server's 9:16 ResolutionSelector dimensions."""
    if megapixels <= 0:
        raise WorkflowError("ResolutionSelector megapixels must be positive")
    scale = math.sqrt(megapixels * 1024 * 1024 / (9 * 16))
    width = round(9 * scale / RESOLUTION_MULTIPLE) * RESOLUTION_MULTIPLE
    height = round(16 * scale / RESOLUTION_MULTIPLE) * RESOLUTION_MULTIPLE
    return width, height


def wire_resolution_selector(workflow: dict[str, Any], megapixels: float) -> tuple[int, int]:
    """Replace template width/height primitives with one ResolutionSelector node."""
    raw_nodes = workflow.get("nodes")
    if not isinstance(raw_nodes, list):
        raise WorkflowError("Saved workflow has no nodes list")
    nodes = {node.get("id"): node for node in raw_nodes if isinstance(node, dict)}
    width_node = nodes.get(115)
    height_node = nodes.get(185)
    if width_node is None or height_node is None:
        raise WorkflowError("ResolutionSelector wiring requires template nodes 115 and 185")
    width, height = resolution_dimensions(megapixels)
    width_links = list((width_node.get("outputs") or [{}])[0].get("links") or [])
    height_links = list((height_node.get("outputs") or [{}])[0].get("links") or [])
    for link in workflow.get("links", []):
        if isinstance(link, list) and len(link) >= 3 and link[1] == 185 and link[2] == 0:
            link[1:3] = [115, 1]
    width_node.update({
        "type": "ResolutionSelector",
        "size": [270, 170],
        "inputs": [],
        "outputs": [
            {"name": "width", "type": "INT", "links": width_links},
            {"name": "height", "type": "INT", "links": height_links},
        ],
        "properties": {"Node name for S&R": "ResolutionSelector"},
        "widgets_values": [RESOLUTION_ASPECT_RATIO, megapixels, RESOLUTION_MULTIPLE],
        "title": "Resolution Selector (Size)",
    })
    workflow["nodes"] = [node for node in raw_nodes if node.get("id") != 185]
    return width, height


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise WorkflowError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"Invalid JSON in {path}: {exc}") from exc


def link_index(nodes: dict[str, dict[str, Any]], workflow: dict[str, Any]) -> dict[int, tuple[str, int]]:
    indexed: dict[int, tuple[str, int]] = {}
    for raw in workflow.get("links", []):
        if not isinstance(raw, list) or len(raw) < 6:
            raise WorkflowError(f"Malformed link: {raw!r}")
        link_id, source_id, source_slot, target_id, target_slot = raw[:5]
        if link_id in indexed:
            raise WorkflowError(f"Duplicate link id {link_id}")
        source_id, target_id = str(source_id), str(target_id)
        if source_id not in nodes or target_id not in nodes:
            raise WorkflowError(f"Link {link_id} references missing node {source_id if source_id not in nodes else target_id}")
        source_outputs = nodes[source_id].get("outputs", [])
        target_inputs = nodes[target_id].get("inputs", [])
        if not isinstance(source_slot, int) or source_slot < 0 or source_slot >= len(source_outputs):
            raise WorkflowError(f"Link {link_id} has invalid source slot {source_slot} on node {source_id}")
        if not isinstance(target_slot, int) or target_slot < 0 or target_slot >= len(target_inputs):
            raise WorkflowError(f"Link {link_id} has invalid target slot {target_slot} on node {target_id}")
        source_link_ids = source_outputs[source_slot].get("links") or []
        if link_id not in source_link_ids:
            raise WorkflowError(f"Link {link_id} is absent from source node {source_id} output slot {source_slot}")
        target_link_id = target_inputs[target_slot].get("link")
        if target_link_id != link_id:
            raise WorkflowError(
                f"Link {link_id} targets node {target_id} slot {target_slot}, but its input records {target_link_id!r}"
            )
        indexed[link_id] = (source_id, source_slot)
    return indexed


def output_targets(nodes: dict[str, dict[str, Any]], controls_only: bool) -> set[str]:
    save_nodes = {node_id: node for node_id, node in nodes.items() if node.get("type") == "SaveVideo"}
    if not save_nodes:
        raise WorkflowError("No SaveVideo output nodes found")
    if not controls_only:
        return set(save_nodes)
    targets = {
        node_id for node_id, node in save_nodes.items()
        if any(token in str(node.get("title", "")).lower() for token in ("pose", "depth"))
    }
    if len(targets) != 2:
        raise WorkflowError(
            "--controls-only requires exactly two SaveVideo nodes titled with pose/depth; "
            f"found {sorted(targets)}"
        )
    return targets


def required_ancestry(
    nodes: dict[str, dict[str, Any]], links: dict[int, tuple[str, int]], targets: set[str]
) -> set[str]:
    required = set(targets)
    pending = list(targets)
    while pending:
        node_id = pending.pop()
        node = nodes[node_id]
        for item in node.get("inputs", []):
            link_id = item.get("link")
            if link_id is None:
                continue
            if link_id not in links:
                raise WorkflowError(f"Node {node_id} input {item.get('name')} references unknown link {link_id}")
            upstream_id, _ = links[link_id]
            if upstream_id not in nodes:
                raise WorkflowError(f"Link {link_id} references missing node {upstream_id}")
            if upstream_id not in required:
                required.add(upstream_id)
                pending.append(upstream_id)
    return required


def widget_values(node: dict[str, Any]) -> dict[str, Any]:
    node_type = node.get("type")
    if node_type not in WIDGET_INPUTS:
        raise WorkflowError(f"Unsupported node type {node_type!r} at node {node.get('id')}")
    values = node.get("widgets_values", [])
    if not isinstance(values, list):
        values = [values]
    names = WIDGET_INPUTS[node_type]
    if len(values) < len(names):
        raise WorkflowError(
            f"Node {node.get('id')} ({node_type}) has {len(values)} widget values; expected at least {len(names)}"
        )
    # Some widgets add UI-only controls after the API inputs (LoadImage's
    # upload selector and RandomNoise/PrimitiveInt's `fixed` control).
    return dict(zip(names, values))


def convert_node(node: dict[str, Any], links: dict[int, tuple[str, int]]) -> dict[str, Any]:
    widget_map = widget_values(node)
    inputs: dict[str, Any] = {}
    input_names = {item.get("name") for item in node.get("inputs", [])}
    for item in node.get("inputs", []):
        name = item.get("name")
        if not name:
            raise WorkflowError(f"Node {node.get('id')} contains an unnamed input")
        link_id = item.get("link")
        if link_id is not None:
            source_id, source_slot = links[link_id]
            inputs[name] = [source_id, source_slot]
        elif name in widget_map:
            inputs[name] = widget_map[name]
    # Primitive nodes in the saved graph have no input descriptor, but their
    # first widget is still the API's `value` input.
    for name, value in widget_map.items():
        if name not in input_names:
            inputs[name] = value
    return {"class_type": node["type"], "inputs": inputs}


def object_info_inputs(schema: dict[str, Any]) -> dict[str, Any]:
    inputs = schema.get("input", {})
    if not isinstance(inputs, dict):
        return {}
    merged: dict[str, Any] = {}
    for section in ("required", "optional", "hidden"):
        section_values = inputs.get(section, {})
        if isinstance(section_values, dict):
            merged.update(section_values)
    return merged


def validate_object_info(prompt: dict[str, Any], object_info_path: Path | None) -> dict[str, Any]:
    if object_info_path is None:
        return {"status": "not_run", "reason": "--object-info was not supplied"}
    info = load_json(object_info_path)
    if not isinstance(info, dict):
        raise WorkflowError(f"Object info must be a JSON object: {object_info_path}")
    errors: list[str] = []
    unchecked_dynamic: list[str] = []
    for node_id, api_node in prompt.items():
        node_type = api_node["class_type"]
        schema = info.get(node_type)
        if not isinstance(schema, dict):
            errors.append(f"node {node_id}: class {node_type!r} absent from object info")
            continue
        schema_inputs = object_info_inputs(schema)
        for name, value in api_node["inputs"].items():
            if name not in schema_inputs:
                prefixes = DYNAMIC_INPUT_PREFIXES.get(node_type, ())
                if any(name.startswith(prefix) for prefix in prefixes):
                    unchecked_dynamic.append(f"node {node_id}: {name}")
                    continue
                errors.append(f"node {node_id}: input {name!r} absent from object info for {node_type}")
                continue
            descriptor = schema_inputs[name]
            if isinstance(descriptor, list) and descriptor and isinstance(descriptor[0], list):
                choices = descriptor[0]
                if not isinstance(value, list) and value not in choices:
                    # LoadImage.VALIDATE_INPUTS checks exists_annotated_filepath,
                    # while its UI enum lists only top-level images. Nested files
                    # are valid; the staging command verifies remote SHA256 and
                    # ComfyUI validates the path again on actual submission.
                    if node_type == "LoadImage" and name == "image":
                        unchecked_dynamic.append(f"node {node_id}: nested image path validated by server: {value}")
                        continue
                    errors.append(f"node {node_id}: {name}={value!r} not in enum {choices!r}")
    status = "passed" if not errors and not unchecked_dynamic else "partial" if not errors else "failed"
    return {"status": status, "path": str(object_info_path), "errors": errors, "unchecked_dynamic_inputs": unchecked_dynamic}


def assert_controlnet_policy(workflow: dict[str, Any]) -> None:
    if workflow.get("extra", {}).get("controlnet_enabled") is not False:
        assert_pose_smoother(workflow)
        return
    forbidden = {"H3FunControlLoader", "H3FunControlApply", "DWPreprocessor", "DepthAnythingV2Preprocessor", "TSPoseKeypointSmoother"}
    nodes = {str(n["id"]): n for n in workflow["nodes"]}
    if any(n["type"] in forbidden for n in nodes.values()):
        raise WorkflowError("No-ControlNet experiment must contain no control or preprocessor nodes")
    links = link_index(nodes, workflow)
    model_input = next(x for x in nodes["144"]["inputs"] if x["name"] == "model")
    if links[model_input["link"]] != ("127", 0):
        raise WorkflowError("No-ControlNet experiment must use the base UNET directly")
    if output_targets(nodes, False) != {"92"}:
        raise WorkflowError("No-ControlNet experiment must render only its final video")


def convert(workflow: dict[str, Any], controls_only: bool, object_info_path: Path | None) -> dict[str, Any]:
    assert_controlnet_policy(workflow)
    raw_nodes = workflow.get("nodes")
    if not isinstance(raw_nodes, list):
        raise WorkflowError("Saved workflow has no nodes list")
    nodes = {str(node.get("id")): node for node in raw_nodes if isinstance(node, dict) and node.get("id") is not None}
    if len(nodes) != len(raw_nodes):
        raise WorkflowError("Every workflow node must be an object with a unique id")
    links = link_index(nodes, workflow)
    selected = required_ancestry(nodes, links, output_targets(nodes, controls_only))
    skipped_notes = sorted(node_id for node_id in selected if nodes[node_id].get("type") in SKIP_TYPES)
    selected.difference_update(skipped_notes)
    unsupported_modes = sorted(
        node_id for node_id in selected if nodes[node_id].get("mode") in (2, 4)
    )
    if unsupported_modes:
        raise WorkflowError(
            "Selected disabled/collapsed mode 2/4 nodes cannot be converted safely: " + ", ".join(unsupported_modes)
        )
    prompt = {node_id: convert_node(nodes[node_id], links) for node_id in sorted(selected, key=int)}
    report = {
        "mode": "controls_only" if controls_only else "full",
        "node_count": len(prompt),
        "node_types": dict(sorted(Counter(node["class_type"] for node in prompt.values()).items())),
        "skipped_markdown_notes": skipped_notes,
    }
    report["object_info_validation"] = validate_object_info(prompt, object_info_path)
    return {
        "prompt": prompt,
        "extra_data": {
            "extra_pnginfo": {"workflow": workflow},
            "workflow_api_conversion": report,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert an 015 Hybrid saved workflow to ComfyUI API payload JSON.")
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_api_json", type=Path)
    parser.add_argument("--controls-only", action="store_true", help="Keep only pose/depth SaveVideo ancestry.")
    parser.add_argument("--object-info", type=Path, help="Optional /object_info JSON snapshot for schema validation.")
    args = parser.parse_args()
    try:
        workflow = load_json(args.input_json)
        if not isinstance(workflow, dict):
            raise WorkflowError("Saved workflow must be a JSON object")
        payload = convert(workflow, args.controls_only, args.object_info)
        report = payload["extra_data"]["workflow_api_conversion"]
        validation = report["object_info_validation"]
        if validation["status"] == "failed":
            raise WorkflowError("Object-info validation failed; API payload was not written: " + "; ".join(validation["errors"]))
        args.output_api_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
