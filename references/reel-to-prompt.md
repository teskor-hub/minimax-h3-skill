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

**3. Pick `length` from `h3_length_options`.** The manifest brackets the source duration with valid `17k+5` frame counts. Take the nearest one and adjust your beats to fit it; a 6.4-second reel becomes 158 frames (6.58 s), so every beat stretches by about 3 %.

**4. Decide the mode.**

| The reel is being used for | Mode |
|---|---|
| composition, motion, pacing — with *your* subject | Ref2VA |
| a single still you also want as frame 0 | I2VA |
| a move between two specific frames you have | FL2VA |

Recreating a reel with your own person is almost always **Ref2VA**: the reel supplies structure, your photos supply identity.

**5. Say which shots need reference photos.** Go through the shot table and mark where the subject is visible and at what angle — front, three-quarter, back, close-up, full-body. That list is the shopping list for reference stills, and it is the single most useful thing this workflow produces. A reel that shows the subject from behind needs a reference covering that; without one the model invents it, and that is where identity collapses.

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
