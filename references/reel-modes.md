# Reel Maker: ControlNet or Motion Strip

These are two **reel preparation workflows**, not new MiniMax checkpoint modes.
Both normally use **Ref2VA** with a compatible `ref2va` checkpoint. Keep the existing
MiniMax prompt format, source inspection, identity, dialogue and output-QC rules.

## Choose before preparing assets

Accept `ControlNet`, `controlnet`, `контролнет`, `Motion Strip`, `motion-strip`,
`motion strip`, `моушен стрип`. Record `reel_mode: controlnet` or
`reel_mode: motion_strip` in the package's asset/wiring notes, outside the pasteable
H3 prompt. This is documentation metadata, not a ComfyUI setting or a model token.

- Honour an explicit choice without asking again. Retain it for follow-ups to the same
  reel; changing it requires an explicit user request, not a silent fallback.
- If neither the current request nor that reel's existing package states a choice,
  ask one short question: **“Which Reel Maker workflow: ControlNet (pose/depth from
  the source video) or Motion Strip (a storyboard image)?”** Source inspection may
  continue, but do not prepare mode-specific assets, download weights or launch a render
  before the choice. A source video by itself does not imply either mode.
- Keep the modes separate. Combine them only on an explicit hybrid-test request and
  list every additional input and its role. Missing ControlNet dependencies do not
  authorise installing them, switching modes or renting compute without task authority.
- If the user only requests a prompt, provide the selected mode's prompt and wiring
  notes; do not turn that into an installation or generation job.

| | ControlNet | Motion Strip |
|---|---|---|
| Motion input | Time-aligned pose and/or depth IMAGE batches in ControlNet Apply | Chronological contact sheet in an ordinary Ref2VA image slot |
| Default image references | Picture 1: face; Picture 2: body proportions | Picture 1: face; Picture 2: target look/composition; Picture 3: motion strip |
| Appearance not supplied by those inputs | Wardrobe, room, props and light must be described explicitly | Look frame supplies appearance/composition; text still names important details |
| Extra requirements | Compatible H3 ControlNet weights, custom nodes and selected preprocessors | No ControlNet model or pose/depth preprocessor required |
| Main limitation | Bad or conflicting control maps can transfer jitter; exact motion and facial acting are not guaranteed | Sparse poses are guidance, not frame-by-frame control; written timing remains essential |

The slot maps are defaults for these workflows, not immutable filenames or a ban on
user-selected references. Inspect the actual graph and images. Preserve an explicitly
requested two-reference setup; add a composition image only when requested or agreed.
When slots change, renumber every prompt label and document the new roles.

## Shared source audit

Each source video needs its own description: an attached TXT/MD file, a matching sidecar
(for example `source.txt` or `описание видео*.txt`), or an ordinary user message mapped
to that video. Read it before drafting. If missing, ask for that video's description and
key intention before its final prompt; source inspection may continue. For several videos,
ask for a filename/ID-to-description mapping rather than recycling one description.
Do not ask again when a matching description is already present. Resolve material
differences between the description and footage explicitly. An explicit user request to
proceed without a description is allowed, with that limitation recorded.

Use the description to understand intent and emphasis, then compare its details with
the footage. Separate what is visible/audible from an author's interpretation. Inspect
dense sequential frames and enlarge ambiguous clothing, props, hand contact and facial
events at native resolution. Verify cuts against adjacent frames rather than accepting
scene-detector output blindly.

Record the opening state, clothing layers/colours/fit, garment coverage and changes,
handedness and actual hand-offs, props, room layout, lighting, camera path, complete
action phases, secondary motion and ending. Both modes need that detail in the prompt.
Neither depth maps nor a face/body photo tells H3 what the original outfit or room was.

Inspect the soundtrack for every source reel in either mode. If speech is present,
automatically transcribe it with timestamps and include the lines in the prompt; do not
wait for a separate transcription request. Distinguish on-screen speakers from offscreen
voices. First audible speaker is `(S1)`, even offscreen;
later new voices receive consecutive IDs. Use `<d>[Language] exact words.</d>`, separate
music lyrics from dialogue and mark uncertain words instead of inventing them. Record
no-speech or unavailable-audio status when applicable; neither authorises invented lines.
Run `python tools/check_prompt_dialogue.py <prompt-file>` on dialogue prompts; this checks
numbering and tags, not transcription accuracy. Do not
claim manual listening when only automatic transcription was available. Preserve the
package's selected audio-conditioning route; changing motion mode does not silently
change audio references, joint generation or the final soundtrack.

