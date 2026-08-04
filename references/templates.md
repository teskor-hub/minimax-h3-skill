# Copy-paste templates

Fill the angle-bracket slots. Keep the block order. Delete blocks that do not apply — do not reorder them.

## R2V — reference to video

```
<Picture 1> locks <SUBJECT: face, distinguishing marks, hair, wardrobe>.
Keep these exactly as in <Picture 1>.
<Picture 2> fixes <SECOND AXIS: silhouette from behind / wardrobe / location>.

Scene: <ENVIRONMENT, time of day, light source, palette>.

[0.0-<t1>s] <opening framing>. <action that changes something>.
[<t1>-<t2>s] <camera move stated as a move>. <what enters or leaves frame>.
[<t2>-<t3>s] <second action>. <where the subject's eyes go>.
[<t3>-<end>s] <the move settles>. <final held state>.

Camera: <one primary move>, <handheld / locked off>, one continuous take, no cuts, no zoom.

Audio: <room tone>, <diegetic effect tied to the action> at <time>, <no music / music description>.

Keep identical: <identity anchors>. Never: on-screen text, watermarks, subtitle bars.
```

## I2V — animate this exact photo

No `Roles` block: the image is frame 0, not a reference. Do not re-describe what is already visible in it — that competes with the conditioning and causes warping. Describe only what **changes**.

```
Scene continues from the input frame.

[0.0-<t1>s] <first change — a movement, not a description>.
[<t1>-<t2>s] <camera move>. <what comes into frame>.
[<t2>-<end>s] <settling action>, <final held state>.

Camera: <one move>, <texture>, one continuous take, no cuts.

Audio: <room tone>, <effect> at <time>, no music.

Keep: <geometry / lighting / composition that must not drift>. No redesign of <the thing>.
```

## FLF2V — first and last frame given

Both endpoints are locked, so the prompt only describes the middle. Keep it short — over-specifying fights the endpoints.

```
<SUBJECT ACTION between the two frames> while the shot <CAMERA MOVE>.
One smooth continuous move, <handheld / steady>, natural micro-wobble, no cuts.
<Where the eyes stay throughout>.

Audio: <room tone>, <effect>, no music.
```

Both frames must share aspect ratio, resolution, colour grade, grain and image quality. A cleaner, more retouched end frame turns the clip into a beautification morph — far more visible than the intended motion.

## T2V — text only

```
<SUBJECT> in <ENVIRONMENT>, <time of day, light>.

[0.0-<t1>s] <action>.
[<t1>-<t2>s] <camera move>, <action>.
[<t2>-<end>s] <ending state>.

Camera: <move>, <texture>, <cuts or continuous>.

Look: <capture technique, grain, palette>.

Audio: <track description with timing>.

Never: <bans>.
```

---

## Worked example — overhead selfie-style shot

The brief: a photo of a woman, tight frontal close-up; the target shot is the viewpoint rising above her head and looking down while she reaches up toward it and holds eye contact.

This is an R2V job — the target framing does not exist in the source photo, and forcing a 180° rotation through I2V collapses the face.

```
<Picture 1> locks her face, freckles, the small cross tattoo under her right eye,
the striped heart tattoo on her neck, the messy black shag haircut with curtain
bangs, and the grey ribbed tank top. Keep all of it exactly as in <Picture 1>.
<Picture 2> fixes her hair length and silhouette seen from behind.

Scene: a warm dim bedroom at night, cream walls, an amber table lamp glowing
behind her, soft film grain, natural low-light colour, shallow depth of field.

[0.0-1.0s] Eye level, close. She looks into the lens, then lifts both arms up and
forward toward the viewer, elbows opening wide, her hands passing just outside the
top corners of the frame.
[1.0-2.8s] The shot cranes up above her head and tilts down into a steep high angle.
Her bare shoulders and the top of her back fill the frame, hair falling forward
around her face, her forearms angled upward at the left and right edges.
[2.8-4.4s] She tilts her head back, chin lifted, eyes up into the lens. The shot
drifts in a slow arc above her, lamp light sweeping across her face.
[4.4-5.0s] The motion settles and holds. One slow blink, the faintest smile.

Camera: handheld, crane up, tilt down to high angle, slow arc above her,
one continuous take, natural micro-wobble, no cuts, no zoom.

Audio: quiet room tone, soft rustle of fabric as she lifts her arms, one calm
breath near 4s, no music.

Keep identical: her face proportions, freckles, both tattoos, hair length.
Never: on-screen text, watermarks, subtitle bars.
```

What the structure is doing:

- **No device anywhere.** The viewpoint is the thing she is reaching for, so it is off-frame by definition. Nothing for the model to render wrong, and it sidesteps the failure where a raised hand comes up empty because the phone was never in the reference.
- **`hands passing just outside the top corners`** keeps the hands cropped. Hands reaching toward the lens are heavily foreshortened and are where extra fingers appear; cropping them removes the opportunity.
- **Camera motion and body motion in separate sentences.** Joined by a possession verb they resolve into a prop.
- **`<Picture 2>` for the back silhouette**, because the source close-up shows nothing below the collarbone and the model would otherwise invent the hair and build that end up filling most of the frame.

### FLF2V alternative

If preserving the exact room, grain and light of the source photo matters more than framing freedom, generate the end frame separately with an image editor, then run FLF2V with the photo as `start_image` and the generated frame as `end_image`. When editing the end frame, the critical instruction is *not* the pose — it is forbidding retouching, so both frames are equally imperfect:

```
Same person, same room, same camera — another frame from the same clip, filmed
two seconds later. Not a new photo.

Change only the pose and the camera angle: <TARGET FRAMING>.

Keep identical: <identity anchors>. Keep identical: the same colour grade, the
same low-light noise and softness, the same slightly amateur phone-camera look.

Do not retouch. Do not smooth the skin, do not remove freckles, do not redraw the
tattoos, do not brighten the room, do not make it look professional or studio-lit.
Keep the same imperfect image quality as the original.

Output in the same aspect ratio and resolution as the input photo.
```

A steep overhead angle is the hardest case for identity — the face is severely foreshortened, chin near, forehead far. If likeness breaks, back off to `a steep high angle from above, about 70 degrees, not fully vertical`: nearly the same composition, far more recoverable face.
