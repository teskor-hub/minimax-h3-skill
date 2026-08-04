---
name: minimax-h3
description: Write, debug and structure prompts for MiniMax H3 video generation (T2VA, I2VA, FL2VA, L2VA, Ref2VA) and configure its ComfyUI workflow. Use when the user mentions MiniMax H3, minimax_h3, fl2va, ref2va, MiniMaxH3ReferenceToVideo, reference-to-video, or asks to animate a photo, write a video prompt, pick a model quant, or fix drifting identity, phantom objects, mangled hands, weightless falls and broken camera moves in H3 output.
---

# MiniMax H3 — prompting and ComfyUI setup

MiniMax H3 is an open-weight omni-modal video model: it generates video **and native stereo audio in a single forward pass**, at 24 fps, with a trained clip length of roughly 5–15 s. It ships as two checkpoints — `fl2va` (frame-conditioned) and `ref2va` (reference-conditioned) — which are different weights, not modes of one model.

This skill follows MiniMax's own prompt-writing guides and adds the failure modes those guides do not cover.

- `references/prompting.md` — the official output format for T2VA / I2VA / FL2VA / L2VA
- `references/reference-mode.md` — the official six-section format for full reference (Ref2VA)
- `references/templates.md` — fill-in templates for every mode
- `references/troubleshooting.md` — symptom → cause → fix, from real failures
- `references/comfyui.md` — checkpoints, quants, VRAM, node-by-node settings

## 0. Before writing a prompt

H3 prompts are long and expensive to iterate, and the wrong mode wastes the whole render. Ask rather than guess when any of these is unclear — one question up front is cheaper than a bad eight-second generation:

- **Which mode?** If the user has an image, establish whether it is a *frame* (I2VA/FL2VA/L2VA) or a *reference* (Ref2VA). This is the single most consequential fork and users rarely state it. "Do you want the video to literally start from this photo, or just to feature this person?" settles it.
- **Which assets exist?** How many reference images, whether there is a reference video or audio, and what each is supposed to contribute. A reference with no assigned role is the top Ref2VA failure.
- **Duration.** Frame count snaps to a grid and the timeline must match it; a prompt written for 10 s rendered at 124 frames is crushed into 5.
- **What must not change** — identity anchors, wardrobe, location, grain.
- **Whether a real camera move is required**, since that is the weakest axis and may need a reference video or a different mode.

State a recommendation rather than only listing options, and say plainly when a request will not work as asked — for example a back view demanded from a frontal close-up through I2VA. Flag the trade-off, propose the mode that does work, and proceed.

**Always state a recommended `length` when the user has not given one.** Put it after the prompt block, as frames and seconds — `length 192 (8.00 s)`. Derive it rather than guessing: budget each beat its *real-world* duration, add a second of settle at the end, then round **up** to the nearest `17k+5` value. Duration is read literally as event speed, so an over-long clip does not give the model room — it gives you slow motion. The table in `references/prompting.md` lists realistic durations for common events; the short version is 124 for a single action on a static camera, 158 with one camera move, 192 for an entrance or approach, 209 for action → reaction → settle, and 243+ once there are cuts. For dialogue, count words at roughly 2.7 per second. Mention the cost when it matters: frames drive VRAM and render time directly, and past 362 the model is out of distribution.

**Always emit the complete prompt, in one code block, ready to paste as-is** — including on follow-ups that change a single word. Never reply with only the edited section, never "replace the beats block with this", never `[rest unchanged]` or `...` standing in for text already written. The user copies and pastes; a fragment forces a manual merge and invites typos. Put nothing inside the block but the prompt itself: the alignment instruction line where the mode requires one, then every section in order, complete. Explanation of what changed goes after the block, in prose, as brief as the change deserves. Length is never a reason to abbreviate.

**Terminology.** Use MiniMax's names — **T2VA, I2VA, FL2VA, L2VA, Ref2VA** — when talking about modes, and the weight-family names `fl2va` / `ref2va` only when talking about checkpoint files. The aliases T2V / I2V / FLF2V / R2V are common in the wild; recognise them, but do not emit them.