Describe observed blinks, gaze direction, brow/cheek/jaw changes and lip articulation
when relevant. An identity portrait is not a request to keep its frozen expression or
look into the lens throughout. Small coordinated body adjustments may be described
without replacing the source action with unrelated dancing. Hidden faces stay hidden;
missing facial landmarks are a limitation, not evidence of a neutral expression.

## ControlNet workflow

### Inputs and wiring

1. Inspect the existing ComfyUI graph, node definitions and model inventory. Reuse
   compatible installed files. Use the H3-specific adapter, not an SD/SDXL ControlNet.
   The documented implementation is
   [ComfyUI-H3-FunControl](https://github.com/wyzborrero/ComfyUI-H3-FunControl).
2. Its `H3FunControlLoader` loads from `ComfyUI/models/controlnet`. The documented
   compatible curve-form file is
   `minimax_h3_fun_controlnet_union_pruned_bf16.safetensors` from
   [Kijai/MiniMax-H3-experimental](https://huggingface.co/Kijai/MiniMax-H3-experimental).
   The original full-width Alibaba checkpoint is not interchangeable in this loader.
   Recheck the installed revision rather than assuming a filename establishes compatibility.
3. Load the source **once**, select the time interval, establish the target FPS and canvas,
   then send the same aligned frame batch to the pose and depth preprocessors. Start
   with DWPose when no pose extractor was specified; preserve a requested OpenPose or
   other compatible extractor and verify its rendered map instead of claiming it is
   universally better. Enable and inspect body, hand and face landmarks where needed.
4. For smoothing, if requested, smooth the selected extractor's keypoints before rendering
   its map, retaining body/hands/face, confidence and missing detections. Do not silently
   convert DWPose into a different skeleton or discard face points. Preview raw and smoothed
   sequences for jitter, temporal lag, hand swaps and lost expressions.
5. Feed the **rendered maps**, not the original RGB footage, to `control_video` on the
   applicable `H3FunControlApply` nodes. The input is an `IMAGE` batch, not raw vector
   keypoints. Use the H3 **video** VAE on both applies; the same union loader may feed both.

```text
source video -> one aligned frame batch -> depth estimator -> depth IMAGE batch
                                     \-> pose estimator -> [optional keypoint smoothing]
                                                        -> pose renderer -> pose IMAGE batch

ref2va MODEL -> H3FunControlApply (depth) -> H3FunControlApply (pose)
            -> existing H3 model/sampling branch -> guider/sampler
                     ^                         ^
              same union ControlNet + H3 video VAE

face image -> ref_image_0 --\
body image -> ref_image_1 --- MiniMaxH3ReferenceToVideo -> conditioning + joint latent
```

This is conceptual wiring, not an importable graph. Preserve the installed workflow's
sampling/sigma-shift order and verify its node names, ports and effective control window
against that version before producing JSON. The upstream example is
[`02_depth_plus_pose_reference.json`](https://github.com/wyzborrero/ComfyUI-H3-FunControl/blob/master/workflows/02_depth_plus_pose_reference.json).

The Ref2VA images define **one** target person: face/identity from `<Picture 1>`, body
proportions from `<Picture 2>`. Body-reference clothes are not automatically the target
outfit. Describe the observed target outfit, setting and props in subject definitions and
the shot body. There is no required `<Picture 3>`, generated first-frame image or strip.
Do not apply the Motion Strip look-frame gate to this two-image setup.

**A ControlNet input creates no `<Video 1>` or `<Picture 3>` in the text encoder.** Keep
control paths, model names, preprocessors and strengths in the wiring block. Only cite a
`<Video N>` if a clip is actually connected to a Ref2VA video-reference socket. Do not
tell the model to render a skeleton, a depth map, coloured joints or a storyboard.

### Alignment and strengths

- Measure the frame batch **after** trim, FPS conversion and resizing. Pose, depth and
  target generation must share frame order/count, width and height. Apply the same
  spatial transform to both branches; preserve aspect ratio and record any agreed crop/pad.
- Native H3 uses 24 FPS and the `17k+5` length grid. A node silently rounding the target
  up does not add matching control frames. If the source has insufficient frames, resolve
  the mismatch before sampling: explicitly choose a valid shorter segment or an agreed
  extension/interpolation policy. Never silently append duplicate frames or retime motion.
  A user's requested crop takes precedence over padding. Preview the aligned first,
  action and final frames and record the exact chosen interval and output length.
- `strength` is an independent multiplier on each apply; chained contributions add.
  The upstream example uses **depth 0.3 + pose 0.7**, with `start_percent=0` and
  `end_percent=1`. This is a reproducible starting example, **not the only valid pair**.
  The checked node accepts `strength` from 0 to 2; it does not forbid 0.5/0.5 or require
  the sum to equal 1. The upstream author's saturation reports are observations from
  particular shots, not universal thresholds. Keep existing successful settings unless
  tuning is requested, then vary one factor at a fixed seed.
- `start_percent`/`end_percent` control the denoising interval, not the portion of the
  source video's timeline. Shortening the window may loosen structure as well as texture;
  do not advertise it as a guaranteed face fix.
- If the result jerks, inspect the source maps, missing landmarks, FPS/count alignment,
  conflicting pose/depth, control weights and patch compatibility before diagnosing a
  forbidden strength pair. Face points alone do not guarantee expression transfer or lip sync.

Upstream reports the ControlNet was trained with `fl2va` and used experimentally with
`ref2va`. That combination is useful community practice, not an official guarantee.

### ControlNet readiness

Verify node availability and weight compatibility; preview both map sequences at normal
speed and inspect difficult intervals. Confirm requested face/hands survive extraction
and optional smoothing. Check actual graph links, image labels, exact aligned dimensions,
FPS, frame count, control strengths/window and audio route. Check the prompt's wardrobe,
scene, props, acting and camera against source evidence. Mark unavailable checks **not
verified**, rather than treating a parseable workflow as ready. No strip/look-frame test
is required when those assets are intentionally absent.

## Motion Strip workflow

Use the image-reference convention: `<Picture 1>` identity, `<Picture 2>` a target
look/composition frame, `<Picture 3>` the chronological motion-only strip. Scope identity
inside the target `<Subject N>`; the look frame may have its own composition role; the
strip supplies the action progression, not the source actor's identity or clothes.
If the user chooses another slot map, document it rather than silently restoring three images.

Build the strip from the selected source interval. Preserve the complete source frame
and each panel's aspect ratio unless a crop was explicitly requested. Use proportional
scaling; derive width from height, never stretch into a predetermined panel rectangle.
Use 990 px panel height as this project's default, not as an H3 requirement. Choose enough
distinct phase anchors for the actual action, including intermediate fast-motion phases;
different timestamps with near-identical poses do not establish those phases. Keep panels
legible at the actual reference-encoding scale. Do not crop important body parts or props
just to remove captions.

Read the saved strip, compare the look frame with the intended composition, and write the
motion as ordered waypoints on one causal trajectory with measured beat timings. The
strip is a still image: it does not encode playback speed. Give exact clothing, setting,
props, camera direction and relevant facial performance in prose even when visible in
the look frame. One strip per rendered source segment; do not reuse the whole-reel strip
for every segment.

ControlNet models, Apply/Loader nodes and pose/depth estimation are **not dependencies**
of this mode. Do not download them. A diagnostic contact sheet used only for source
inspection is not automatically a motion reference; wire only the chosen final strip.

### Motion Strip readiness

Verify actual image order/roles, look-frame composition, readable distinct strip phases,
panel aspect ratios, source-aligned timing, consistent text/reference scope and the audio
route. Check that a still portrait is not being treated as the required facial performance.
Do not claim control-map validation when this mode has no control maps.

## Handoff and switching

State the selected `reel_mode`, exact asset-slot map, source interval, target FPS/count,
complete pasteable prompt and applicable readiness results. A mode name in a prompt does
not rewire ComfyUI. When switching modes, update the graph and asset list first, remove
references to absent inputs from the prompt, then rerun the chosen mode's checks.
After any render, verify the actual output and audit motion, camera, appearance, face,
audio and ending against the source. Report structural checks separately from GPU-tested
quality; this documentation update itself is not a generation test.
