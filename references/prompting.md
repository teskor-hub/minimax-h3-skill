# Prompting MiniMax H3 in depth

## Why structure beats prose

H3 is a timeline model. It reasons about *what changes between second 1 and second 3*, not about a description of a picture. Two prompts with identical vocabulary produce very different results depending on whether the vocabulary is arranged as a keyword cloud or as playback order.

The failure this prevents is the most common one in the wild: describing a **still frame** and getting a still frame with drift. `A woman in a dim bedroom, warm lamp light, cinematic, beautiful` gives you five seconds of a face slowly melting. `[0-2s] she turns her head toward the lamp; [2-5s] she looks back into the lens` gives you a shot.

## The five blocks

### Roles — R2V only

Every reference gets an explicit job. The guides converge on this as the number one R2V failure: attaching files without telling the model what each is for.

```
<Picture 1> locks the character's face, hairstyle and body proportions.
<Picture 2> sets the film stock, palette and grain.
<Picture 3> is the bottle she lifts.
<Video 1> supplies walking rhythm and camera pace only — not the subject, not the location.
<Audio 1> sets the voice timbre.
```

Split concerns deliberately. "Video 1 for motion, Picture 1 for identity" works because each reference owns one axis. Two references silently competing for the same axis is the second-biggest failure mode — if two images both imply a face, say which one wins.

Numbering follows **socket connection order** on `MiniMaxH3ReferenceToVideo`, not filename order.

### Beats — timestamped action

```
[0-5s]   she moves along the benches
[5-10s]  she lifts the bottle into the backlight
[10-15s] she sets it down
```

Rules:
- 1–3 beats per 5 seconds. More beats than that and each gets a fraction of a second.
- Match beat count to duration. A 3-beat prompt rendered at 5 s is rushed; a 1-beat prompt at 15 s stalls and the model invents filler.
- Every beat names a *change*. "She stands in the doorway" is not a beat. "She steps through the doorway" is.

### Look — production language

Name the capture technique, not the vibe:

```
handheld with natural micro-wobble, warm low-light, soft film grain,
shallow depth of field, slight autofocus delay, amateur phone-camera look
```

Dead words that consume tokens and steer nothing: `cinematic`, `masterpiece`, `beautiful`, `8k`, `ultra-detailed`, `award-winning`.

Transitions, when you need them, are named explicitly: `hard cut`, `match cut`, `wipe`, `tape jump`. Say `one continuous take, no cuts` when you want no transitions — otherwise a multi-beat prompt may get cut up.

### Sound — its own track

H3 renders stereo audio in the same pass as the picture. Leaving it unwritten does not produce silence; it produces the model's guess, which is usually generic music.

```
Quiet room tone throughout. Soft rustle of fabric as she lifts her arms.
One calm breath near 4s. No music.
```

Patterns that work:
- name instruments and their entry time — `lo-fi drum machine from 0s, tape-noise sample joins at 2.5s, melody fades over the last second`
- pair diegetic sound with the action that causes it — `footsteps landing`, `a faint knock of fingers on plastic`
- for speech, give the line verbatim in quotes plus delivery — `she says, "I thought we had more time," quietly`
- say `no music` or `no dialogue` when you mean it

### Locks and bans

Constraints go **up front**, not appended at the end where they get diluted.

```
Keep identical: her face proportions, the freckles across her nose, the small
cross tattoo under her right eye, hair length, the grey ribbed tank top.
Never: on-screen text, watermarks, subtitle bars, studio lighting.
```

## Worked examples

Verbatim from published guides, showing the shape at different complexity levels.

**R2V, identity + motion split across references:**

> Use Image 1 as the locked character reference. Preserve the face, hairstyle, age, outfit, and body proportions. Use Video 1 only for walking motion and camera pace. Place the character in a rain-covered night market. End as she stops under a blue streetlight and looks toward the camera.

Note the shape: role assignment → new scene → explicit ending. The ending clause matters; without it the model decides where to leave the shot.

**R2V, three references each with one job:**

> Use reference images for the character's face and wardrobe. Use reference video for relaxed walking rhythm. Use reference audio for warm mid voice timbre. Create a 10-second medium shot on a windy coastal boardwalk at golden hour. The character walks toward camera, smiles once, and says a short free-spirited line. Camera tracks backward smoothly. Keep identity and wardrobe consistent. End on a stable medium close-up.

**R2V, camera path borrowed from a video reference:**

> Reference the camera path from Video 1: a back-following steadicam move through changing light zones. Generate a modern city walk from a warm cafe interior to a busy street and then into a subway stairwell. Keep the lighting transition smooth and do not cut away from the main subject.

**I2V, product, geometry locked:**

> The watch remains centered as a narrow band of warm light travels across the brushed metal case. Fine mist moves slowly behind the product. Camera trucks slightly right while preserving watch geometry and the dark marble surface. No redesign of the dial. End on a clean three-quarter product angle with the dial fully readable.

`No redesign of the dial` is the lock. In I2V the input is frame 0, so locks are about preventing drift away from it.

## The camera-as-object trap

H3 parses `camera` as a scene noun when the sentence gives the subject a grip on it. `She holds the camera above her head` reliably renders a physical camera in her hands, which is almost never what the user wanted — they wanted the *viewpoint* to be above her head.

The fix is grammatical, not semantic:

1. `camera` appears only in the directive line — `Camera: crane up, tilt down to high angle, handheld` — where it reads as an instruction.
2. The subject's action never mentions a device: `she lifts both arms up and forward toward the viewer, elbows opening wide, her hands passing just outside the top corners of the frame`.
3. Camera movement and body movement live in **separate sentences**. Joined by a verb of possession, the model connects them through an object; kept apart, the viewer's brain connects them and the model has nothing to render.

If a device still materialises, drop the noun entirely: `Shot: handheld crane up, tilt down to high angle, slow arc, continuous take`.

Same logic for `lens` (`looks into the lens` occasionally spawns glass — fall back to `looks straight at the viewer`) and for any phone that is meant to *be* the camera.

## Common mistakes

| Mistake | What happens |
|---|---|
| Keyword cloud, no temporal change | five seconds of drift and morphing |
| Still-frame description | subject barely moves, background breathes |
| References attached without roles | model averages them into a stranger |
| Two references competing for one axis | identity flickers between them |
| Competing camera moves stacked equally | motion mush, no readable move |
| Constraints buried at the end | constraints ignored |
| Mode mismatch (background described in I2V) | conflicts with frame 0, causes warping |
| Mixing first/last frames with references | the unused path is silently dropped |
| Rewriting the whole prompt to fix one thing | you learn nothing about which change worked |
| Negative-prompt lists | no negative socket exists at CFG 1; ignored |

## Iteration protocol

1. Fix the seed (`управление после генерации` → `fixed`) the moment you get something close.
2. Change exactly one note — identity, motion, camera, or constraint.
3. Re-render, compare.
4. Only then move the seed again to check the change generalises.

With `randomize` on you cannot attribute a change to the prompt, because the noise moved too. This costs more wall-clock than any sampler setting.

## Sources

- fal.ai — MiniMax H3 Prompting Guide
- Morphic — How to use MiniMax H3: references, editing, and audio
- Topview — MiniMax H3 in ComfyUI: Day-0 Local Guide
- ComfyUI docs — MiniMax H3 workflow examples
- ComfyUI blog — MiniMax H3 Day-0 Support
