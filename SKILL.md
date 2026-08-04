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

**Structure beats instruction.** Anything you can make impossible by construction should be made impossible by construction rather than forbidden in words. A second shot is prevented by a lowered muzzle and drifting smoke, not by `no second shot`. A subject spinning instead of the camera is prevented by describing background parallax, not by `she does not turn`. A reference video bleeding its actor into your output is prevented by a merged `<Subject N>` definition, not by `do not take the person from <Video 1>`. Every ban is a text instruction competing against a data signal, and the data usually wins.

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

Frame count sets duration at 24 fps — use multiples of 4. 124 ≈ 5.2 s · 144 = 6 s · 168 = 7 s · 192 = 8 s.
