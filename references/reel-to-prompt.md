# Reel → prompt: rebuilding a reference clip in H3

Recreating a clip you like is normally guesswork — you watch it, remember roughly what happened, and invent beat timings. Since H3 reads beat duration literally as event speed, invented timings are the single biggest source of footage that feels floaty or rushed.

`tools/reel_shots.py` removes the guessing. It breaks the reference clip into shots, measures every cut, and writes frames you can actually look at.

**This is a script that gets run, not a validator that sits unused.** It runs once per reference clip, before writing anything, and it produces something no amount of careful reading could: measured cut times and frames from footage nobody has seen yet.

## Running it

```bash
python3 tools/reel_shots.py "https://www.instagram.com/reel/XXXX/" -o work/reel01
python3 tools/reel_shots.py /path/to/local.mp4 -o work/reel01
```

Requires `ffmpeg`, `ffprobe`, and `yt-dlp` for URLs. Output:

```
work/reel01/manifest.json   duration, fps, resolution, orientation, cut times,
                            per-shot start/end/duration, H3 length options
work/reel01/frames/         NNN_shotNN_head|mid|tail_TTT.TTTs.jpg
work/reel01/audio.wav       16 kHz mono, if the source had audio
```

Options: `--threshold` (default `0.30`) sets scene sensitivity — drop to `0.15` for soft or graded footage where cuts are subtle, raise to `0.40` for noisy or heavily-moving footage that produces false cuts. `--max-frames` caps extraction, keeping every shot head. `--no-audio` skips the wav.

Sanity-check the shot table it prints. If a five-second reel reports twenty shots, the threshold is too low and the detector is firing on camera movement; if a fast-cut edit reports one shot, it is too high.

## Turning the manifest into a prompt

**1. Read the frames.** Actually open them. The head frame of each shot establishes composition and subject placement; the tail frame shows where that shot ended up. The difference between head and tail *is* the beat.

**2. Map shots to beats, using the measured times.** A shot from 1.24 s to 2.05 s is a 0.81-second beat, so write it as one. Do not round to something comfortable — that is exactly how a fall becomes moon gravity.

**3. Pick `length` from `h3_length_options` — the value at or above the source duration, never below it.** The manifest brackets the source with valid `17k+5` frame counts. Take the one **≥** the duration being covered and trim the surplus in the editor; a 6.4-second reel becomes 158 frames (6.58 s), so every beat stretches by about 3 %. A 14.90-second take becomes 362 (15.08 s).

Rounding down is not a cheaper draft. **A reference video longer than the target is truncated to the target**, so a 14.90-second motion reference asked for at 124 frames contributes only its first 5.17 s — the rest of the choreography is absent, not compressed. The single-clip ceiling is 362 frames, 15.08 s.

**3b. Decide the shape from the cut count, before writing anything.**

- **No cuts, source ≤ 15.08 s** — one clip at the bracketing grid value.
- **No cuts, source > 15.08 s** — one render cannot hold it. Ask the user whether to split the take into consecutive segments of at most 15.08 s, or to keep one chosen 15-second section.
- **Cuts present** — ask whether they want one render per cut (the only option past 15.08 s total, and the better one for hard cuts) or a single full pass carrying the cuts internally (only when the whole source fits inside 15.08 s, and shaky past about two cuts).

When several clips cover segments of one source, **trim the reference video to each segment before wiring it**. Truncation keeps the head, so an untrimmed file makes clip 2 copy clip 1's motion.

**3c. Write the motion as a timeline, not a summary.** If the point is to reproduce the choreography, the description accounts for the whole running time in order, roughly one beat per one to two seconds, each naming what the hands, head and body do at that moment. `She makes a few quick adjustments` leaves fourteen seconds for the model to fill with movement of its own, and explicit text outweighs a video reference — so the summary wins and the copy fails.

**4. Decide the mode.**

| The reel is being used for | Mode |
|---|---|
| composition, motion, pacing — with *your* subject | Ref2VA |
| a single still you also want as frame 0 | I2VA |
| a move between two specific frames you have | FL2VA |

Recreating a reel with your own person is almost always **Ref2VA**: the reel supplies structure, your photos supply identity.

**5. Say which shots need reference photos.** Go through the shot table and mark where the subject is visible and at what angle — front, three-quarter, back, close-up, full-body. That list is the shopping list for reference stills, and it is the single most useful thing this workflow produces. A reel that shows the subject from behind needs a reference covering that; without one the model invents it, and that is where identity collapses.

