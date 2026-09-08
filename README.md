# MiniMax H3 — Claude Code Skill

A Claude Code skill for **MiniMax H3**, the open-weight omni-modal video model that generates video *and* native stereo audio in a single pass. Install it once and Claude stops guessing: it picks the right checkpoint, writes prompts in MiniMax's documented rewrite-output structure, and knows why your camera move rendered a physical camera.

Not using Claude Code? The same thing ships as [`portable-prompt.md`](portable-prompt.md) — one block of text you paste into ChatGPT, Grok or anything else. Building a whole reel rather than a single shot? [`reels-portable-prompt.md`](reels-portable-prompt.md) is the same knowledge wrapped in a clip-by-clip pipeline.

Built on MiniMax's own prompt-writing guides, plus the failure modes those guides don't cover.

---

## Why

H3 has a documented output format — six labelled sections in reference mode, a fixed alignment instruction in keyframe modes, a defined camera vocabulary with amplitude and speed — and almost nobody writes prompts that way. Plain prose omits relationships the structure makes explicit; how large the resulting quality difference is has not been measured here.

Then there is everything the documentation doesn't mention. Two 66 GB checkpoints that look interchangeable and are not. A stock BasicGuider path with no negative input, so copied prompts often carry a `no extra fingers, no watermark` list that goes nowhere. A model that renders `she holds the camera` as a woman holding a camera, spins the subject when you ask the camera to move, and renders a fall in moon gravity if you give the beat too many seconds.

This skill encodes both halves so you don't rediscover either one render at a time.

## Ways to use it

The same knowledge ships in the following forms, kept in sync. Pick whichever matches your setup.

### 1. As a Claude Code skill

`SKILL.md` and `references/` are a proper skill. Claude loads the core automatically and pulls in the detailed references only when it actually needs them.

```bash
git clone https://github.com/teskor-hub/minimax-h3-skill ~/.claude/skills/minimax-h3
```

Project-scoped instead of global:

```bash
git clone https://github.com/teskor-hub/minimax-h3-skill .claude/skills/minimax-h3
```

That's it — no configuration. It triggers on `MiniMax H3`, `fl2va`, `ref2va`, reference-to-video, "turn this photo into a video", or a complaint about drifting identity and mangled hands.

### 2. As a chat prompt — ChatGPT, Grok, Gemini, anything

**[`portable-prompt.md`](portable-prompt.md) is not a skill — it is a prompt.** A single self-contained instruction you paste into an ordinary chat: as a system prompt, as a custom instruction, or simply as the first message of a conversation. No Claude Code, no install, no file loading, no tooling. Plain text, any model.

Open it, copy everything below the horizontal rule, paste, then describe the shot you want in plain language.

It folds the framework, the rules, all four mode templates and the symptom→fix table into one document, because a chat model has no way to lazily load `references/` the way Claude Code does. Full installation and quant/VRAM tables are left out. Minimal ControlNet/Motion Strip input roles and alignment rules are included so the prompt can choose the right workflow.

### 3. As a reel pipeline — [`reels-portable-prompt.md`](reels-portable-prompt.md)

Also a pasteable prompt, but pitched a level up. A source reel that fits the selected H3 length budget can stay one render; longer reels use several clips joined in an editor — this one takes an idea or a reference reel and returns the entire build: shot breakdown, an exact `17k+5` length per clip, the list of reference photos you still have to shoot, one complete prompt per clip, and an edit sheet covering joins, on-screen text and music. Say *"I want a reel about X"* or *"rebuild this reel"* and it answers in those five blocks every time.

Pair it with [`tools/reel_shots.py`](tools/reel_shots.py) when rebuilding an existing reel: run the tool, paste the `manifest.json`, and the beat timings come from measurement instead of memory.

## Choose your Reel Maker workflow

When rebuilding a source reel, choose **ControlNet** or **Motion Strip**. If you do not
specify one, the skill asks before preparing mode-specific inputs. It remembers the choice
for that reel's follow-ups; these are two workflows using Ref2VA, not new model checkpoints.

| Workflow | What you supply | What it needs |
|---|---|---|
| **ControlNet** | Source video + face reference + body reference | H3-compatible ControlNet and pose/depth preprocessors; aligned maps drive the model separately from the two images |
| **Motion Strip** | Source video + face reference + target look/composition frame | A chronological image strip built from the source; no ControlNet download or pose/depth estimation |

Examples:

> Rebuild this reel in ControlNet mode. Picture 1 is my face reference, Picture 2 is my body reference.

> Rebuild this reel in Motion Strip mode with an identity photo, target look frame and motion strip.

> Переделай этот рилс: режим ControlNet, только фейс и боди реф.

**Each video needs its own description** — a text file or a message explaining the
scene, intended meaning and important details. The skill reads an existing description
first and asks only when it is missing, identifying the relevant filename/reel. It does
not silently ignore the description or invent its meaning; an explicit request to proceed
without one is honoured and noted.

**Both workflows inspect the source's descriptions, frames and soundtrack.** If dialogue
is present, its actual words, speaker roles and timing are transcribed and included in the
prompt automatically, including offscreen voices. Music lyrics are not mistaken for
conversation; uncertain words are flagged. Wardrobe, setting, props and facial acting
are described in both modes. A mode choice alone does not install models or launch a render.

See [the mode guide](references/reel-modes.md) for slot maps, ControlNet compatibility,
frame alignment, strength tuning and separate readiness checks. The same choice is included
in both portable prompts. This repository documents the workflows; it does not bundle the
ControlNet weights or a ready-to-import ComfyUI graph.

## What it does

Ask in plain language:

> Write me a Ref2VA prompt — this photo of a woman, the viewpoint rises above her head and she looks up into it

