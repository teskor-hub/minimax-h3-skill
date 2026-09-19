# Setup and the two workflows

## The decision

| Input / intent | Use | Required scene inputs |
|---|---|---|
| Reproduce an existing video's motion and shot order | **Ref + ControlNet** | Aligned source video; face + body + one to three native scene photos; pose/depth generated from that video; TS smoothing |
| Create a new scene without a source video | **Ref Only** | One to five relevant reference photos and a text description; no source video, pose, depth, ControlNet, TS smoother or source audio |

An explicit choice wins. Missing source footage selects Ref Only; it is not a reason to stop and demand control maps. Both templates generate native video and audio with the same Ref2VA model family. Motion Strip/Hybrid remain separate historical alternatives outside this two-mode skill.

The established default after the September 12 tests was Ref + ControlNet with TS smoothing. A no-ControlNet reconstruction test rendered but departed from the source's continuity; that does not make photos-only creation invalid. The new **pure photos-only** graph also removes the old test's source-audio and source-derived-length dependencies. Its GPU output has not been tested in this handoff. Do not call it a proven exact-motion replacement.

## Recorded working environment and model files

The accepted source-video baseline ran with ComfyUI **0.34.0**, frontend **1.51.9**, Python **3.12.12**, PyTorch **2.9.1+cu128**, and an **RTX PRO 6000 Blackwell Max-Q with approximately 96 GiB VRAM**. This is a recorded environment, not a minimum requirement or a promise for every card named RTX 6000. The recipient's setup has not been live-tested. Do not automatically replace their working Torch/CUDA stack.

Both modes use these model selections from the accepted graph:

| ComfyUI location | File |
|---|---|
| `models/diffusion_models/` | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` |
| `models/text_encoders/` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` |
| `models/vae/` | `minimax_h3_video_vae_fp16.safetensors` |
| `models/vae/` | `minimax_h3_audio_vae_fp32.safetensors` |

The repository for these files is [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3). Model weights are not included in the skill. Select compatible installed files in the loader widgets. A different quantization is a hardware/quality choice, not a silent filename substitution.

Both supplied graphs retain a disabled `PathchSageAttentionKJ` pass-through node from [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes). KJNodes is therefore still a node dependency of the supplied Ref Only graph. Sage acceleration is **disabled** in this baseline; do not claim that it needs to be enabled. `ResolutionSelector` is a core `comfy_extras.nodes_resolution` node in the recorded environment, not a required third-party quick-resolution plugin.

### Additional requirements for Ref + ControlNet only

