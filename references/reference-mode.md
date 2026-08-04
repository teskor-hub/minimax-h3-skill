# Full-reference mode (R2V) — the official six-section format

Source: MiniMax's `VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`. Runs on the `ref2va` checkpoint.

Shots, camera motion, speakers, dialogue and ordinary sound follow `prompting.md`. This file covers what is specific to reference mode: the labels, the analysis sections, and the format differences.

## Structure

| Section | Purpose |
|---|---|
| `subject_definitions` | defines referenced content and its labels |
| `summary` | task type, target video, main reference relationships |
| `retention_analysis` | how each reference is preserved, transferred or reused |
| `detailed_description` | visuals, actions, shots, sound, dialogue in playback order |
| `overall_soundscape` | ambience and physical sound |
| `non_diegetic_music` | audience-only score |

Once a label is assigned it keeps the same meaning across every section.

## 1. subject_definitions

### `<Subject N>` — reusable visible content

People, animals, objects · scenes, backgrounds, environments · clothing, props, interfaces, effects · styles, actions, expressions, poses.

It is a **content unit that will appear in the target video**, not the source file. One subject may be defined by several assets, and one asset may supply several subjects.

```
<Subject 1> is the young woman in <Picture 1>, with long dark hair, a blue cardigan, and a thin silver necklace.
```

**Merging sources — this is how reference conflicts are resolved:**

```
<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.
```

One subject, two assets, each with a stated contribution. There is no prohibition anywhere: you never write "do not take the person from `<Video 1>`", because the video was never given the identity role in the first place.

### `<Picture N>` — concrete frame anchors only

Use a standalone picture entry only when the image is a shot's first frame, keyframe, last frame, edited keyframe, or composition anchor.

```
<Picture 2> is the first frame of [Shot 1], showing a woman seated beside a café window.
<Picture 3> is a storyboard reference for [Shot 1] and [Shot 2], defining their viewpoint, subject placement, and shot order.
```

**If an image only defines a character, scene, costume or style, do not create a standalone picture entry** — cite the image inside the corresponding `<Subject N>` instead. This is the single most common structural error: using `<Picture 1>` to carry a face.

### `<Video N>` — whole-video relationships only

Editing a source video · continuing from its end · referencing its camera movement, cuts, rhythm or temporal structure.

```
<Video 1> is the source video for the target video edit.
```

**If a person, object, scene, action or effect from a reference video is reused as visible content, it belongs to `<Subject N>`.** `<Video N>` names the asset or its structure and never replaces subject labels.

### `<Audio N>` — audio signal

A standalone audio asset, or the enabled synchronized track of a reference video. Copying audio · referencing a music style · referencing a speaker's timbre and delivery · reusing dialogue, lyrics or effects · referencing beat, rhythm or continuity.

When an audio maps to a target speaker, reuse that speaker's global ID:

```
<Audio 1> is the voice-timbre reference for <Subject 1> (S1).
```

The ID comes from the target video's speaker order and is never independently assigned here.

`<Video N>` and `<Audio N>` are numbered **independently** — the same file can be `<Video 1>` and `<Audio 2>`, and different indices do not prevent a shared source. A reference video does not create an `<Audio N>` merely because the file contains sound.

> **How these actually arrive.** ComfyUI emits the labels into the token stream itself, before your prompt, in socket order — so your tags point at labels that already exist in context. Reference images go in whole; **reference video is downsampled to 2 fps** and split into 2-frame blocks with `<T.T seconds>` timestamps, so a 5-second clip reaches the encoder as about ten frames; and **reference audio never reaches the encoder at all** — only the bare `<Audio j>: ` label does, with the waveform routed to the DiT separately. An audio reference therefore cannot carry semantic structure through the prompt path, however you describe it. See `comfyui.md`.

## 2. summary

One short English paragraph, opening with a bracketed task type.

| Task type | When |
|---|---|
| `keyframe completion` | an image is a concrete frame anchor |
| `reference generation` | an asset guides a character, scene, style, action, camera movement or storyboard without being a concrete frame or an edited source |
| `video editing` | an existing source video is directly modified |
| `video continuation` | new content continues or extends an existing video |
| `audio reuse` | the same audio signal is reused in whole or part |
| `audio reference` | only style, timbre, content, texture, beat or continuity is referenced |

Combine with ` + ` and never repeat a type: `[video continuation + keyframe completion]`, `[video editing + audio reuse]`.

**Presence of a video does not create a video task type.** A reference video supplying only camera movement, cuts or rhythm is `reference generation`. Use `video editing` or `video continuation` only when that video is actually edited or continued.

Use the already-defined labels; introduce no new ones here. Video-editing summaries begin `The target video is an edited version of <Video 1>.`

## 3. retention_analysis

One line per label, fidelity stated with a fixed marker.

**Visible content** — `<Subject N>`, `<Picture N>`, `<Video N>`:

| Marker | Meaning |
|---|---|
| `fully_preserved` | the defined role is fully preserved |
| `partially_preserved` | still used, but some defined characteristics change or are only partly retained |
| `attribute_transfer` | characteristics are transferred to a different identifiable target subject |
| `weak_reference` | only broad similarity in style, category, composition or atmosphere |

```
<Subject 1> (appears in [Shot 1], [Shot 3]): fully_preserved - ...
<Picture 2> ([Shot 1] first frame): fully_preserved - ...
<Video 1> (cut and pacing structure): weak_reference - ...
```

**Audio** — `<Audio N>`:

| Marker | Meaning |
|---|---|
| `fully_copy` | the complete source audio is the target's complete final track |
| `partially_copy` | only part of the timeline or selected layers are copied, or sounds are added, removed or replaced afterwards |
| `reference` | not copied; only timbre, rhythm, style, dialogue content or texture is referenced |
| `weak_reference` | only broad category or atmosphere similarity |