and you get a prompt in MiniMax's documented six-section full-reference structure, with the device deliberately absent (it's the viewpoint, so it should never be rendered), hands cropped at the frame edge (where extra fingers come from), and camera motion separated from body motion (joined, they resolve into a prop).

Ask which model to download and it answers from your actual VRAM, not from a generic table.

## What's inside

| File | Used by | Contents |
|---|---|---|
| `SKILL.md` | Claude Code | mode selection, output formats, reference labels, camera vocabulary, hard rules |
| `references/prompting.md` | Claude Code | the official T2VA / I2VA / FL2VA / L2VA format in depth |
| `references/reference-mode.md` | Claude Code | the official six-section full-reference (Ref2VA) format |
| `references/templates.md` | Claude Code | fill-in templates for every mode, with a worked example |
| `references/comfyui.md` | Claude Code | every checkpoint with sizes, quant explanations, VRAM tiers, node-by-node settings |
| `references/troubleshooting.md` | Claude Code | symptom → cause → fix |
| `references/reel-modes.md` | Claude Code | ControlNet / Motion Strip choice, source dialogue, input roles and readiness |
| **`portable-prompt.md`** | **any chat model** | **all of the above except ComfyUI, in one pasteable block** |
| **`reels-portable-prompt.md`** | **any chat model** | **the reel pipeline: breakdown → per-clip lengths → reference shopping list → per-clip prompts → edit sheet** |

## A taste of what's in there

**Identity belongs in `<Subject N>`, not `<Picture N>`.** This is the fix for "why does the face keep changing". `<Picture N>` is only for concrete frame anchors — the guide explicitly says not to create a standalone picture entry for a character. And the motion-from-video plus appearance-from-photo case everyone fights with is a documented one-liner: `<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.` One subject, two sources, each with a stated role — instead of two competing references and a "don't take the person from Video 1" that never works.

**Two checkpoints, not two modes.** `fl2va` takes your frame and moves it — animation. `ref2va` takes your subject and shoots a new scene — casting. If the value is in the picture, use `fl2va`. If it's in who's in it, use `ref2va`. Forcing a back view out of a frontal close-up through I2VA is the single most common way to melt a face.

**The stock BasicGuider path has no negative prompt.** It has one conditioning input and effectively CFG 1, so describe the desired state positively. Custom ControlNet workflows may use another guider with negative conditioning; the skill checks the actual graph rather than silently replacing it.

**Steps are probably the most overrated knob.** The stock workflow uses `res_multistep` at 20 steps. The often-quoted equivalence to 35–40 Euler steps is a rule of thumb, not a measurement on this model, and whether 30 steps buy anything visible is untested here. On reference-heavy graphs the *scheduler* is the more promising A/B — `beta` or `normal` against `simple`, at a fixed seed.

**Structure beats instruction.** Anything you can make impossible by construction should be, rather than forbidden in words. A second shot is prevented by a lowered muzzle and drifting smoke, not by `no second shot`. A subject spinning instead of the camera is prevented by describing background parallax, not by `she does not turn`. Every ban is a text instruction competing against a data signal, and the data usually wins.

**Duration is read literally as event speed.** Give a fall 1.5 seconds and you get a 1.5-second fall — weightless, moon gravity. Real falls take about half a second; budget that and spend the rest on the aftermath. Weight comes from the stop, not the drop.

**Unwritten audio isn't silence.** H3 generates stereo audio in the same pass whether or not you asked. Skip the sound fields and you get the model's guess, which is usually generic music.

## Model reference

| Component | bf16 | int8_convrot | pruned int8 | nvfp4_awq |
|---|---|---|---|---|
| Diffusion (`fl2va` / `ref2va`) | 66.28 GB | 34.04 GB | 20.97 GB | — |
| Text encoder (Qwen3-VL-32B) | 51.51 GB | 27.14 GB | — | 15.69 GB |

Video VAE `fp16` 5.21 GB and audio VAE `fp32` 0.61 GB are required in every configuration. The text encoder and both VAEs are **shared across all four modes** — switching between I2VA and Ref2VA changes only the diffusion checkpoint.

Verified in the ComfyUI source: 24 fps, a `17k+5` frame grid with a trained range of roughly 124–362 frames, and reference slots for 9 images, 3 videos, 3 video soundtracks and 3 standalone audio clips. A 2K / 1440-short-edge output mode and a 7000-character prompt field are community-reported and not verified against a primary source — see [SOURCES.md](SOURCES.md).

## Requirements

For the skill: [Claude Code](https://claude.com/claude-code). For `portable-prompt.md` and `reels-portable-prompt.md`: a chat window. The skill and portable prompts are documentation, with no build step. Executing a ControlNet workflow additionally needs compatible H3 ControlNet weights, nodes and the chosen preprocessors; Motion Strip does not.

## Sources

The format rules come from MiniMax's own guides — [base (T2VA / I2VA / FL2VA / L2VA)](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md) and [full-reference](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md).

Setup and model details from the [ComfyUI H3 tutorial](https://docs.comfy.org/tutorials/video/minimax/minimax-h3), the [official workflow templates](https://github.com/Comfy-Org/workflow_templates), the [Comfy-Org model repository](https://huggingface.co/Comfy-Org/MiniMax-H3) and the [day-0 announcement](https://blog.comfy.org/p/minimax-h3-day-0-support-in-comfyui). Additional context from the guides published by [fal.ai](https://fal.ai/learn/devs/minimax-h3-prompting-guide), [Morphic](https://morphic.com/resources/how-to/minimax-h3-guide) and [Topview](https://www.topview.ai/blog/minimax-h3-comfyui-day-0-guide).

The troubleshooting file is not from any of them — it's what actually broke.

## License

MIT — see [LICENSE](LICENSE).