**Provenance.** `SOURCES.md` tags every claim in this skill as Official, Implementation, Empirical or Community. When a user leans on a number, check which it is — several widely repeated figures (2K output cap, 7000-character prompt field, 12-file reference limit) are community reports with no primary source, and the empirical rules are tendencies rather than guarantees. Say which kind you are relying on when it matters to the decision.

## 1. Pick the mode

| User wants | Official mode | Checkpoint |
|---|---|---|
| Video from text only | T2VA | `fl2va` |
| **This exact photo** animated forward | I2VA | `fl2va` |
| A path from frame A to frame B, or a seamless loop | FL2VA | `fl2va` |
| A shot that *lands on* a given final frame | L2VA | `fl2va` |
| **This person/object** in a new shot | Ref2VA | `ref2va` |

`fl2va` = **f**irst/**l**ast frame → **v**ideo+**a**udio. `ref2va` = **ref**erence → video+audio.

Decision rule: if the value is in **the picture** — its room, light, grain, composition — use `fl2va`. If the value is in **who or what is in it**, use `ref2va`. `fl2va` is animation: it takes the frame and moves it. `ref2va` is casting: it takes the subject and shoots a new scene.

A shot needing a viewpoint that does not exist in the source photo (back view, wide, different room) is a full-reference job. Forcing it through I2VA makes the model hallucinate the missing body while rotating, which is where identity collapses.

**There is no video-to-video, and therefore no frame-preserving character swap.** Every H3 node in ComfyUI starts sampling from an empty latent; keyframe and reference latents are conditioning re-injected each step and never denoised. No frame of a reference video survives into the output. The `video editing` and `video continuation` task types are not thereby proven inert locally — the plumbing is identical for every task type and only the `summary` prefix differs — but no source frame is preserved whichever prefix you write. Whether the model responds differently to them under local inference is untested.

**But do not over-correct — the useful version of that request is the tool's main purpose.** "A new video in which the person resembles my reference photo and moves the way this clip does" is exactly `reference generation`, and it works. Expect recognisable likeness rather than face-swap identity: H3 is a generative video model, not an identity adapter. Distinguish the two explicitly when a user says "swap", because they usually mean the second one and will be wrongly discouraged by a flat no.

Likeness improves, in order of payoff: two to four reference photos of the same person from different angles, all merged into one `<Subject N>`; identity in `<Subject N>` rather than a standalone `<Picture N>`; `ref_image_size: max` on the final render; short camera travel, so less unseen geometry has to be invented; a higher-precision text encoder if VRAM allows, since identity flows through it in reference mode.

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
detailed_description:  shot-by-shot body, normally 350–500 words
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

This is not "never exclude anything" — it is about **where the exclusion lives**. A fidelity marker is a fixed value in MiniMax's documented format, which is a stronger convention than an ad-hoc sentence; but ComfyUI parses nothing, so it arrives as ordinary prompt tokens either way. That scoping there beats the same words in the body is **empirical**, not mechanical. What is solid is the general observation: a ban is text competing against a data signal, and the data usually wins.

**There is no negative prompt.** The ComfyUI template uses `BasicGuider` — one conditioning input, CFG effectively 1, no negative socket. State the desired condition positively instead. Do not reach for `CFGGuider` casually: it doubles inference time, and how H3 was trained with respect to guidance is not established by any source here.

**The model cannot count, and bans amplify what they ban.** `exactly one shot` is a token sequence, not a constraint, and `no second shot` puts *second shot* into the conditioning with no negative channel to subtract it. Name an event once, in one shot, with no prohibition attached, then block repetition through scene state.

**Never write `camera` as a noun the subject interacts with.** H3 renders `she holds the camera` as a prop. Use the official camera vocabulary for the movement, describe the subject's arms separately, and keep the two in different sentences — joined by a verb of possession they resolve into an object. When the device *is* the viewpoint, use `POV` and never mention it at all; a visible outstretched arm is what sells the grip.

**Impossible poses produce body horror.** Camera directly behind + body not rotating + eye contact needs a 170° neck twist, and the model resolves it by inverting the head or blending front and back anatomy. Stop at three-quarter, let the shoulders rotate with the head, and lock anatomy explicitly.

**Shot and beat duration is read literally as event speed.** A fall given 1.5 s renders as a 1.5-second fall — weightless, moon gravity. Real falls take about half a second. Budget the real duration, spend the remaining time on the aftermath, and remember that weight comes from the stop rather than the drop.

**Big physical events need intermediate poses and room in the frame.** "She falls" is an outcome the model smooths away. Give the trajectory, and make sure the framing actually contains the ground.

**One primary camera move per shot.** A secondary tilt or pan that keeps the subject framed during that move is fine — a pedestal up with a compensating tilt down is one operation, not two. What collapses into mush is several independent, equal-weight moves competing in the same shot.

**Iterate one variable at a time**, at a fixed seed.

## 6. Limits

Verified: 24 fps, the `17k+5` frame grid, a trained range of roughly 124–362 frames. Community-reported and **not** found in the primary sources: output up to 2K with a 1440 short edge, and a 7000-character prompt field — do not present either as documented. `detailed_description` runs 350–500 English words for generation tasks, with documented exceptions: dialogue-dense content departs from the range to fit the spoken timeline, and editing descriptions scale with the source. Full-reference slots in ComfyUI: 9 reference images, 3 reference videos, 3 same-index video soundtracks, 3 standalone audio clips. **Standalone audio is accepted on its own** — the node processes it unconditionally, despite community write-ups claiming otherwise. The reference-video tooltip recommends 2–15 s, but the code enforces only a 5-frame minimum, and a clip longer than the *aligned* target frame count is truncated to that, then trimmed *down* until its own frame count also satisfies `17k+5`. No 12-file total or combined-duration cap exists in the source.

**Frame count snaps to a 17k+5 grid**, and anything off it is rounded up silently — multiples of 4 are *not* the rule. Valid values at 24 fps: 124 = 5.17 s · 141 = 5.88 s · 158 = 6.58 s · 175 = 7.29 s · 192 = 8.00 s · 209 = 8.71 s · 226 = 9.42 s · 243 = 10.13 s · 260 = 10.83 s · 277 = 11.54 s · 294 = 12.25 s · 311 = 12.96 s · 328 = 13.67 s · 345 = 14.38 s · 362 = 15.08 s. The trained range is roughly **124–362**; outside it the model is out of distribution.

## 7. What ComfyUI does with your prompt

**There is no rewriter.** MiniMax's guides describe the output of their own rewriting model, but ComfyUI tokenizes your text verbatim — not chat-templated, no special tokens. So the documented structure has to be written by hand if you want it at all. Whether reproducing it outperforms an equivalent plain-prose prompt has not been measured here; this skill uses it as the documented default, not as a proven win.

**The alignment instruction is not emitted for you.** ComfyUI prepends only `"<Picture 1>: "` and the image. The `For the target video, at 0.00 seconds…` and `How the reference pictures align…` lines from the guide are *your* text — type them as the first line of the prompt box, followed by a blank line.

**ComfyUI injects the reference labels itself**, before your prompt, in a **fixed category order**: all images, then videos — each video's soundtrack label placed immediately *before* its own `<Video k>` — then standalone audio. Ordinals are 1-based per type and follow slot number, not the order you happened to wire things. Two consequences: a video's soundtrack takes `<Audio 1>` ahead of any standalone audio, and moving an image from `ref_image_2` to `ref_image_0` renumbers it without touching your prompt. When you write `<Picture 1>` you are pointing at a label that already exists in the context.

Slot maxima on the node: **9 images, 3 videos, 3 video soundtracks, 3 standalone audio.** The sockets auto-grow, so a fresh node showing three image inputs is not the limit.

**Reference audio never reaches the text encoder** — only its label does; the waveform goes to the DiT separately. **Reference video reaches the encoder at 2 fps**, so a 5-second clip arrives as roughly ten frames.

See `references/comfyui.md` for the exact `ref_image_size` formulas, the native canvas, and the undocumented `MiniMaxH3SigmaShift` node.
