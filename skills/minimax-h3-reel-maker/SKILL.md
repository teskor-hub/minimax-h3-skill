---
name: minimax-h3-reel-maker
description: >-
  Prepare MiniMax H3 Ref2VA reels in two workflows: reproduce a supplied source clip with scene photos, pose/depth ControlNet and TS smoother, or create a new video from photos and text alone. Use for H3 reference-based video preparation and its ComfyUI graphs.
---

# MiniMax H3: two reference workflows

Use the bundled graphs and preserve the user's intended scene, clothing, props, actions and audio requirements. This skill prepares a generative reconstruction, not a pixel-preserving face-swap. It does not authorize paid compute, uploads, installation, queue changes or messages to other people by itself.

## Select the workflow without requesting unnecessary assets

- A source video is supplied and its motion/cuts should be reproduced: **Ref + ControlNet**, recorded as `control`. Use `assets/01_REF_CONTROLNET_TS.json`. Keep depth, DWPose and **TS Pose Keypoint Smoother**.
- No source video is supplied: **Ref Only**, recorded as `refs`. Use `assets/02_REF_ONLY.json`. Work from available photos and the requested action. **Do not ask for or require a source reel, pose video, depth maps, ControlNet, TS smoother or source audio.** These nodes and source dependencies are absent from this graph.
- An explicit mode choice overrides automatic selection. If the user supplies a clip but wants only its aesthetic, the clip need not become motion control. Do not turn a photos-only request into a reconstruction task.

Both workflows use H3 `ref2va` weights. They are preparation workflows, not separate checkpoints. Motion Strip and Hybrid are not defaults in this handoff.

Read [workflows.md](references/workflows.md) for models, dependencies, controls, alignment, installation and packaging. Read [prompting.md](references/prompting.md) before writing the full prompt. Recorded versions and test limits are in [provenance.json](references/provenance.json).

## Prepare the inputs

**With a source clip:** read its matching description, inspect dense frames across the full selected interval and inspect the audio. Use the description for intent and footage for evidence. Identify people, garments, props, room layout, opening/ending states, cuts, camera motion, facial acting and critical action beats. Resolve contradictions instead of silently simplifying the scene. If a meaningful description is missing, ask only for the missing intent; an explicit request to proceed from footage alone is sufficient.

**Photos only:** inspect the available photos and the user's scene/action request. Infer the needed setup from those inputs. There is no missing-source-video blocker. Ask a concise question only when the desired action or a crucial appearance choice is unclear. Select an exact duration appropriate to the action; 124 frames at 24 FPS is a usable short starting example, not an obligatory test.

Assign every connected photo a distinct role. The established source-video layout is P1 face, P2 body proportions and P3–P5 one to three full-frame scene anchors. In photos-only mode use one to five relevant photos; do not demand separate face/body/scene images when the supplied photo already covers the needed roles. The helper preserves the exact supplied order. Merge photographs of the same person into one `<Subject 1>` and explicitly state their contributions. A body photo's outfit does not silently replace the intended outfit.

Prepare missing scene anchors from the relevant source frame when appropriate and when an image tool is available. Preserve its full composition, wardrobe and objects while applying the requested appearance. Inspect the output. Keep original image resolution; never enlarge a tiny screenshot and claim that it is a native source frame. Scene anchors are appearance/composition evidence, not mandatory first/last frames or a timed storyboard. Remove genuinely unused sockets and renumber all prompt labels together.

If an image tool refuses an asset, save the exact submitted prompt, error/category/stage and affected filename. Report it. Do not silently change clothes, props or scene meaning, disguise a retry, substitute another tool to bypass the block, or mark the missing reference ready. Preserve successful and failed attempts separately.

## Audio and timing

Source-video mode uses one selected interval for images, controls and source audio. Speech requires timestamped words and on/off-screen speaker roles; ASR is not manual listening. Photos-only mode has no source audio to inspect or transcribe. Include user-requested dialogue if given; do not invent a source transcript. Both graphs retain native joint video/audio output. Do not silently replace generated audio with the original track in post-production.

Use 24 FPS and an exact `17k+5` frame count, normally 124–362. State seconds as frames / 24. A source clip, control maps and requested output must have matching frame counts and dimensions. Resolve a shorter available clip before sampling; do not silently duplicate frames, slow motion or truncate its ending. For photos only, length is a direct Ref2VA widget and has no video-count dependency.

Use the Resolution Selector: 9:16, 1 MP, multiple 32 for the recorded full setting (768×1376). A requested low-resolution check uses 0.2 MP (352×608 with this selector) and a separately shortened prompt/interval. Do not impose test renders when the user requests full renders directly. Do not split an otherwise valid full reel automatically.

## Export, verify, then assess the actual result

Use `scripts/configure_workflow.py` to make a fresh local package from actual inputs and a complete prompt. With `--source`, automatic selection is `control`; without it, automatic selection is `refs`. See the commands in the workflow guide. The script does not submit anything. It preserves native image bytes, assigns unique input paths, removes unused photo slots and emits UI/API JSON. Use a fresh output directory for every attempt.

Inspect the exported graph: correct photos/order, full prompt, exact length, output FPS, model selection and audio wiring. In `control`, verify DWPose keypoints → TS smoother → rendered pose → pose ControlNet, with depth on its own branch. In `refs`, verify there are no source-video, pose, depth, ControlNet or TS nodes and no hidden source-audio or frame-count links. A structural pass is not proof of GPU compatibility or visual quality.

When generation is authorized, use the user's selected ComfyUI environment and queue ready independent jobs together if requested. Save **every** generated attempt in that reel's `output` folder with a unique attempt identifier and preserve its prompt/workflow. Check the generated final video, not only ControlNet previews: frame count/FPS, visible likeness, clothing, props, limb count, motion continuity, camera path and ending. Inspect dense frames at critical moments; do not claim continuous playback or manual listening if unavailable. Report unavailable checks and material defects. Only add captions after the video is accepted.
