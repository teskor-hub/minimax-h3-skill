# Templates

Fill the angle-bracket slots. Keep section order and the exact instruction lines — they are fixed strings, not paraphrasable.

## T2VA — text only

```
integrated_multimodal_description: [Shot 1] <STYLE: Live-action, cinematic / 2D-animated / vintage film>, <opening framing> frames <SUBJECT> in <ENVIRONMENT>. The camera <MOVE> <with small/large amplitude> <at slow/fast speed> as <ACTION>. <REACTION or state change>. [Shot 2] At 00:0X.000, the camera cuts to <NEW INFORMATION — subject, space, state, viewpoint or time>.

overall_soundscape: <ambience>. <physical action sounds tied to what happens>.

non_diegetic_music: <instrumentation, tempo, rhythm, dynamic development> — or N/A.
```

## I2VA — animate this exact photo

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] <STYLE>, the <SUBJECT> shown in <Picture 1> remains <position and framing>, preserving <appearance, clothing, key objects, spatial relationships>. The camera <MOVE> <amplitude> <speed> as <FIRST CHANGE>. <CONTINUOUS DEVELOPMENT>. <RESULT OR REACTION>.

overall_soundscape: <ambience>. <action sounds>.

non_diegetic_music: <...> — or N/A.
```

Do not re-describe what is already visible in the picture beyond naming the anchors that must not drift. Describe what **changes**.

## FL2VA — first and last frame

```
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the <S.SS>-second mark of the target video.

integrated_multimodal_description: [Shot 1] <STYLE>, <SUBJECT> begins in the position and framing established by Picture 1, <opening state>. The camera <MOVE> <amplitude> <speed> as <INTERMEDIATE CHANGE 1>, <INTERMEDIATE CHANGE 2>, and <NARROWING DIFFERENCE>. <SUBJECT> settles into the pose, spacing, and composition established by Picture 2 at the end of the shot.

overall_soundscape: <...>

non_diegetic_music: <...> — or N/A.
```

Single shot unless multiple are explicitly required. Both frames must share aspect ratio, resolution, colour grade, grain and image quality — a cleaner end frame turns the clip into a beautification morph, far more visible than the intended motion.

## L2VA — land on a final frame

```
How the reference pictures align with the target video — <Picture 1> (from [Shot 1]) aligns with the <S.SS>-second mark of the target video.

integrated_multimodal_description: [Shot 1] <STYLE>, <opening framing> begins with <PLAUSIBLE EARLIER STATE compatible with the final image>. The camera <MOVE> <amplitude> <speed> as <TRANSITION PATH>. Toward the end, <ELEMENTS> settle into the exact <arrangement, position, camera angle, lighting, and final composition> established by <Picture 1>.

overall_soundscape: <...>

non_diegetic_music: <...> — or N/A.
```

## Full-reference (R2V)

```
subject_definitions:
<Subject 1> is the <PERSON> whose appearance comes from <Picture 1> — <face, hair, distinguishing marks, wardrobe> — and whose <motion / pose / action> comes from <Video 1>.
<Subject 2> is the <ENVIRONMENT> from <Picture 1>: <walls, light sources, furniture, floor>.
<Video 1> is the <camera-movement and pacing> reference for the target video.

summary:
[reference generation] The target video shows <Subject 1> in <Subject 2>, <one-sentence action>, following the <camera movement and pacing> of <Video 1>.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - <the listed identity features> are retained.
<Subject 2> (appears in [Shot 1]): fully_preserved - <the listed environment features> are retained.
<Video 1> (camera movement and pacing): weak_reference - only the travelling path and handheld rhythm are followed; none of its people, wardrobe, location or lighting appear.

detailed_description:
The target video is <one or two sentences of style, palette, lighting, grain>.
[Shot 1] <Subject 1>, <referenced characteristics as visible here>, <position in frame>, <current action>. The camera <MOVE> <amplitude> <speed> as <what changes>. <Continued action, state changes, what enters or leaves frame>. <Final held state>.

overall_soundscape:
<ambience>. <physical action sounds>.

non_diegetic_music:
N/A
```

Reminders that decide whether this works at all: identity goes in `<Subject N>`, never a standalone `<Picture N>`. Anything reused as visible content from a video is a subject, not a `<Video N>`. Scope a reference's role in `retention_analysis` rather than forbidding things in the body.

---

## Worked example — overhead selfie-style shot

Brief: a photo of a woman, tight frontal close-up; the target is the viewpoint rising above her head and looking down while she reaches toward it and holds eye contact.

Full-reference, because the target framing does not exist in the source photo and forcing a 180° rotation through I2VA collapses the face.

```
subject_definitions:
<Subject 1> is the young woman whose appearance comes from <Picture 1>: a messy black
shag haircut with wispy curtain bangs, freckled cheeks, a small cross tattoo under her
right eye, a striped heart tattoo on her neck, a grey ribbed tank top and a thin chain
with a red pendant. Her hair length and silhouette from behind come from <Picture 2>.
<Subject 2> is the bedroom from <Picture 1>: cream walls, an amber table lamp on a
dresser, carpet, warm low light.

summary:
[reference generation] The target video shows <Subject 1> standing in <Subject 2>,
raising both arms toward the lens as the camera cranes above her and looks down.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - her face, freckles, both tattoos,
hair and wardrobe are retained.
<Subject 2> (appears in [Shot 1]): fully_preserved - the walls, lamp and carpet are retained.

detailed_description:
The target video is a warm, dim handheld phone video at night, softly grained, with
shallow depth of field and natural low-light colour.
[Shot 1] <Subject 1> stands at eye level facing the lens, the amber table lamp glowing
behind her right shoulder. She lifts both arms up and forward toward the viewer, elbows
opening wide, her hands passing just outside the top corners of the frame. The camera
pedestals up with large amplitude at slow speed and tilts down into a steep high angle;
the ceiling leaves the frame and the carpet appears behind her instead. Her bare
shoulders and the top of her back fill the lower frame, her black hair falling forward
around her face, her forearms angled upward at the left and right edges. She tilts her
head back, chin lifted, and holds eye contact with the lens as the lamp light rakes
across her cheek. The move settles and holds; she blinks once, slowly, with the faintest
smile.

overall_soundscape:
Quiet indoor room tone continues throughout, with the soft rustle of fabric as her arms
lift and one calm breath near the end.

non_diegetic_music:
N/A
```

What the structure is doing:

- **No device anywhere.** The viewpoint is what she reaches for, so it is off-frame by definition. Nothing to render wrong, and it sidesteps the failure where a raised hand comes up empty because the phone was never in the reference.
- **`hands passing just outside the top corners`** keeps the hands cropped. Hands reaching toward the lens are heavily foreshortened and are where extra fingers appear.
- **`pedestals up … and tilts down`** — official camera vocabulary with amplitude and speed, in one sentence, as an action. Written as a possession verb (`she raises the camera`) it would resolve into a prop instead.
- **`<Picture 2>` cited inside the subject, not as its own entry**, because it only supplies hair silhouette — it is not a frame anchor.

### If likeness breaks at extreme angles

A near-vertical overhead is the hardest case: the face foreshortens severely, chin near, forehead far. Back off to a steep-but-not-vertical angle — roughly 70° — and the composition barely changes while the face becomes recoverable.
