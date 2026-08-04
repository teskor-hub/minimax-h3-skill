# The official format — T2VA / I2VA / FL2VA / L2VA

Source: MiniMax's own `VIDEO_PROMPT_WRITING_GUIDE_base_en.md`. This is the shape the model's prompt rewriter emits, so it is the shape the model was trained to consume.

## The four frame-conditioned modes

| Mode | What it is |
|---|---|
| **T2VA** | a complete audiovisual timeline built from text alone |
| **I2VA** | T2VA plus a first-frame instruction, developing forward from that frame |
| **FL2VA** | T2VA plus a first-and-last-frame instruction, a continuous path between them |
| **L2VA** | T2VA plus a last-frame instruction, converging from a plausible earlier state |

All four run on the `fl2va` checkpoint.

## Part one — the alignment instruction

T2VA has none and begins directly with the core fields. The other three open with an exact line, followed by **one blank line** before the fields.

**I2VA**
```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```

**FL2VA**
```
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
```

**L2VA**
```
How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

`N` is the index of the actual final shot. `S.SS` is the effective duration to exactly two decimals.

## Part two — the three core fields

```
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

- **integrated_multimodal_description** — visuals, actions, shots, speakers, dialogue, singing and diegetic sound along the timeline
- **overall_soundscape** — ambience, physical action sounds and non-verbal human sounds across the whole video
- **non_diegetic_music** — score the characters cannot hear

## Building the description

### Open with style

`[Shot 1]` states the overall style and initial composition. Named styles: `Cinematic`, `live-action`, `2D-animated`, `3D CG`, `claymation`, `watercolor`, `vintage film`. For keyframe tasks derive the style from the reference image.

```
[Shot 1] Live-action, cinematic, a medium-wide shot frames a baker opening the shutters...
```

### Shots and cuts

`[Shot 1]` takes no timestamp. Every later shot opens with a strictly increasing cut time inside the video duration:

```
[Shot 2] At 00:03.500, the camera cuts to...
```

Cut phrasings: `the camera cuts to`, `the shot cuts to`, `the shot transitions to`, `the shot changes to`, `the shot switches to`. Cross-dissolve, fade and wipe only when the user asks.

**A cut must introduce new information** about subject, space, state, viewpoint or time. If only distance or a slight angle changes, use camera motion instead.

### Camera motion — type + amplitude + speed

| Dimension | Values |
|---|---|
| Type | `Zoom In / Zoom Out` · `Push In / Pull Out` · `Pan Left / Pan Right` · `Truck Left / Truck Right` · `Tilt Up / Tilt Down` · `Pedestal Up / Pedestal Down` · `Arc Shot` · `Tracking Shot` · `Static Shot` · `Shake Slightly / Shake Strongly` · `POV` · `Roll Clockwise / Roll Counterclockwise` |
| Amplitude | `with small amplitude` · `with large amplitude` |
| Speed | `at slow speed` · `at fast speed` |

Medium amplitude and normal speed are omitted. Write the move as a natural action inside the sentence, not as tags appended to it:

```
The camera pushes in with small amplitude at slow speed toward the folded letter in her hands.
The camera pans right with large amplitude at fast speed, revealing the open doorway.
The camera holds a static shot as the runner exits the frame.
```

Note the two that solve common problems: **`Arc Shot`** is the orbit you were describing longhand, and **`POV`** is how you get a subject's-eye view without ever naming a device.

### Speakers, dialogue, singing

Stable IDs `(S1)`, `(S2)`; a compound `(S1,S2)` when numbered speakers vocalise together. IDs persist across shots. Characters who never vocalise get no ID.

On first appearance, establish identity from visual and audio context — type, age, gender, on- or off-screen, pitch, timbre, rate, accent. The identifying phrase, ID, action and delivery go **outside** `<d>`; inside `<d>` goes only the language tag and the exact spoken content, verbatim, untranslated.

```
The young woman with a quiet, breathy voice (S1) says: <d>[English] I get off at the next station.</d>
The two children (S1,S2) shout together, <d>[English] Wait for us!</d>
```

Voiceover uses the exact phrase `says in an off-screen voiceover`, and every voiceover `<d>` is immediately followed by a statement that the on-screen character's lips stay closed:

```
The man (S1) says in an off-screen voiceover: <d>[English] I still remember that road.</d> while his lips remain completely closed.
```

A line crossing a cut uses `<scenetrans>` at both connecting points plus an explicit continuity statement — `continues seamlessly across the cut`, `continues uninterrupted into the next shot`, `carries over from the previous shot`, `remains audible across the transition`. Speech truncated by the video ending uses `<cutoff>`.

### On-screen text

Anything actually visible — banner, sign, label, subtitle, neon — goes in English double quotes, verbatim, untranslated.

```
A red neon sign reading "营业中" glows above the doorway.
```

### overall_soundscape

1–4 sentences, one paragraph: wind, rain, traffic, footsteps, fabric, impacts, breathing, laughter, panting. Dialogue, singing and diegetic music stay in the description and are not repeated here. `N/A` only for explicitly requested total silence.

```
overall_soundscape: Steady rain taps against the café windows while low room ambience continues underneath. The entrance bell rings once, followed by wet footsteps and the soft scrape of a chair.
```

### non_diegetic_music

1–3 sentences on instrumentation, speed, rhythm and dynamics. **No abstract mood words and no explanation of emotional function.** Music the characters can hear — singing, instruments, radio, TV, a phone — is diegetic and belongs in the description instead. `N/A` when there is none.

```
non_diegetic_music: Sparse piano notes at a slow tempo, joined by sustained low strings that gradually increase in volume before fading out.
```

## Per-mode structure

**I2VA** — `<Picture 1>` *is* frame 0 and belongs to `[Shot 1]`. Establish the image's style, subjects, composition and anchors, then describe the next action. Identity, clothing, colours, key objects and spatial relationships stay consistent.
Shape: **first-frame anchor → action onset → continuous development → result or reaction**

**FL2VA** — Picture 1 opens, Picture 2 closes. Do not restate two static images; supply the motion path between them. **Favours a single shot** so the model can interpolate continuously; use multiple shots only when explicitly asked. The last frame must be reached at the end of the final shot.
Shape: **first-frame state → observable intermediate changes → progressively narrowing differences → last-frame state**

**L2VA** — `<Picture 1>` is the final frame and belongs to the last `[Shot N]`, not to Shot 1. Infer a plausible earlier state, then converge.
Shape: **plausible preceding state → explicit action and transition path → gradual convergence → last-frame landing**

## Worked example — I2VA, verbatim from the guide

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, the young woman shown in <Picture 1> remains beside the rain-covered train window, preserving her appearance, clothing, seat position, and the carriage layout. The camera trucks right with small amplitude at slow speed as she lifts her gaze from the folded letter toward the passing city lights. Her reflection moves across the glass while the quiet, breathy young woman (S1) says: <d>[English] I get off at the next station.</d> She folds the letter along its existing crease.

overall_soundscape: The train wheels produce a steady metallic rhythm beneath a low ventilation hum. Rain ticks against the window while paper rustles softly in her hands.

non_diegetic_music: Sustained cello notes at a slow tempo with widely spaced piano tones, gradually decreasing in volume.
```

Note what it does *not* do: no keyword cloud, no `cinematic masterpiece 8k`, no negative list, no re-description of what is already visible in Picture 1 beyond naming the anchors it must preserve.
