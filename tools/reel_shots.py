#!/usr/bin/env python3
"""Break a reference clip into shots so an H3 prompt can be written from what is
actually on screen instead of from memory.

Given a URL or a local file it produces, in one output directory:

  manifest.json   duration, fps, resolution, aspect, detected cut times, per-shot
                  entries with start/end/duration and the frames sampled from each
  frames/         JPEGs at the head, middle and tail of every shot
  audio.wav       16 kHz mono, for listening or transcription (optional)

Nothing here writes a prompt. The point is to replace guessed beat timings with
measured ones — the model reads the frames and the manifest, then writes the
prompt itself. See references/reel-to-prompt.md.

Usage:
    python3 tools/reel_shots.py <url-or-file> [-o OUTDIR] [--threshold 0.30]
                                              [--max-frames 40] [--no-audio]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

FRAME_QUALITY = 3  # ffmpeg -q:v, 2 is best, 5 already visibly soft


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def need(binary):
    if shutil.which(binary) is None:
        sys.exit(f"error: {binary} not found on PATH")


def fetch(source, workdir):
    """Return a local path, downloading first if the source is a URL."""
    if not re.match(r"^https?://", source):
        if not os.path.isfile(source):
            sys.exit(f"error: no such file: {source}")
        return source

    need("yt-dlp")
    target = os.path.join(workdir, "source.%(ext)s")
    print(f"downloading {source}")
    r = run(["yt-dlp", "-q", "--no-warnings", "-f",
             "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b", "-o", target, source])
    if r.returncode != 0:
        sys.exit(f"yt-dlp failed:\n{r.stderr.strip()}")
    files = [os.path.join(workdir, f) for f in os.listdir(workdir)
             if f.startswith("source.")]
    if not files:
        sys.exit("yt-dlp reported success but produced no file")
    return files[0]


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path])
    if r.returncode != 0:
        sys.exit(f"ffprobe failed:\n{r.stderr.strip()}")
    data = json.loads(r.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if video is None:
        sys.exit("error: no video stream")

    num, den = (video.get("avg_frame_rate") or "0/1").split("/")
    fps = round(float(num) / float(den), 3) if float(den) else 0.0
    w, h = int(video["width"]), int(video["height"])
    duration = float(data["format"].get("duration")
                     or video.get("duration") or 0.0)
    return {
        "duration": round(duration, 3),
        "fps": fps,
        "width": w,
        "height": h,
        "aspect": f"{w}:{h}",
        "orientation": "portrait" if h > w else ("square" if h == w else "landscape"),
        "has_audio": audio is not None,
        "video_codec": video.get("codec_name"),
    }


def detect_cuts(path, threshold):
    """Cut timestamps via ffmpeg's scene score. Returns sorted seconds."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-filter_complex", f"select='gt(scene,{threshold})',metadata=print",
             "-an", "-f", "null", "-"])
    times = [float(m) for m in
             re.findall(r"pts_time:([0-9.]+)", r.stderr or "")]
    return sorted(set(round(t, 3) for t in times))


def build_shots(duration, cuts, min_len=0.20):
    """Cut list -> shot list, dropping boundaries too close together."""
    bounds = [0.0]
    for c in cuts:
        if c - bounds[-1] >= min_len and c < duration - min_len:
            bounds.append(c)
    bounds.append(round(duration, 3))

    shots = []
    for i in range(len(bounds) - 1):
        start, end = bounds[i], bounds[i + 1]
        shots.append({
            "shot": i + 1,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
        })
    return shots


def sample_times(shots, max_frames):
    """Head/middle/tail per shot, thinned to a budget, always keeping heads."""
    wanted = []
    for s in shots:
        a, b = s["start"], s["end"]
        pad = min(0.06, s["duration"] / 6)
        picks = [("head", a + pad), ("mid", (a + b) / 2), ("tail", b - pad)]
        for kind, t in picks:
            wanted.append({"shot": s["shot"], "kind": kind, "time": round(max(t, 0.0), 3)})

    if len(wanted) <= max_frames:
        return wanted
    heads = [w for w in wanted if w["kind"] == "head"]
    rest = [w for w in wanted if w["kind"] != "head"]
    room = max_frames - len(heads)
    if room <= 0:
        return heads[:max_frames]
    step = max(1, round(len(rest) / room))
    return sorted(heads + rest[::step], key=lambda w: w["time"])


