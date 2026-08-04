---
name: minimax-h3
description: Write, debug and structure prompts for MiniMax H3 video generation (T2V, I2V, FLF2V, R2V) and configure its ComfyUI workflow. Use when the user mentions MiniMax H3, minimax_h3, fl2va, ref2va, MiniMaxH3ReferenceToVideo, reference-to-video, or asks to animate a photo, write a video prompt, pick a model quant, or fix drifting identity, phantom objects, mangled hands and broken camera moves in H3 output.
---

# MiniMax H3 — prompting and ComfyUI setup

MiniMax H3 is an open-weight omni-modal video model: it generates video **and native stereo audio in a single forward pass**, up to 2K / 24fps / 15s. It ships as two separate checkpoints — `fl2va` (frame-conditioned) and `ref2va` (reference-conditioned) — which are different weights, not modes of one model.

Read `references/prompting.md` before writing any prompt. Read `references/comfyui.md` before recommending model files or node settings. Read `references/troubleshooting.md` when the user reports a specific artifact.

## 1. Pick the mode first

The single most common mistake is writing a good prompt for the wrong mode.

| User wants | Mode | Checkpoint | Input image is… |
|---|---|---|---|
| Video from text only | T2V | `fl2va` | — |
| **This exact photo** animated | I2V | `fl2va` | literally frame 0, pixel-exact |
| A→B move, seamless loop, clip chaining | FLF2V | `fl2va` | frame 0 **and** frame N |
| **This person/object** in a new shot | R2V | `ref2va` | semantic reference, redrawn |

Decision rule: if the value is in **the picture** (its room, light, grain, composition), use `fl2va`. If the value is in **who or what is in it**, use `ref2va`.

`fl2va` is animation — it takes the frame and moves it.
`ref2va` is casting — it takes the subject and shoots a new scene.

A shot that needs a viewpoint absent from the source photo (back view, wide, different room) is an R2V job. Forcing it through I2V means the model must hallucinate the missing body while rotating, which is where identity collapses.

## 2. The five-block prompt framework

H3 is trained on structured briefs, not prose. Always emit blocks in this order.

```
Roles    — what each reference locks   (R2V only)
Beats    — timestamped actions
Look     — camera, lighting, grain, texture
Sound    — audio as its own track, with timing
Locks    — what must stay identical / must never appear
```

Prompt field holds up to 7000 characters. Use them.

**Roles** (R2V): every attached file gets an explicit job. Never attach and hope.
```
<Picture 1> locks her face, freckles and tattoos.
<Picture 2> fixes hair length and silhouette from behind.
<Video 1> supplies the handheld camera rhythm only, not the subject.
```
Tags are numbered **in the order the inputs are connected to the node**. Reorder the sockets and the roles swap.

**Beats**: timestamped change, never a still frame.
```
[0.0-1.5s] eye level, she looks into the lens
[1.5-3.5s] the shot cranes up and tilts down into a high angle
[3.5-5.0s] she looks up into the lens, holds, one slow blink
```
Budget 1–3 beats per 5 seconds. Match beat count to duration instead of padding.

**Look**: production language, not adjectives. `handheld`, `micro-wobble`, `soft film grain`, `warm low-light`, `amateur phone-camera look`. The words `cinematic`, `beautiful`, `high quality`, `8k` carry no signal for this model.

**Sound**: H3 generates audio whether or not you asked. Unwritten audio is not silence — it is a guess. Name the room tone, the effects and their timing, and say `no music` when you mean it.

**Locks**: identity anchors and bans, stated up front rather than buried at the end.

## 3. Hard rules

**Never write `camera` as a noun the subject interacts with.** H3 reads `she holds the camera` as a prop to render. Keep the word inside the `Look`/`Camera:` directive line only, and describe the subject's arms separately — `she lifts both arms toward the viewer, hands passing just outside the top corners of the frame`. Same for `phone` when the device is the viewpoint: if it is the camera, it is off-frame by definition and must not be described at all.

**There is no negative prompt.** The ComfyUI template uses `BasicGuider`, i.e. CFG = 1, single conditioning input, no negative socket. Lists like `no extra fingers, no watermark` have nowhere to go. State the desired state positively instead: `her right hand grips firmly, five clearly separated fingers`. Do not swap in `CFGGuider` — H3 is tuned for CFG 1, and it doubles inference time.

**The model cannot count, and bans amplify what they ban.** There is no event counter — `exactly one shot` is a token sequence, not a constraint, and `no second shot` puts *second shot* into the conditioning where CFG 1 offers no negative channel to subtract it. Every mention of an event, prohibitions included, adds weight to it happening. Name the event once, in one beat, keep it out of `Locks`, and suppress repetition through scene state instead — muzzle lowered, smoke drifting, spent shell on the ground. A ban is a word; a lowered barrel is something the model can draw.

**Beat duration is read literally as event speed.** A fall given 1.5 s renders as a 1.5-second fall — weightless, moon gravity. Real falls take about half a second. Budget the beat to the real duration, spend the spare time on the aftermath, and remember that weight comes from the stop rather than the drop.

**One camera move per beat.** Stacked equal-weight moves (orbit + push-in + tilt at once) collapse into mush.

**Objects that do not exist in the reference rarely materialise.** If the subject must hold something, either supply it as a reference image with its own role, or restructure so the object is off-frame.

**Do not mix modes.** First/last frames and references are separate conditioning paths; asking R2V to treat `<Picture 2>` as an end frame does nothing — there is no terminal-frame mechanism in `ref2va`.

**Iterate one variable at a time.** Change the identity note, the motion note, the camera note, or a constraint — never the whole prompt — and hold the seed fixed while doing it.

## 4. Limits

| | |
|---|---|
| Output | up to 2K (short edge 1440), 24 fps, 5–15 s |
| Aspect ratios | 21:9, 16:9, 4:3, 1:1, 3:4, 9:16, auto |
| Prompt | 7000 characters |
| R2V references | 9 images + 3 videos + 3 audio, **12 files max** |
| Reference video/audio | 2–15 s each, 15 s combined |
| Audio reference | must accompany at least one image or video; standalone audio is rejected |

## 5. Camera vocabulary

Depth `push in` `pull out` · Horizontal `truck left/right` `pan left/right` · Vertical `rise` `lower` `tilt up/down` · Subject-led `tracking shot` `follow` `back-following steadicam` · Shaped `orbit` `half-orbit` `low-angle orbit` `crane up` `overhead` · Static `locked off` · Texture `handheld` `micro-wobble` `autofocus delay`

## References

- `references/prompting.md` — full framework, worked examples, R2V role-mapping, audio patterns
- `references/templates.md` — copy-paste templates for all four modes
- `references/comfyui.md` — checkpoints, quants, VRAM, node-by-node settings
- `references/troubleshooting.md` — symptom → cause → fix
