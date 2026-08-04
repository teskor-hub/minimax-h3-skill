---
name: minimax-h3
description: Write, debug and structure prompts for MiniMax H3 video generation (T2VA, I2VA, FL2VA, L2VA, full-reference R2V) and configure its ComfyUI workflow. Use when the user mentions MiniMax H3, minimax_h3, fl2va, ref2va, MiniMaxH3ReferenceToVideo, reference-to-video, or asks to animate a photo, write a video prompt, pick a model quant, or fix drifting identity, phantom objects, mangled hands, weightless falls and broken camera moves in H3 output.
---

# MiniMax H3 — prompting and ComfyUI setup

MiniMax H3 is an open-weight omni-modal video model: it generates video **and native stereo audio in a single forward pass**, up to 2K / 24fps / 15s. It ships as two checkpoints — `fl2va` (frame-conditioned) and `ref2va` (reference-conditioned) — which are different weights, not modes of one model.

This skill follows MiniMax's own prompt-writing guides and adds the failure modes those guides do not cover.

- `references/prompting.md` — the official output format for T2VA / I2VA / FL2VA / L2VA
- `references/reference-mode.md` — the official six-section format for full-reference (R2V)
- `references/templates.md` — fill-in templates for every mode
- `references/troubleshooting.md` — symptom → cause → fix, from real failures
- `references/comfyui.md` — checkpoints, quants, VRAM, node-by-node settings

## 0. Before writing a prompt

H3 prompts are long and expensive to iterate, and the wrong mode wastes the whole render. Ask rather than guess when any of these is unclear — one question up front is cheaper than a bad eight-second generation:

- **Which mode?** If the user has an image, establish whether it is a *frame* (I2VA/FL2VA/L2VA) or a *reference* (R2V). This is the single most consequential fork and users rarely state it. "Do you want the video to literally start from this photo, or just to feature this person?" settles it.
- **Which assets exist?** How many reference images, whether there is a reference video or audio, and what each is supposed to contribute. A reference with no assigned role is the top R2V failure.
- **Duration.** Frame count snaps to a grid and the timeline must match it; a prompt written for 10 s rendered at 124 frames is crushed into 5.
- **What must not change** — identity anchors, wardrobe, location, grain.
- **Whether a real camera move is required**, since that is the weakest axis and may need a reference video or a different mode.

State a recommendation rather than only listing options, and say plainly when a request will not work as asked — for example a back view demanded from a frontal close-up through I2VA. Flag the trade-off, propose the mode that does work, and proceed.

Two numbers in §6 come from community write-ups rather than MiniMax or the ComfyUI source: the 2K / 1440-short-edge output cap and the 7000-character prompt field. Treat them as approximate and do not present them as documented.

## 1. Pick the mode

| User wants | Official mode | Checkpoint |
|---|---|---|
| Video from text only | T2VA | `fl2va` |
| **This exact photo** animated forward | I2VA | `fl2va` |
| A path from frame A to frame B, or a seamless loop | FL2VA | `fl2va` |
| A shot that *lands on* a given final frame | L2VA | `fl2va` |
| **This person/object** in a new shot | full-reference (R2V) | `ref2va` |

