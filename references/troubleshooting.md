# Troubleshooting — symptom → cause → fix

## A physical camera or phone appears in the shot

**Cause.** `camera` was written as a noun the subject interacts with. H3 parses `she holds the camera above her head` as a prop to render.

**Fix.** Keep `camera` inside the directive line only (`Camera: crane up, tilt down…`). Describe the arms with no device: `she lifts both arms toward the viewer, hands passing just outside the top corners of the frame`. Put the camera move and the body move in separate sentences. If it persists, drop the noun entirely and write `Shot: handheld crane up, tilt down to high angle, continuous take`.

## The subject raises a hand but the object never appears

**Cause.** Objects absent from the reference rarely materialise mid-shot.

**Fix.** Either supply the object as its own reference image with an explicit role (`<Picture 3> is the bottle she lifts`), or restructure so the object is the viewpoint and therefore off-frame.

## Identity drifts / the face becomes someone else

**Cause, in order of likelihood.**

1. Wrong mode — a viewpoint absent from the source photo was forced through I2V, so the model hallucinated the body mid-rotation.
2. `ref_image_size` left at `match`.
3. Only one reference image, for a shot that reveals angles it does not cover.
4. Two references competing for the identity axis.
5. Encoder quantised to `nvfp4_awq` — identity flows through the encoder in R2V.

**Fix.** Switch to R2V. Set `ref_image_size` to `max`. Add 2–3 references covering the angles the shot will reveal, each with an explicit job. If the shot must stay I2V, shorten the camera travel — a three-quarter back view at ~120° survives where a full 180° does not. On a large-VRAM card, step the encoder up to `int8_convrot` or `bf16`.

## The room, light or grain changes between start and end

**Cause.** R2V regenerates the scene; it does not preserve the source photo's environment. Or, in FLF2V, the two endpoint frames do not match.

**Fix.** If the environment matters, that is an `fl2va` job, not `ref2va`. For FLF2V, make both frames share aspect ratio, resolution, grade, noise and sharpness. A retouched end frame produces a visible beautification morph.

## Extra fingers, fused hands

**Cause.** Hands fully in frame and heavily foreshortened, i.e. reaching toward the lens.

**Fix.** Crop them: `hands passing just outside the top corners of the frame`, `hands and wrists cropped off at the edges`. Do not reach for a negative prompt — there is no negative socket. State it positively if the hands must be visible: `five clearly separated fingers, a firm grip`.

## The negative prompt does nothing

**Cause.** The template uses `BasicGuider`, single conditioning input, CFG effectively 1. There is nowhere to attach a negative.

**Fix.** Rewrite bans as positive statements of the desired state. Do not swap in `CFGGuider` — it doubles inference time and H3 was not trained with guidance.

## Motion is mush, no readable camera move

**Cause.** Several camera moves stacked with equal weight in one beat.

**Fix.** One primary move per beat. If two are genuinely needed, split them across consecutive beats.

## The subject barely moves; the background breathes

**Cause.** The prompt describes a still frame rather than change over time.

**Fix.** Convert to timestamped beats, each naming something that changes. "She stands in the doorway" is not a beat; "she steps through the doorway" is.

## Motion is rushed or teleports between poses

**Cause.** The prompt's timeline is longer than the render length. 124 frames at 24 fps is 5.2 s — a 15-second brief gets crushed into it.

**Fix.** Match `length` to the beats, or cut beats. Long or complex camera travel wants 180–240 frames.

## Output is cut up when a continuous take was wanted

**Cause.** Multi-beat prompts read as a sequence of shots.

**Fix.** Add `one continuous take, no cuts` to the `Camera:` line. Conversely, name transitions explicitly (`hard cut`, `match cut`, `tape jump`) when you do want them.

## Unwanted music or wrong ambience

**Cause.** Audio was not written. H3 generates audio in the same pass regardless, so an unwritten track is a guess, not silence.

**Fix.** Always include an `Audio:` block. Name room tone, effects and their timing. Write `no music` explicitly.

## Reference roles suddenly swapped without a prompt change

**Cause.** `<Picture 1>`, `<Video 1>`, `<Audio 1>` are numbered by socket connection order on the node, not by filename. Rewiring reassigns roles.

**Fix.** Check the wiring order before blaming the prompt.

## Standalone audio reference rejected

**Cause.** Audio must accompany at least one image or video.

**Fix.** Attach a picture or clip alongside it.

## The event happens more times than asked ("exactly one shot" fires three)

**Cause.** Diffusion models do not count — `exactly one` is a token sequence, not a
constraint, and nothing tracks how many times an event occurred. Negation makes it
worse: `no second shot` puts *second shot* into the conditioning and raises its
salience, with no negative channel at CFG 1 to subtract it. On top of that, the
training prior for most actions is repetition — range footage almost always contains
a burst. Every mention of the event, bans included, adds weight to it.

**Fix.** Count the mentions in your own prompt; a typical failing prompt names the
event six times between the beats and the `Locks` block. Name it once, in one beat,
with no prohibition attached, and delete it from `Locks`. Then block repetition with
scene state rather than instruction — the muzzle lowered, smoke drifting, the spent
shell on the gravel, the stock off her shoulder. Put the event early and fill the rest
of the timeline with its consequences, so there is no idle time to repeat it in.

## A fall or impact never happens

**Cause.** "She falls" is an outcome, and the model smooths outcomes away. Or the
framing does not contain the ground she is falling toward. Or a cheaper event in the
prompt is being repeated instead — three shots fired rather than one fall.

**Fix.** Give the trajectory as intermediate poses — `her rear foot skids, her knees
fold, she hits the gravel sitting down, her legs stretch out in front of her`. Widen
the frame so the ground is in it. Constrain the cheap event explicitly (`exactly one
shot is fired in the whole clip`). Lock the end state or she springs back up.

## The fall looks weightless, like moon gravity

**Cause.** The beat is too long. Beat duration is read literally as event speed —
allocate 1.5 s to a fall and you get a 1.5-second fall, which is slow motion.

**Fix.** Budget about 0.5 s for the fall itself and spend the spare time on the
aftermath. Add `real-time speed throughout, no slow motion, no ramping` near the top
of the prompt. Weight comes from the stop, not the drop: `she stops dead on impact,
no float, no drift, no bounce`. Add consequences — dust kicking up, motion blur during
the fast part, hair settling a beat *after* the body has already landed.

## Output looks soft or noisy

**Cause.** Almost never the step count. Usually quantisation level or resolution.

**Fix.** Move up a quant tier before touching steps. `res_multistep` at 20 steps is already equivalent to 35–40 Euler steps; 30 costs 50 % more time for an invisible gain. On reference-heavy graphs, A/B the scheduler (`beta` or `normal` against `simple`) at a fixed seed — that is worth more than extra steps.

## Can't tell whether a prompt edit helped

**Cause.** `управление после генерации` / `control_after_generate` is on `randomize`, so the noise moved too.

**Fix.** Set it to `fixed` and change one note at a time.
