# Troubleshooting — symptom → cause → fix

Mixed evidence, and the difference matters. **Official** marks a rule stated in MiniMax's guides. **Implementation** marks behaviour visible in the ComfyUI source or stock workflow. **Empirical** marks a render tendency or an inferred symptom-to-cause link. A structural rule can be Official while the claim that breaking it causes a particular artifact is only Empirical — most entries below are exactly that pairing, so read the causes as *likely* rather than demonstrated. See `SOURCES.md`.

## A multi-view character sheet gives worse identity than plain photos

**Reported outcome.** Attaching a grid-format character reference sheet — front, profile, back, face close-ups and hands on a neutral background, all in one image — performed noticeably worse than separate photographs. Tried once by a user on 2026-08-04; not measured against a control.

**Likely cause.** The sheet is resized as a single image, so at `ref_image_size: max` a 3 × 3 grid gives roughly 680 px per panel against 2048 px for a dedicated still. Every view arrives at about a third the linear detail. The grid's own structure — framed panels, gutters, a repeated figure, a seamless backdrop — is also visible content competing with the target scene.

**Do not recommend sheets.** Use separate full-resolution photographs, two to four of them, covering the angles the shot will actually reveal. If a user already has a sheet, treat it as one weak reference among several rather than as the primary identity source.

## Identity drifts, or the face flickers between two people

**Cause, in order of likelihood.**

1. Identity was put in a standalone `<Picture N>` instead of `<Subject N>`. The guide explicitly says an image that only defines a character gets no picture entry of its own.
2. Two references compete for the identity axis — typically a reference video containing a person alongside a reference still. This is an empirical hypothesis, not a mechanism read from the source: the encoder actually presents stills as `<Picture i>` vision blocks and video as timestamped two-frame blocks sampled at 2 fps, and the DiT receives separate image and video reference kinds. How the model weighs repeated video appearances against one portrait is not established anywhere.
3. Wrong mode: a viewpoint absent from the source photo was forced through I2VA, so the model hallucinated the body mid-rotation.
4. `ref_image_size` left at `match` — but only if the reference is above ~1 MP, since below that both settings are identical no-ops.
5. Encoder quantised to `nvfp4_awq` — identity flows through the encoder in reference mode.

**Fix.** Define one merged subject naming each source's contribution: `<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.` Scope the video's role in `retention_analysis` with `weak_reference` and an explicit list of what it does *not* supply. Set `ref_image_size` to `max`. Shorten long camera travel — a three-quarter back view survives where a full 180° does not. On a large-VRAM card, step the encoder up to `int8_convrot` or `bf16`.

## A reference video drags its wardrobe, location or lighting into the output

**Cause.** The video was given no scoped role, so it contributes on every axis. `Do not take the person from <Video 1>` is a text instruction competing against a data signal, with no negative channel at CFG 1 to enforce it.

**Fix.** Put the scope in `retention_analysis`, where the format expects it: `<Video 1> (camera movement and pacing): weak_reference - only the travelling path and handheld rhythm are followed; none of its people, wardrobe, location or lighting appear.` Better still, remove the competition — if you want camera motion, shoot the reference orbiting an object with no person in frame.

## A physical camera or phone appears in the shot

**Cause.** `camera` was written as a noun the subject interacts with. H3 parses `she holds the camera above her head` as a prop to render.

**Fix.** Use the official camera vocabulary for the movement (`the camera pedestals up with large amplitude at slow speed`), describe the arms with no device (`she lifts both arms toward the viewer, hands passing just outside the top corners of the frame`), and keep the two in **separate sentences** — joined by a verb of possession they resolve into an object. When the device *is* the viewpoint, use the `POV` motion type and never mention it at all.

## The subject rotates instead of the camera

**Cause.** Camera motion is the weakest axis in text conditioning; the model substitutes subject animation, which it knows far better. `She turns` is also read as a whole-body spin.

**Fix.** Use `Arc Shot` — the official term for the orbit you were describing longhand — with explicit amplitude and speed. Forbid body rotation in specific parts (`her feet, hips and shoulders stay facing the same direction; only her head turns`). Then describe **parallax**: `the lamp and dresser slide from the right edge of the frame to the left and out of view`. A static camera cannot sweep the background, so if the model renders the sweep, the camera moved.

## Head inverted, breasts on the back, anatomy scrambled

**Cause.** An impossible pose. Camera directly behind + body forbidden to rotate + eye contact requires roughly a 170° neck twist, and the model resolves the contradiction by inverting the head or blending front and back anatomy.

**Fix.** Remove the contradiction rather than adding constraints. Stop the camera at three-quarter behind, let the shoulders rotate slightly with the head, and add an anatomy lock: `her chin never goes past her shoulder; her head and chest always face the same general direction; she never bends backwards`.

## The subject raises a hand but the object never appears

**Cause.** Objects absent from the references rarely materialise mid-shot.

**Fix.** Supply the object as its own `<Subject N>` with a source, or restructure so it is the viewpoint and therefore off-frame.

## Extra fingers, fused hands

**Cause.** Hands fully in frame and heavily foreshortened, reaching toward the lens.

