# Prompting for this handoff

Use one complete English prompt. This project variant uses these labels in order:

1. `subject_definitions:` — merge identity/body/scene images into consistent visible subjects; assign every connected Picture a role.
2. `summary:` — start with `[reference generation]` and state the overall action and viewpoint.
3. `retention_analysis:` — describe which subject attributes and scene geometry are retained. Markers are ordinary text guidance, not hard constraints.
4. `detailed_description:` — timed physical actions, facial acting and viewpoint motion. Keep body action and viewpoint action in distinct sentences. Preserve real beat density; a long time allocation may slow the event down.
5. End exactly with `non_diegetic_music:` followed by `N/A` on the next line.

This is the established project prompt variant, not a claim that every official H3 template has only five sections. Keep audio wiring and dependency notes outside the pasteable prompt. Omit `overall_soundscape` and general audio-reference prose in this variant. H3's supplied BasicGuider path has no negative-prompt socket; describe the desired visible state rather than relying on a negative list.

The model's Picture numbering follows the actual connected image slots. A source clip feeding ControlNet does not create `<Video 1>` inside Ref2VA. Do not cite a disconnected Picture or a nonexistent Video. Ordinary scene photos are not a sequence of forced frames. A detail close-up can change the framing even when text calls it “detail only”; prefer compatible full-frame references for a fixed viewpoint.

For source reconstruction, use measured cuts and action timings. For photos only, create a coherent timed action from the user's description; no source transcript, source motion or source pose is required. Keep identity, wardrobe, anatomy, objects and spatial relationships consistent. Make important motion explicit instead of replacing it with “small movements.” Preserve a genuinely static viewpoint or specify a bounded move and its endpoint.

For dialogue, `(S1)` is the first audible voice, including off-screen voices; subsequent new voices are `(S2)`, `(S3)`, etc. Use `<d>[English] Exact words.</d>` with the actual language and punctuation. Speaker IDs belong with speaking actions, not in `retention_analysis`. Source speech must be transcribed; desired original speech may come directly from the user's script. Music lyrics are not automatically dialogue. Run:

```powershell
python scripts/check_prompt_dialogue.py "prompt.txt"
```

## Complete photos-only example using one portrait

This example creates a new scene; it is not an instruction to change an existing source outfit. Adapt wardrobe and action to the actual user request.

```text
subject_definitions:
<Subject 1> is one adult person whose facial identity, hair and natural skin texture come from <Picture 1>. The person wears a plain navy jacket over a light-grey T-shirt.
<Subject 2> is a quiet sunlit room with a pale wall, a wooden desk and a closed book.

summary:
[reference generation] A continuous vertical medium shot shows <Subject 1> beside the desk in <Subject 2>, greeting the viewer with one natural hand wave and settling into a relaxed expression.

retention_analysis:
<Subject 1>: fully_preserved — retain the face and hair from <Picture 1>, one consistent outfit, natural skin detail and connected hand anatomy.
<Subject 2>: fully_preserved — retain the wall, desk, closed book and steady daylight throughout the shot.

detailed_description:
[Shot 1] 0.00–1.00 s: <Subject 1> stands beside the desk and turns their gaze toward the viewpoint with a small smile. The viewpoint is fixed at eye level, with stable framing and subject scale.
1.00–3.00 s: the person lifts their right forearm, opens the hand beside the shoulder, and waves it gently from side to side twice. The shoulder, elbow, wrist and fingers remain connected and move naturally.
3.00–4.20 s: the right hand lowers to the person's side while the smile relaxes.
4.20–5.167 s: the person remains comfortably still, blinks once and holds the same position. The viewpoint, background and lighting remain steady through the ending.

non_diegetic_music:
N/A
```

Configuration: Ref Only, one connected image, 124 frames / 24 FPS = 5.166667 seconds. Native audio is generated without a source-audio reference; this is not a promise of silent output or any exact sound.