def extract_frames(path, picks, frames_dir):
    os.makedirs(frames_dir, exist_ok=True)
    written = []
    for i, p in enumerate(picks, 1):
        name = f"{i:03d}_shot{p['shot']:02d}_{p['kind']}_{p['time']:07.3f}s.jpg"
        out = os.path.join(frames_dir, name)
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-ss", str(p["time"]), "-i", path, "-frames:v", "1",
                 "-q:v", str(FRAME_QUALITY), out])
        if r.returncode == 0 and os.path.exists(out):
            written.append({**p, "file": os.path.relpath(out, os.path.dirname(frames_dir))})
    return written


def extract_audio(path, out_wav):
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", path,
             "-vn", "-ac", "1", "-ar", "16000", out_wav])
    return out_wav if r.returncode == 0 and os.path.exists(out_wav) else None


def grid_options(duration, fps=24):
    """H3 accepts frame counts of the form 17k+5. Bracket the source duration."""
    counts = [n for n in range(5, 400) if n % 17 == 5]
    out = []
    for n in counts:
        secs = n / fps
        if duration - 3 <= secs <= duration + 3:
            out.append({"frames": n, "seconds": round(secs, 2)})
    if not out:  # source far outside the useful range
        nearest = min(counts, key=lambda n: abs(n / fps - duration))
        out = [{"frames": nearest, "seconds": round(nearest / fps, 2)}]
    return out


def main():
    ap = argparse.ArgumentParser(description="Break a reference clip into shots.")
    ap.add_argument("source", help="URL or path to a video file")
    ap.add_argument("-o", "--outdir", default="reel_analysis")
    ap.add_argument("--threshold", type=float, default=0.30,
                    help="scene-change sensitivity, 0.2 catches more, 0.4 fewer")
    ap.add_argument("--max-frames", type=int, default=40)
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    need("ffmpeg")
    need("ffprobe")
    os.makedirs(args.outdir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        path = fetch(args.source, tmp)
        info = probe(path)
        print(f"{info['duration']}s  {info['width']}x{info['height']} "
              f"{info['orientation']}  {info['fps']}fps  "
              f"audio={'yes' if info['has_audio'] else 'no'}")

        cuts = detect_cuts(path, args.threshold)
        shots = build_shots(info["duration"], cuts)
        print(f"{len(cuts)} cut(s) detected -> {len(shots)} shot(s)")

        picks = sample_times(shots, args.max_frames)
        frames = extract_frames(path, picks, os.path.join(args.outdir, "frames"))
        print(f"{len(frames)} frame(s) written")

        audio_rel = None
        if info["has_audio"] and not args.no_audio:
            wav = extract_audio(path, os.path.join(args.outdir, "audio.wav"))
            audio_rel = os.path.basename(wav) if wav else None

        for s in shots:
            s["frames"] = [f["file"] for f in frames if f["shot"] == s["shot"]]

        manifest = {
            "source": args.source,
            "media": info,
            "cuts": cuts,
            "shots": shots,
            "audio": audio_rel,
            "h3_length_options": grid_options(info["duration"]),
            "note": "Frame times are measured, not estimated. Write beats from "
                    "these, and pick length from h3_length_options.",
        }
        with open(os.path.join(args.outdir, "manifest.json"), "w") as fh:
            json.dump(manifest, fh, indent=2)

    print(f"\nwrote {args.outdir}/manifest.json")
    print(f"      {args.outdir}/frames/")
    if audio_rel:
        print(f"      {args.outdir}/{audio_rel}")
    print("\nshot table:")
    for s in shots:
        print(f"  shot {s['shot']:>2}  {s['start']:>7.3f} - {s['end']:>7.3f}  "
              f"({s['duration']:>5.2f}s)  {len(s['frames'])} frame(s)")
    print("\nH3 length options near this duration:")
    for o in manifest["h3_length_options"]:
        print(f"  {o['frames']:>3} frames = {o['seconds']}s")


if __name__ == "__main__":
    main()