`fl2va` = **f**irst/**l**ast frame → **v**ideo+**a**udio. `ref2va` = **ref**erence → video+audio.

Decision rule: if the value is in **the picture** — its room, light, grain, composition — use `fl2va`. If the value is in **who or what is in it**, use `ref2va`. `fl2va` is animation: it takes the frame and moves it. `ref2va` is casting: it takes the subject and shoots a new scene.

A shot needing a viewpoint that does not exist in the source photo (back view, wide, different room) is a full-reference job. Forcing it through I2VA makes the model hallucinate the missing body while rotating, which is where identity collapses.

**There is no video-to-video, and therefore no character swap.** Every H3 node in ComfyUI starts sampling from an empty latent; keyframe and reference latents are conditioning re-injected each step and never denoised. No frame of a reference video survives into the output. Asking to "replace the person in this clip" cannot be satisfied — the answer is a new generation that approximately follows the reference's motion, with everything else rebuilt. The `video editing` and `video continuation` task types in the reference guide belong to MiniMax's own pipeline; ComfyUI implements only `reference generation`. Say this plainly when a user asks for a swap rather than producing a prompt that quietly cannot work.

## 2. Output format

**T2VA / I2VA / FL2VA / L2VA** — an alignment instruction line (except T2VA), one blank line, then three fields:

```
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

**Full-reference** — six sections, in this order:

```
subject_definitions:   what each referenced item is and what it contributes
summary:               [task type] one paragraph
retention_analysis:    per-label fidelity markers
detailed_description:  shot-by-shot body, 350–500 words
overall_soundscape:    ambience and physical sound
non_diegetic_music:    audience-only score, or N/A
```

Shots: `[Shot 1]` carries **no timestamp**. Later shots open with a strictly increasing cut time — `[Shot 2] At 00:03.500, the camera cuts to …`. Open `[Shot 1]` with the style: `[Shot 1] Live-action, cinematic, a medium-wide shot frames …`

## 3. Reference labels

Four labels, and picking the wrong one is the most common structural mistake.

| Label | What it is for |
|---|---|
| `<Subject N>` | **reusable visible content** — a person, animal, object, environment, costume, prop, style, action or pose |
| `<Picture N>` | an image used as a **concrete frame** — first, key, last, or composition anchor |
| `<Video N>` | **whole-video relationships** — an edit source, a continuation point, or borrowed camera movement, cuts and rhythm |
| `<Audio N>` | an audio signal that is copied or referenced |

**Identity lives in `<Subject N>`, never in a standalone `<Picture N>`.** The guide is explicit: if an image only defines a character, scene, costume or style, do not give it its own picture entry — cite it inside the subject definition.

**One subject may draw on several assets, and that is how you resolve reference conflicts:**

```
<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking
motion comes from <Video 1>.
```

That single line is the official answer to "take the motion from the video and the face from the photo". You do not forbid the video from contributing a face — you define one subject and state what each source supplies. Anything reused as *visible content* from a video belongs to `<Subject N>`; `<Video N>` only names the asset or its structure.

## 4. Camera motion

Official vocabulary. Write it as a natural English action inside the shot, never as labels stacked at the end.

**Type** — `Zoom In / Zoom Out` (focal length, body still) · `Push In / Pull Out` (body moves) · `Pan Left / Right` (pivot horizontally) · `Truck Left / Right` (translate horizontally) · `Tilt Up / Down` (pivot vertically) · `Pedestal Up / Down` (whole camera rises or drops) · `Arc Shot` (arc around the subject) · `Tracking Shot` · `Static Shot` · `Shake Slightly / Strongly` · `POV` · `Roll Clockwise / Counterclockwise`

**Amplitude** — `with small amplitude`, `with large amplitude`. **Speed** — `at slow speed`, `at fast speed`. Medium amplitude and normal speed are simply omitted.

```
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
The camera arcs around her with large amplitude at slow speed as the lamp sweeps across frame.
```

Prefer camera motion over a cut when only distance or angle changes. A cut should introduce new information about subject, space, state, viewpoint or time.

## 5. Hard rules

These are empirical — none of them appear in MiniMax's guides.

**Structure beats instruction.** Anything you can make impossible by construction should be made impossible by construction rather than forbidden in words. A second shot is prevented by a lowered muzzle and drifting smoke, not by `no second shot`. A subject spinning instead of the camera is prevented by describing background parallax, not by `she does not turn`. A reference video bleeding its actor into your output is prevented by a merged `<Subject N>` definition and a `weak_reference` marker in `retention_analysis`, not by `do not take the person from <Video 1>` in the body.

This is not "never exclude anything" — it is about **where the exclusion lives**. A fidelity marker is an enum the format defines and the model was trained to read; the same words as a sentence in `detailed_description` are prose competing against a data signal, and the data usually wins.

**There is no negative prompt.** The ComfyUI template uses `BasicGuider` — one conditioning input, CFG effectively 1, no negative socket. State the desired condition positively instead. Do not swap in `CFGGuider`: it doubles inference time and H3 was not trained with guidance.

**The model cannot count, and bans amplify what they ban.** `exactly one shot` is a token sequence, not a constraint, and `no second shot` puts *second shot* into the conditioning with no negative channel to subtract it. Name an event once, in one shot, with no prohibition attached, then block repetition through scene state.

**Never write `camera` as a noun the subject interacts with.** H3 renders `she holds the camera` as a prop. Use the official camera vocabulary for the movement, describe the subject's arms separately, and keep the two in different sentences — joined by a verb of possession they resolve into an object. When the device *is* the viewpoint, use `POV` and never mention it at all; a visible outstretched arm is what sells the grip.

**Impossible poses produce body horror.** Camera directly behind + body not rotating + eye contact needs a 170° neck twist, and the model resolves it by inverting the head or blending front and back anatomy. Stop at three-quarter, let the shoulders rotate with the head, and lock anatomy explicitly.

**Shot and beat duration is read literally as event speed.** A fall given 1.5 s renders as a 1.5-second fall — weightless, moon gravity. Real falls take about half a second. Budget the real duration, spend the remaining time on the aftermath, and remember that weight comes from the stop rather than the drop.

**Big physical events need intermediate poses and room in the frame.** "She falls" is an outcome the model smooths away. Give the trajectory, and make sure the framing actually contains the ground.

**One camera move per shot.** Stacked equal-weight moves collapse into mush.

**Iterate one variable at a time**, at a fixed seed.

## 6. Limits

Output up to 2K (short edge 1440), 24 fps, 5–15 s. Prompt field 7000 characters. `detailed_description` runs 350–500 English words for generation tasks. Full-reference accepts 9 images + 3 videos + 3 audio clips, 12 files maximum; reference video and audio are 2–15 s each, 15 s combined; standalone audio is rejected and must accompany at least one image or video.

**Frame count snaps to a 17k+5 grid**, and anything off it is rounded up silently — multiples of 4 are *not* the rule. Valid values at 24 fps: 124 = 5.17 s · 141 = 5.88 s · 158 = 6.58 s · 175 = 7.29 s · 192 = 8.00 s · 209 = 8.71 s · 226 = 9.42 s · 243 = 10.13 s · 260 = 10.83 s · 277 = 11.54 s · 294 = 12.25 s · 311 = 12.96 s · 328 = 13.67 s · 345 = 14.38 s · 362 = 15.08 s. The trained range is roughly **124–362**; outside it the model is out of distribution.

## 7. What ComfyUI does with your prompt

**There is no rewriter.** MiniMax's guides describe the output of their own rewriting model, but ComfyUI tokenizes your text verbatim — not chat-templated, no special tokens. Writing in the documented format yourself is therefore the only way to land in the training distribution.

**The alignment instruction is not emitted for you.** ComfyUI prepends only `"<Picture 1>: "` and the image. The `For the target video, at 0.00 seconds…` and `How the reference pictures align…` lines from the guide are *your* text — type them as the first line of the prompt box, followed by a blank line.

**ComfyUI injects the reference labels itself**, before your prompt, in a **fixed category order**: all images, then videos — each video's soundtrack label placed immediately *before* its own `<Video k>` — then standalone audio. Ordinals are 1-based per type and follow slot number, not the order you happened to wire things. Two consequences: a video's soundtrack takes `<Audio 1>` ahead of any standalone audio, and moving an image from `ref_image_2` to `ref_image_0` renumbers it without touching your prompt. When you write `<Picture 1>` you are pointing at a label that already exists in the context.

Slot maxima on the node: **9 images, 3 videos, 3 video soundtracks, 3 standalone audio.** The sockets auto-grow, so a fresh node showing three image inputs is not the limit.

**Reference audio never reaches the text encoder** — only its label does; the waveform goes to the DiT separately. **Reference video reaches the encoder at 2 fps**, so a 5-second clip arrives as roughly ten frames.

See `references/comfyui.md` for the exact `ref_image_size` formulas, the native canvas, and the undocumented `MiniMaxH3SigmaShift` node.
