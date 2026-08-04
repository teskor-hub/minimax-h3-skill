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

**`ref_image_size`: `match` → `max`.** `match` scales references to generation resolution and is faster; `max` keeps up to 2048 px on the short edge and holds identity noticeably better. If you care about likeness, this buys more than any sampler change.

**`length`.** 124 frames at 24 fps = 5.2 s. Match this to the beat count in the prompt — a prompt with a 15-second timeline rendered at 124 frames gets compressed into a frantic 5 seconds. Long or complex camera moves want 180–240 frames; short moves stay crisper at 124.

**Seed → `fixed`** the moment output is close. Debugging a prompt against moving noise is guesswork.

**Resolution last.** It hits VRAM harder than anything else.

**Sage Attention**, if installed, roughly doubles generation speed with minimal quality loss. Blackwell needs SageAttention 2++ or 3.

## R2V input wiring

`MiniMaxH3ReferenceToVideo` accepts up to 9 images, 3 videos and 3 audio clips, **12 files total**. Reference video and audio are 2–15 s each, 15 s combined. Standalone audio is rejected — it must accompany at least one image or video.

Prompt tags `<Picture 1>`, `<Video 1>`, `<Audio 1>` are numbered by **socket connection order**. Rewiring the inputs reassigns the roles without touching the prompt, which is a subtle and very annoying source of "the prompt suddenly stopped working".

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