## Identify before you describe — the zoom pass

A contact sheet is enough to read **pose and trajectory** and nothing else. At six panels
across an 1800-pixel strip each frame is roughly 300 px wide; at ten panels it is 180. That
resolves an arm position. It does not resolve what is in the hand, and a plausible guess is
exactly what gets rendered — a hair video makes "comb" plausible when the object is a
makeup pencil held up like a plumb line, and the whole meaning of the gesture goes with it.

**Before naming anything, crop it at native resolution and look at it.** One pass, in this
order:

1. **Every object the subject holds or touches.** Crop the hand region from the full-size
   frame at the moment the object is closest to camera.
2. **The action the object performs.** A pencil raised beside a brow is *measuring*, not
   *combing*. The function determines the whole gesture — describe it, not just the shape.
3. **Marks on the reference actor that must not transfer** — tattoos, jewellery, a watch, a
   hair tie. Each one needs an explicit exclusion in `retention_analysis`, and you cannot
   exclude what you never saw.
4. **The subject's own distinguishing details** in the identity photo, at full size.
5. **Burned-in text** anywhere in the frame — crop it off the strip rather than forbidding
   it in words.

```bash
# object in the hand, native pixels, upscaled for reading
ffmpeg -ss 8.60 -i src.mp4 -frames:v 1 -vf "crop=300:300:330:330,scale=600:600" zoom.png
```

**If you cannot identify it after zooming, say so and ask.** "A thin dark object in her
right hand, I cannot tell what it is" is a usable line in a report. A confident wrong noun
is not — it survives into `subject_definitions`, gets rendered as a real prop, and costs a
generation to find out.

## What transfers and what does not

**Transfers well.** Shot rhythm and cut timing. Framing and subject placement. Camera movement, once translated into the official vocabulary. Lighting direction and general palette. The overall energy of the edit.

**Transfers poorly or not at all.** The person — H3 gives recognisable likeness from your references, never the reel's actor. Exact background geography. Text on screen. Anything that depends on a specific real location. Fast, complex hand action.

**Does not transfer at all.** Frame content: sampling always starts from an empty latent, so nothing of the source survives into the output. This is a rebuild, not an edit.

**A caution about audio.** The wav is for you to listen to, so you can describe the soundscape accurately. It cannot be fed back as a reference that carries meaning — reference audio never reaches the text encoder, only its `<Audio j>` label does.

## Worked shape

For a 6.4-second reel that the tool reports as three shots — 0.00–2.02, 2.02–4.02, 4.02–6.40 — with the subject frontal in shot 1, in profile in shot 2, and walking away in shot 3:

```
Length: 158 frames (6.58 s), the nearest grid value above 6.40.

Reference photos needed:
  <Picture 1>  frontal, face clearly lit          — covers shot 1
  <Picture 2>  three-quarter                      — covers shot 2
  <Picture 3>  from behind, showing hair length   — covers shot 3

subject_definitions:
<Subject 1> is the <person> whose appearance comes from <Picture 1>, <Picture 2>
and <Picture 3> — <features> — in <wardrobe>.
<Subject 2> is the <location>: <what the frames show>.

summary:
[reference generation] <one sentence, from what the frames actually show>.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - ...
<Subject 2> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - ...

detailed_description:
<style, read off the frames — light, grain, palette, capture technique>
[Shot 1] <what the head frame shows>. <what changes by the tail frame>.
[Shot 2] At 00:02.020, the shot cuts to <new information>. <the beat>.
[Shot 3] At 00:04.020, the shot cuts to <new information>. <final state>.

overall_soundscape:
<from listening to audio.wav>

non_diegetic_music:
<from listening, or N/A>
```

Note the cut times in `[Shot 2]` and `[Shot 3]`: taken from the manifest, formatted `MM:SS.mmm`, strictly increasing. That is the whole point of measuring them.

If the reel is a single continuous take, do not invent cuts — write one shot and put the change into camera motion, exactly as the base guide prefers.

## When not to bother

If the reel is one static talking-head shot, the tool tells you nothing you could not see. It earns its keep on fast edits, on clips where the pacing is the appeal, and on anything longer than a few seconds where beat timing would otherwise be guessed.
