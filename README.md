# MiniMax H3 — Claude Code Skill

A Claude Code skill for **MiniMax H3**, the open-weight omni-modal video model that generates video *and* native stereo audio in a single pass. Install it once and Claude stops guessing: it picks the right checkpoint, writes prompts in the structure the model was trained on, and knows why your camera move rendered a physical camera.

Built from the official ComfyUI templates and the published prompting guides, then hardened against the failure modes you actually hit.

---

## Why

H3 is unusually unforgiving about *how* a prompt is written. The same vocabulary arranged as a keyword cloud versus a timeline gives completely different results. It has two separate 66 GB checkpoints that look interchangeable and are not. It has no negative prompt, which is not documented anywhere obvious — half the prompts on the internet carry a `no extra fingers, no watermark` list that goes nowhere. And it renders `she holds the camera` as a woman holding a camera.

This skill encodes all of that so you don't rediscover it one failed render at a time.

## Install

```bash
git clone https://github.com/teskor-hub/minimax-h3-skill ~/.claude/skills/minimax-h3
```

Project-scoped instead of global:

```bash
git clone https://github.com/teskor-hub/minimax-h3-skill .claude/skills/minimax-h3
```

That's it. Claude loads it automatically when a conversation touches MiniMax H3, `fl2va`, `ref2va`, reference-to-video, or "turn this photo into a video".

## What it does

Ask in plain language:

> Write me an R2V prompt — this photo of a woman, the viewpoint rises above her head and she looks up into it

and you get a prompt in the five-block structure H3 expects, with the device deliberately absent (it's the viewpoint, so it should never be rendered), hands cropped at the frame edge (where extra fingers come from), and camera motion separated from body motion (joined, they resolve into a prop).

Ask which model to download and it answers from your actual VRAM, not from a generic table.

## What's inside

| File | Contents |
|---|---|
| `SKILL.md` | mode selection, the five-block framework, hard rules, limits |
| `references/prompting.md` | the framework in depth, worked examples, R2V role mapping, audio patterns |
| `references/templates.md` | copy-paste templates for R2V, I2V, FLF2V, T2V |
| `references/comfyui.md` | every checkpoint with sizes, quant explanations, VRAM tiers, node-by-node settings |
| `references/troubleshooting.md` | symptom → cause → fix |

## A taste of what's in there

**Two checkpoints, not two modes.** `fl2va` takes your frame and moves it — animation. `ref2va` takes your subject and shoots a new scene — casting. If the value is in the picture, use `fl2va`. If it's in who's in it, use `ref2va`. Forcing a back view out of a frontal close-up through I2V is the single most common way to melt a face.

**There is no negative prompt.** The official template uses `BasicGuider` — one conditioning input, CFG effectively 1, no negative socket. Bans have to be rewritten as positive statements of the desired state. Don't swap in `CFGGuider`: it doubles inference time and H3 never saw guidance in training.

**Steps are the most overrated knob.** `res_multistep` is a higher-order multistep sampler; 20 steps is equivalent to 35–40 on Euler. Going to 30 costs 50 % more time for nothing visible. The setting actually worth tuning on reference-heavy graphs is the *scheduler* — `beta` or `normal` against the default `simple`, at a fixed seed.

**Every reference needs a job.** `<Picture 1>` numbering follows socket connection order, not filenames. Attach files without telling the model what each controls and it averages them into a stranger.

**Unwritten audio isn't silence.** H3 generates stereo audio in the same pass whether or not you asked. Skip the audio block and you get the model's guess, which is usually generic music.

## Model reference

| Component | bf16 | int8_convrot | pruned int8 | nvfp4_awq |
|---|---|---|---|---|
| Diffusion (`fl2va` / `ref2va`) | 66.28 GB | 34.04 GB | 20.97 GB | — |
| Text encoder (Qwen3-VL-32B) | 51.51 GB | 27.14 GB | — | 15.69 GB |

Video VAE `fp16` 5.21 GB and audio VAE `fp32` 0.61 GB are required in every configuration. The text encoder and both VAEs are **shared across all four modes** — switching between I2V and R2V changes only the diffusion checkpoint.

Output: up to 2K (short edge 1440), 24 fps, 5–15 s. R2V accepts 9 images + 3 videos + 3 audio clips, 12 files maximum.

## Requirements

[Claude Code](https://claude.com/claude-code). The skill is documentation — no dependencies, no build step, nothing to run.

## Sources

Assembled from the [ComfyUI H3 tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3), the [official workflow templates](https://github.com/Comfy-Org/workflow_templates), the [Comfy-Org model repository](https://huggingface.co/Comfy-Org/MiniMax-H3), the [ComfyUI day-0 announcement](https://blog.comfy.org/p/minimax-h3-day-0-support-in-comfyui), and the prompting guides published by [fal.ai](https://fal.ai/learn/devs/minimax-h3-prompting-guide), [Morphic](https://morphic.com/resources/how-to/minimax-h3-guide) and [Topview](https://www.topview.ai/blog/minimax-h3-comfyui-day-0-guide).

## License

MIT — see [LICENSE](LICENSE).