Choose a marker **only within the role already defined for that label**. Newly added actions, backgrounds or plot events in the target video are not losses of reference fidelity.

This section is where role scoping actually lives. `<Video 1> (camera movement and pacing): weak_reference - only the travelling path and handheld rhythm are followed; none of its people, wardrobe, location or lighting appear.` does the work that a `do not take…` sentence in the body never does.

## 4. detailed_description

Shot by shot in playback order, same base format as `prompting.md`. Differences from T2VA:

| Dimension | T2VA | Full-reference |
|---|---|---|
| Main field | `integrated_multimodal_description` | `detailed_description` |
| Style opening | after `[Shot 1]` | one or two sentences **before** `[Shot 1]` |
| Reference info | no labels | insert labels at first appearance and wherever their roles apply |
| Audio | describes its own sound | cites `<Audio N>` and states copy or reference |

```
The target video is in a cinematic, literary music-video style with soft lighting and a slightly desaturated color palette.
[Shot 1] The scene opens in a crowded urban street...
[Shot 2] At 00:09.000, the shot cuts to an extreme close-up...
```

At an important subject's first clear appearance, describe its referenced characteristics, frame position and current action — within what is actually visible in that shot. Later shots reuse the label without redefining it.

Frame anchors read naturally: `the shot begins from <Picture 1>` · `the shot's keyframe corresponds to <Picture 2>` · `the shot ends on <Picture 3>`.

**350–500 English words** for generation tasks. Dialogue-dense content prioritises fitting the spoken timeline over hitting a word count. Editing descriptions scale with the source. A single shot does not justify a shorter description — distribute detail by information load.

Make it genuinely detailed: composition, subject appearance and position, environment and lighting, actions and state changes, camera movement, current sound, and where referenced content actually takes effect. **Do not reduce it to a plot summary or a list of reference relationships.**

### Speakers with references

When a referenced subject speaks, keep both labels:

```
<Subject 2> (S1) turns toward the woman and says, <d>[English] Last summer, I went to my grandfather's house.</d>
```

`<Subject N>` identifies the referenced subject, `(Sx)` the actual speaker. Off-screen keeps the same form marked `off-screen`. A speaker with no defined subject uses a stable voice description plus `(Sx)`.

Verbal content existing only inside a directly reused soundtrack, with no person producing it, uses `<Audio N>` as the source and gets no `(Sx)`:

```
When <Audio 1> reaches the phrase <d>[English] I'm lonely lonely lonely</d>, <Subject 1> performs the corresponding hand gesture without becoming a separate speaker source.
```

Directly reused dialogue or lyrics keep the exact source words and original language inside `<d>`; write `[unclear]` rather than guessing. Standardise punctuation to `,` `.` `?` `!` and strip tildes, emoji, bullets and decoration. When only timbre, rhythm, emotion or delivery is referenced, **do not carry the original dialogue across**.

Never write `(Sx)` in `retention_analysis`.

## 5. Sound sections

`overall_soundscape` and `non_diegetic_music` follow `prompting.md`. State a copy or reference relationship only in the section matching the audible layer — ambience and effects in the soundscape, audience-only score in the music field:

```
overall_soundscape: The copied ambience layer from <Audio 1> continues throughout the target video.
non_diegetic_music: <Audio 2> is directly reused as the complete audience-only score.
```

Complete dialogue and lyrics live only inside `<d>` in `detailed_description` and are never repeated here.

## Complete example, verbatim from the guide

```
subject_definitions:
<Subject 1> is the coffee-shop environment in <Picture 1>, featuring an exposed brick wall, an orange tufted sofa with patterned pillows, a neon sign, and a wooden coffee table.
<Subject 2> is the fluffy white Samoyed in <Picture 2>, <Picture 3>, and <Picture 4>, with thick white fur, pointed ears, a dark nose, and a curved tail.
<Subject 3> is the young blonde woman in <Video 1>, with long blonde hair and a light-pink button-down shirt with rolled-up sleeves.
<Subject 4> is the young man in <Video 2>, with short wavy brown hair and a dark-grey hoodie with drawstrings.
<Audio 1> is the voice-timbre reference for <Subject 3> (S1), containing a spoken English vocal layer.

summary:
[reference generation + audio reference] The target video shows <Subject 3> eating a cookie in <Subject 1>. <Subject 4> enters with <Subject 2>, which lunges toward the cookie. The three-shot exchange uses <Audio 1> as the voice-timbre reference for <Subject 3> and ends with a canned audience laugh.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - the exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table are retained.
<Subject 3> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - the blonde woman's identity, long hair, and light-pink shirt are retained.
<Audio 1>: reference - its vocal timbre guides the dialogue delivery of <Subject 3> without copying the original signal.

detailed_description:
The target video uses a realistic multi-camera sitcom style with warm indoor lighting.
[Shot 1] A medium shot establishes <Subject 1>, the coffee shop with its exposed brick wall, orange tufted sofa, patterned pillows, neon sign, and wooden coffee table. <Subject 3> (S1), the young woman with long blonde hair and a light-pink button-down shirt with rolled-up sleeves, sits on the sofa holding a chocolate-chip cookie...

overall_soundscape:
Soft indoor coffee-shop room tone continues throughout the scene.

non_diegetic_music:
N/A
```

Note that `<Subject 3>` and `<Subject 4>` are people taken **from videos** — and they are subjects, not `<Video N>` entries. `<Video 1>` and `<Video 2>` are never even defined as standalone labels here, because they only identify where those subjects came from.