**Fix.** Crop them — `hands passing just outside the top corners of the frame`. There is no negative prompt to fall back on; if the hands must be visible, state the desired condition positively: `five clearly separated fingers, a firm grip`.

## The negative prompt does nothing

**Cause.** The ComfyUI template uses `BasicGuider` — one conditioning input, CFG effectively 1, no negative socket.

**Fix.** Rewrite bans as positive statements of the desired state. Do not reach for `CFGGuider` casually: it doubles inference time, and how H3 was trained with respect to guidance is not established by any source here.

## The event happens more times than asked

**Cause.** Diffusion models do not count — `exactly one shot` is a token sequence, not a constraint. Negation makes it worse: `no second shot` puts *second shot* into the conditioning. And the training prior for most actions is repetition. Every mention, bans included, adds weight.

**Fix.** Count the mentions in your own prompt; a failing prompt typically names the event six times across the body and the locks. Name it once, with no prohibition attached. Then block repetition with **scene state**: the muzzle lowered, smoke drifting, the spent shell on the gravel, the stock off the shoulder. Put the event early and fill the rest of the timeline with its consequences.

## A fall or impact never happens

**Cause.** "She falls" is an outcome, and the model smooths outcomes away. Or the framing does not contain the ground. Or a cheaper event in the prompt is being repeated instead.

**Fix.** Give the trajectory as intermediate poses — `her rear foot skids, her knees fold, she hits the gravel sitting down, her legs stretch out in front of her`. Widen the frame so the ground is in it. Lock the end state or she springs back up.

## The fall looks weightless, like moon gravity

**Cause.** The beat is too long. Duration is read literally as event speed — allocate 1.5 s to a fall and you get a 1.5-second fall, which is slow motion.

**Fix.** Budget about 0.5 s for the fall and spend the rest on the aftermath. Add `real-time speed throughout, no slow motion`. Weight comes from the stop, not the drop: `she stops dead on impact, no float, no drift, no bounce`. Add consequences — dust kicking up, motion blur during the fast part, hair settling a beat *after* the body lands.

## Motion is mush, no readable camera move

**Cause.** Several camera moves stacked with equal weight in one shot.

**Fix.** One primary move per shot, with amplitude and speed stated. Split genuinely necessary second moves across consecutive shots.

## The subject barely moves; the background breathes

**Cause.** The description states a still frame rather than change over time.

**Fix.** Every clause should name something that changes. "She stands in the doorway" is not an action; "she steps through the doorway" is.

## Motion is rushed or teleports between poses

**Cause.** The written timeline is longer than the rendered length. 124 frames at 24 fps is 5.17 s.

**Fix.** Match frame count to the timeline, or cut shots. Long camera travel wants 192–243 frames. Note that `length` snaps **up** to the nearest `17k+5` value without telling you — 144 silently becomes 158, 168 becomes 175. Pick from the grid directly: 124, 141, 158, 175, 192, 209, 226, 243, 260, 277, 294, 311, 328, 345, 362.

## The output is cut up when one continuous take was wanted

**Cause.** Multiple `[Shot N]` markers are literally multiple shots.

**Fix.** Use one shot and express the change through camera motion. The guide's own rule: if only distance or a slight angle changes, prefer camera motion over a cut.

## Unwanted music or wrong ambience

**Cause.** `non_diegetic_music` was omitted. H3 generates audio in the same pass regardless, so an unwritten track is a guess.

**Fix.** Always write both sound fields. `N/A` for no score. Keep abstract mood words out of the music field — instrumentation, tempo, rhythm, dynamics only.

## Reference roles swapped without a prompt change

**Cause.** Labels are numbered **per type, by slot index, inside a fixed category order** — images, then videos, then standalone audio — not by filename or by the sequence in which you dragged the wires. Moving an asset to a different slot renumbers it. A reference video's soundtrack also claims `<Audio 1>` ahead of any standalone clip.

**Fix.** Check the wiring order before blaming the prompt.

## Standalone audio reference does nothing

**Cause.** *Not* a missing image or video — current ComfyUI iterates `ref_audios` unconditionally and accepts standalone audio on its own. The widely repeated "standalone audio is rejected" is a community claim the source contradicts.

**Fix.** Check the node is current, that the clip reaches a `ref_audio_N` socket, and that the loader returns a valid waveform and sample rate. Do not add visual media to satisfy a requirement that does not exist. Remember also that the audio never reaches the text encoder — only its `<Audio j>` label does — so it cannot carry meaning through the prompt path.

## Output looks soft or noisy

**Cause.** Almost never the step count. Usually quantisation level or resolution.

**Fix.** Move up a quant tier before touching steps. `res_multistep` needs fewer steps than `euler` for comparable convergence, so 20 is not as low as it looks — though the usual "equals 35–40 Euler" figure is a rule of thumb, not a measurement. On reference-heavy graphs, A/B the scheduler (`beta` or `normal` against `simple`) at a fixed seed.

## Can't tell whether a prompt edit helped

**Cause.** `control_after_generate` is on `randomize`, so the noise moved too.

**Fix.** Set it to `fixed` and change one thing at a time.