- [ComfyUI-H3-FunControl](https://github.com/wyzborrero/ComfyUI-H3-FunControl): `H3FunControlLoader` and `H3FunControlApply`.
- `models/controlnet/minimax_h3_fun_controlnet_union_pruned_bf16.safetensors` from [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental). The original full-width checkpoint is not an interchangeable substitute for this loader path.
- [comfyui_controlnet_aux](https://github.com/Fannovel16/comfyui_controlnet_aux): DWPose and Depth Anything V2. Recorded selections: `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`, `depth_anything_v2_vitb.pth`; preprocessor resolution 576. Use the preprocessor's documented model/cache setup.
- [Teskor's Utils](https://github.com/teskor-hub/comfyui-teskors-utils): **`TSPoseKeypointSmoother`**, accepting DWPose's `POSE_KEYPOINT` output. This is not the separate POSEDATA smoother. The actual keypoint-node source checked on September 19 still has the same nine widgets as this graph; `force_body_18` belongs to the other POSEDATA node. Verify the actual installed schema when upgrading.
- KJNodes also supplies `GetImageSizeAndCount` in this mode.

Install custom nodes into the recipient's own ComfyUI environment using their preferred Manager or repository instructions, then restart ComfyUI. Use that environment's Python for its dependencies. Ref Only does **not** require the three control-related repositories, the union ControlNet weights, or the DWPose/depth model files.

## Recorded settings

| Setting | Value |
|---|---|
| Resolution | `ResolutionSelector`: 9:16, 1 MP, multiple 32 → 768×1376 |
| Requested small check | 0.2 MP → 352×608 with the recorded selector |
| FPS | 24 |
| Length | Valid `17k+5` frames, normally 124–362; 124 = 5.166667 s, 277 = 11.541667 s, 362 = 15.083333 s |
| Sampler / schedule | Euler / normal, 20 steps, denoise 1 |
| Guider | BasicGuider; no separate negative-prompt socket |
| Reference image sizing | `max` in the accepted baseline; can cost more time than `match` |
| Seed | 827616893189874 in the example; choose and record an explicit seed for each comparison |
| Depth / pose | 0.3 / 0.7, both active from 0 to 1 of denoising; only source-video mode |

These are preserved settings, not universal optima. Changing the reference-image-size option, quantization, controls or sampling can change quality and timing. Compare one factor at a time when tuning.

TS keypoint settings: `filter_extra_people=true`, `smooth_alpha=0.7`, `gap_frames=12`, `min_run_frames=3`, `conf_thresh_body=0.35`, `conf_thresh_hands=0.6`, `render_resolution=768`, `smooth_hands=false`, `smooth_face=true`. Hands remain detected/rendered; finger smoothing is disabled. Subject filtering must be reviewed for multi-person scenes.

```text
Source-video mode:
one aligned source → frames → depth preprocessor → resize → depth H3 ControlNet
                            → DWPose KEYPOINTS → TS smoother IMAGE → resize → pose H3 ControlNet
source audio, if present → Ref2VA audio reference → joint sampler
photos + complete prompt → Ref2VA conditioning/latent → joint sampler → native video/audio → SaveVideo

Photos-only mode:
photos + complete prompt + direct length → Ref2VA conditioning/latent
base ref2va model → joint sampler → native video/audio → SaveVideo
```

Both graph branches must refer to the same scene and person. In source-video mode the video is control input, not a Ref2VA `<Video 1>` reference.

## Create a new local package

The helpers need Python 3, Pillow and, for source-video mode, `ffprobe`. Audio/frame preparation additionally uses `ffmpeg`. Run commands from the installed skill directory, or use absolute script paths. No dependency installer or GPU launcher runs automatically.

First write a complete prompt as described in `prompting.md`. The helper creates a new directory and will refuse to overwrite an existing package. Photos retain their original file bytes and dimensions. Names under `comfy_input/<slug>/` prevent collisions between queued reels. Do not reuse the same slug for different inputs on one ComfyUI server.

### Photos only — no video argument

```powershell
python scripts/configure_workflow.py --images "D:\my_reel\portrait.png" --prompt "D:\my_reel\prompt.txt" --frames 124 --slug reel01_attempt01 --out "D:\my_reel\package01"
```

This automatically selects `refs`, disconnects P2–P5, keeps only P1, and sets length directly. With several photos, list them after `--images` in the exact Picture order. No pose/depth/control assets are needed. Use `--mode refs` when an explicit mode flag is helpful.

### Source-video mode

Choose the source interval and a valid frame count first. The helper expects an **already aligned** clip at 24 FPS with the exact requested dimensions/count. It measures decoded frames rather than trusting a container's approximate duration. It refuses silent trim, padding and speed changes.

For a selected interval with enough source frames, this example preserves the full image by proportional resize plus small letterbox padding; change the count/interval for the actual reel:

```powershell
ffmpeg -i "D:\my_reel\source.mp4" -map 0:v:0 -map "0:a?" -vf "fps=24,scale=768:1376:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=768:1376:(ow-iw)/2:(oh-ih)/2,setsar=1" -frames:v 277 -t 11.541666667 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac "D:\my_reel\source_aligned.mp4"
python scripts/configure_workflow.py --source "D:\my_reel\source_aligned.mp4" --images "D:\my_reel\face.png" "D:\my_reel\body.png" "D:\my_reel\scene.png" --prompt "D:\my_reel\prompt.txt" --frames 277 --slug reel02_attempt01 --out "D:\my_reel\package01"
```

The example selects 0–11.541667 s. Do not apply that crop blindly to a different source or silently discard dialogue. Use the same explicit interval for picture/control/audio preparation. If no audio stream exists, the helper disconnects the source-audio input while retaining native generated audio output. Full-body changes, captions and source-frame extraction need visual review, not just a successful command.

For either mode, copy the **contents** of the generated `comfy_input` directory into `ComfyUI/input`, preserving its slug subfolder, and import `workflow.json`. `api.json` is an API payload, not the UI graph. Review model selections and the actual input previews before queueing. `--object-info` can consume a `/object_info` snapshot from the intended ComfyUI instance for additional schema checks; it does not make missing files or model weights appear and may leave dynamic sockets unverified.

## Validation and known limits

The source-video graph descends from a real accepted 015 render, reviewed with dense samples and first/last frames. Portable filenames and generic templates have not been GPU-rendered anew. Pure photos-only wiring is checked locally but no new photos-only GPU result is claimed. A successful script, YAML validator or schema check alone is not an end-to-end model quality test.

The old 265×482 screenshot was replaced by a native 1080×1920 scene frame in the accepted 015 comparison. The duplicate-leg issue disappeared in the reviewed run, but resolution alone was not isolated: composition and encoding changed too. Prefer native original frames, inspect contradictory refs and count limbs in the final video instead of assuming a higher pixel count guarantees success.

Keep exact image-generation prompts and refusal records. A `sexual / output` response identifies a stage/category, not the exact word responsible. Report the missing asset; do not silently redesign the outfit, prop or action. Existing private batch references and generation logs are not part of the public skill.
