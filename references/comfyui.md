# MiniMax H3 in ComfyUI — models, quants, settings

## Repository layout

All files live in [`Comfy-Org/MiniMax-H3`](https://huggingface.co/Comfy-Org/MiniMax-H3). The repo's directory names match ComfyUI's `models/` subfolders exactly, so a single download with paths preserved lands everything correctly.

### Diffusion models — `models/diffusion_models/`

Two checkpoint families. **Different weights, not modes.**

| File | Size |
|---|---|
| `minimax_h3_fl2va_bf16.safetensors` | 66.28 GB |
| `minimax_h3_fl2va_int8_convrot.safetensors` | 34.04 GB |
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 20.97 GB |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | 20.96 GB |
| `minimax_h3_ref2va_bf16.safetensors` | 66.28 GB |
| `minimax_h3_ref2va_int8_convrot.safetensors` | 34.04 GB |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | 20.97 GB |
| `minimax_h3_ref2va_pruned_fp8_scaled.safetensors` | 20.96 GB |

- **`fl2va`** — first/last frame → video+audio. Powers T2V, I2V and FLF2V.
- **`ref2va`** — reference → video+audio. Powers R2V.
- `va` = video+audio, because H3 generates both in one pass.
- **`convrot`** — rotation-based quantisation (Hadamard/QuaRot family). Holds quality better than plain INT8 at the same bit width and does not need FP8 hardware.
- **`pruned`** — drops precomputed adaLN curve tables, roughly 40 % smaller than the same INT8 checkpoint.
- **`fp8_scaled`** — alternative at the same size for FP8-native GPUs (Ada, Blackwell).

### Text encoder — `models/text_encoders/`

Qwen3-VL-32B, **shared by all four modes**. Switching between I2V and R2V changes only the diffusion checkpoint.

| File | Size |
|---|---|
| `qwen3vl_32b_minimax_h3_bf16.safetensors` | 51.51 GB |
| `qwen3vl_32b_minimax_h3_int8_convrot.safetensors` | 27.14 GB |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 15.69 GB |

`nvfp4_awq` is NVIDIA FP4 with activation-aware weight quantisation — natively fast on Blackwell, emulated (slow) on Ampere.

**Encoder precision matters more in R2V than in I2V.** Reference images are tagged in the prompt as `<Picture 1>`, i.e. they enter as multimodal context through the VLM. Identity flows through the encoder. In I2V the conditioning frame enters through the VAE latent path instead, so the encoder carries less of the likeness.

### VAEs — `models/vae/`

Both required, one variant each, nothing to choose.

| File | Size |
|---|---|
| `minimax_h3_video_vae_fp16.safetensors` | 5.21 GB |
| `minimax_h3_audio_vae_fp32.safetensors` | 0.61 GB |

## Choosing a build

| VRAM | Diffusion | Encoder | Notes |
|---|---|---|---|
| 96 GB (RTX PRO 6000 Blackwell) | `bf16` | `bf16` | 66 + 51 GB exceed VRAM together, but ComfyUI loads the encoder, encodes, frees it, then loads the diffusion model. Needs plenty of system RAM. Do **not** pass `--highvram`. |
| 48 GB (RTX 6000 Ada, A6000) | `int8_convrot` | `int8_convrot` | comfortable, no swapping |
| 24 GB | `pruned_int8_convrot` | `nvfp4_awq` | the official template default |
| 16 GB | `pruned_int8_convrot` | `nvfp4_awq` | works with layerwise offload; expect minutes per clip |

Total disk: ~124 GB for the full bf16 set, ~42.5 GB for the 24 GB-class set. Add another 21–66 GB if you want both `fl2va` and `ref2va`.

### Download

```bash
pip install -U "huggingface_hub[hf_transfer]"
export HF_HUB_ENABLE_HF_TRANSFER=1

hf download Comfy-Org/MiniMax-H3 \
  diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors \
  text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors \
  vae/minimax_h3_video_vae_fp16.safetensors \
  vae/minimax_h3_audio_vae_fp32.safetensors \
  --local-dir /path/to/ComfyUI/models
```

## Node settings

Official template defaults (`video_minimax_h3_r2v.json`):

```
UNETLoader          minimax_h3_ref2va_pruned_int8_convrot.safetensors, weight_dtype default
CLIPLoader          qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, type minimax, device default
KSamplerSelect      res_multistep
BasicScheduler      simple, steps 20, denoise 1.0
BasicGuider         (no negative input — CFG is effectively 1)
RandomNoise         seed, randomize
MiniMaxH3ReferenceToVideo   prompt, 1344 × 768, length 124, ref_image_size match
CreateVideo         24 fps, bit_depth 8
```

### What to leave alone

**Steps: 20.** `res_multistep` is a higher-order multistep sampler and converges roughly twice as fast as Euler — 20 steps here is equivalent to 35–40 on `euler`. Raising to 30 costs 50 % more time for a difference you will not see. Steps are the most overrated knob in video generation: time scales linearly, quality plateaus.

**Denoise 1.0.** Only lower it for video-to-video.

**`BasicGuider`.** H3 is trained for CFG 1. Swapping in `CFGGuider` to get a negative prompt doubles inference time (two forward passes per step) and can destabilise a model that never saw guidance during training.

**24 fps / bit_depth 8.** Standard. 16-bit only matters if you are grading downstream.

### What to actually tune

**`scheduler`: try `beta` or `normal` against `simple`.** On reference-heavy graphs — which R2V always is — `res_multistep` paired with `beta` or `normal` often beats the default `simple`. This is the one setting on the sampling panel worth an A/B at a fixed seed.

**`ref_image_size`: `match` → `max`** for the final render. It holds identity noticeably better than any sampler change — but reference tokens are re-attended at every sampling step, so `max` can be several times slower. Iterate on `match`, finish on `max`. Full decision table below.

**`length`.** 124 frames at 24 fps = 5.17 s. Match this to the timeline in the prompt — a 15-second description rendered at 124 frames gets compressed into a frantic 5 seconds. Long or complex camera moves want 192–243 frames; short moves stay crisper at 124. Values snap **up** to the `17k+5` grid, so pick from it directly (table below).

**Seed → `fixed`** the moment output is close. Debugging a prompt against moving noise is guesswork.

**Resolution last.** It hits VRAM harder than anything else.

**Sage Attention**, if installed, roughly doubles generation speed with minimal quality loss. Blackwell needs SageAttention 2++ or 3.

## R2V input wiring

`MiniMaxH3ReferenceToVideo` accepts up to **9 images, 3 videos, 3 video soundtracks and 3 standalone audio clips** — verified against the node's auto-grow schema. The node tooltip gives reference video as 2–15 s. The often-quoted "12 files total" and "15 s combined" caps come from community write-ups rather than MiniMax or the ComfyUI source; treat them as approximate. Standalone audio must accompany at least one image or video.

Prompt tags `<Picture 1>`, `<Video 1>`, `<Audio 1>` are numbered **per type, by slot index, within a fixed category order** — images, then videos with their soundtracks, then standalone audio. Moving an asset between slots reassigns the roles without touching the prompt, which is a subtle and very annoying source of "the prompt suddenly stopped working".

### How ComfyUI actually feeds the model

Read from `comfy/text_encoders/minimax.py` and `comfy_extras/nodes_minimax_h3.py`. This settles several things that are otherwise guesswork.

**There is no prompt rewriter.** MiniMax's guides describe the output format of their rewriting model, but ComfyUI has no such stage — your text is tokenized verbatim and appended to the token stream. The encoder docstring is explicit: *"The H3 presentation is NOT chat-templated: token ids are raw prompt/label text (no special tokens)"*. So writing in the documented format yourself is not optional polish; it is the only way the prompt lands in the distribution the model was trained on.

**The alignment instruction is not emitted for you.** ComfyUI prepends only the picture label and the image itself. The `For the target video, at 0.00 seconds…` and `How the reference pictures align…` lines from the base guide are *your* text — type them as the first line of the prompt box, then a blank line, then the fields.

**ComfyUI injects the reference labels itself, before your prompt:**

```
t2va:   <prompt>
fl2va:  "<Picture 1>: " <vision block> ["<Picture 2>: " <vision block>] <prompt>
ref2va: image -> "<Picture i>: " <vision block>
        audio -> "<Audio j>: "                     (audio never enters Qwen)
        video -> "<Video k>: " then, per 2-frame block, "<T.T seconds>" <vision block>
        then <prompt>
```

Ordinals are 1-based **per type**, and the order is **fixed by category, not by wiring**: all images first, then videos, then standalone audio. The node docstring is explicit — *"References enter the presentation in fixed order: images, then videos (each soundtrack's `<Audio j>` label right before its `<Video k>`), then standalone audio."*

Two practical consequences:

- **A reference video's soundtrack claims `<Audio 1>`**, ahead of any standalone audio clip, and its label sits immediately *before* that video's own `<Video k>`. Attach a soundtrack and your standalone audio silently becomes `<Audio 2>`.
- **Numbering follows slot index, not the order you wired things.** Moving an image from `ref_image_2` to `ref_image_0` renumbers it, and your prompt now points at the wrong asset without a single character changing.

The node's own description says it plainly: *"Use the same tags when prompting."*

**Slot maxima:** 9 images, 3 videos, 3 video soundtracks, 3 standalone audio. These are auto-grow sockets, so a fresh node showing three image inputs is not the ceiling — connect one and the next appears.

**Reference audio never reaches the text encoder.** Only the bare label `<Audio j>: ` is emitted into the token stream; the waveform is encoded by the audio VAE and handed to the DiT separately. Referring to `<Audio 1>` in the prompt is a pointer, not a description the encoder can read — so audio references cannot carry semantic structure through the prompt path.

**Reference video is downsampled to 2 fps for the encoder.** Frames are sampled every 12th frame and grouped into 2-frame temporal blocks, each preceded by a `<T.T seconds>` timestamp. A 5-second clip therefore reaches Qwen as roughly ten frames in five vision blocks — still more identity signal than a single still, but far less than the full clip. Reference videos need at least 5 frames.

**`ref_image_size` in exact terms**, both down-scale only:

- `match` — `scale = min(1, sqrt((width × height) / (w × h)))`, aspect-preserving, to the generation's pixel *area*
- `max` — `scale = min(1, 2048 / min(w, h))`, short edge up to 2048 px

Both are wrapped in `min(1, …)`, so neither ever upscales. At the default 1344 × 768 canvas the generation area is 1.03 MP, which gives a clean decision table:

| Source reference | `match` | `max` |
|---|---|---|
| ≤ 1.03 MP (roughly 880 × 1170 and below) | untouched | untouched |
| 1–5.6 MP, short edge ≤ 2048 | shrunk to 1.03 MP | untouched |
| short edge > 2048 (a phone original at 3000 × 4000) | shrunk to ~1 MP | short edge held at 2048 |

**Set `max` when you care about likeness** — it is never *worse* than `match` for fidelity, only equal or better.

But weigh the cost, because the node's own tooltip is blunt about it: *"Reference tokens ride through every sampling step, so 'max' can be **several times slower**."* This is not merely a VRAM bump — those tokens are re-attended at every one of the 20 steps. On a large reference set the difference is minutes per clip.

And it only *does* anything above about a megapixel. Feed a screenshot or a saved social-media image at 800 × 1000 and the two settings produce byte-identical results at identical speed; the fix there is a higher-resolution source, not a different setting.

Practical order: iterate motion and composition on `match`, switch to `max` for the final render once the shot is right. Paying several times the render cost on throwaway test generations is the wrong trade.

**Native canvas.** 768 short edge with a 768 × 1344 area cap, each axis rounded to a multiple of 32. The template's 1344 × 768 is exactly that cap.

**Latents.** Video `[B, 24, T, H/16, W/16]` and audio `[B, 32, 2, T₄₀]` as a nested pair; audio runs on a 40 fps latent grid. Keyframe and reference condition latents are re-injected every step and never denoised.

### Length snaps to a 17k+5 grid

`align_frame_count` advances `n` until `n % 17 == 5`, and the widget steps by 17. Valid frame counts are therefore 5, 22, 39 … and at 24 fps:

| Frames | Duration | | Frames | Duration |
|---|---|---|---|---|
| 124 | 5.17 s | | 243 | 10.13 s |
| 141 | 5.88 s | | 260 | 10.83 s |
| 158 | 6.58 s | | 277 | 11.54 s |
| 175 | 7.29 s | | 294 | 12.25 s |
| 192 | 8.00 s | | 311 | 12.96 s |
| 209 | 8.71 s | | 328 | 13.67 s |
| 226 | 9.42 s | | 345 | 14.38 s |
|  |  | | 362 | 15.08 s |

**The trained range is roughly 124–362 frames** — about 5.2 to 15.1 seconds. The node accepts up to 3600, but the tooltip marks anything longer as untested, and below 124 is equally out of distribution.

Anything off the grid is snapped **up** silently. Multiples of 4 are not the rule: 144 becomes 158 and 168 becomes 175 without telling you.

### MiniMax H3 Sigma Shift

An extra node the stock template does not wire up: `MiniMaxH3SigmaShift`, under `model/patch/minimax`, with `shift_video` defaulting to **12.0** and `shift_audio` to **3.0**. The video shift drives the sampler's sigma schedule; the DiT inverts it to the shared base grid and derives the audio schedule from it. Worth an A/B at a fixed seed if motion feels over- or under-cooked — it moves where sampling spends its steps, which no scheduler swap can do.

### Socket types, and what they imply

```
ref_images.ref_image_0              IMAGE
ref_videos.ref_video_0              IMAGE   ← frames, not VIDEO
ref_video_audios.ref_video_audio_0  AUDIO   ← that video's soundtrack, supplied separately
ref_audios.ref_audio_0              AUDIO
```

**`ref_video_0` is typed `IMAGE`, not `VIDEO`.** Two consequences.

First, audio is not extracted automatically — that is why `ref_video_audio_0` exists as its own socket. Load the clip with `LoadVideo` → `GetVideoComponents` (splits `VIDEO` into `IMAGE`, `AUDIO`, fps) or with `VHS_LoadVideo`, then wire the frames and the audio separately. The stock R2V template ships only `LoadImage` nodes; you add the video loader yourself. Reference frames also cost VRAM directly, so trim the clip to the part that carries the motion rather than feeding it whole.

Second, and more important: reference video and reference stills enter the model **through the same channel**, as batches of images into Qwen3VL. There is no architectural separation between "this input carries identity" and "this input carries motion" — that split exists **only in the prompt text**. Unlike a pose ControlNet, where motion arrives on a separate spatial path and physically cannot carry appearance, here every reference competes on every axis.

So a reference video containing a person is a sustained identity signal — dozens of frames of a face — against a single still. The frames usually win, and the video's wardrobe and face bleed into the output. `Do not take the person or the wardrobe from <Video 1>` shifts the odds but does not settle it: it is a text instruction fighting a data signal, with no negative channel at CFG 1 to subtract it.

The reliable fix is structural, not verbal — remove the competing signal instead of forbidding it. If you want camera motion, shoot the reference orbiting an object with no person in frame. Otherwise crop the reference so the face never appears, and keep the clip short.
