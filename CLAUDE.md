# MiniMax H3 skill — working notes

## What this is

A **Claude Code skill** (plus a **portable chat prompt**) that teaches prompt-writing
and ComfyUI setup for **MiniMax H3** — an open-weight, omni-modal video model that
generates video *and* native stereo audio in one forward pass, at 24 fps, over a trained
clip length of ~124–362 frames. It ships as two separate checkpoints, `fl2va`
(frame-conditioned) and `ref2va` (reference-conditioned). The skill is built on MiniMax's
own prompt-writing guides, plus the failure modes those guides don't cover.

This repo is documentation. There is nothing to build, run, or test — the "product" is the
prose in `SKILL.md`, `references/`, and `portable-prompt.md`, and the one script in `tools/`.

## Where things live

- **Source of truth:** this repo, `/workspaces/usual/minimax-h3-skill` — git, remote
  `teskor-hub/minimax-h3-skill`, branch `main`.
- **Installed copy:** `/root/.claude/skills/minimax-h3` — what Claude Code actually loads.
  Currently byte-identical to this repo. **After editing `SKILL.md`, `references/`, or
  `tools/`, re-sync the installed copy** (git pull / re-clone / copy) or the running skill
  is stale.
- This session's cwd `/workspaces/h3 minimax` is an empty scratch dir, not the project.

## Two deliverables, kept in sync

The same knowledge ships in two shapes:

1. `SKILL.md` + `references/*.md` + `tools/` — the Claude Code skill (references are
   lazy-loaded only when needed).
2. `portable-prompt.md` — one self-contained block pasted into any chat model (ChatGPT,
   Grok, Gemini). Same knowledge **minus the ComfyUI half**, because a chat model can't
   lazily load `references/`.

**Rule: any factual change to one must be propagated to the other, and to `SOURCES.md`.**
The git log is full of "propagate corrections to every copy" and "close the last copy
divergences" passes — drift between the skill and the portable prompt is the recurring bug
here. When you change a claim, grep both surfaces for it.

## Provenance discipline — the core working rule

`SOURCES.md` tags every claim as **Official** (MiniMax docs) / **Implementation** (read from
ComfyUI source) / **Empirical** (observed tendency) / **Community** (third-party, unverified).

- Never state Empirical or Community claims as documented fact. Say which kind you're
  leaning on when it affects a decision.
- When you add or alter a claim in any model-facing file, **add or update its `SOURCES.md`
  row**. If a statement isn't traceable to a row, that's a gap worth flagging.
- Implementation facts were read against ComfyUI `master` on **2026-08-04**
  (`comfy/text_encoders/minimax.py`, `comfy_extras/nodes_minimax_h3.py`,
  `video_minimax_h3_r2v.json`). Re-verify against current source before trusting them —
  they change when ComfyUI does.
- Several widely-repeated figures are **community, not primary**: the 2K/1440 output cap,
  the 7000-char prompt field, the "12-file limit", "standalone audio is rejected". The last
  two are contradicted by the node schema. Don't present any of them as documented.

## Domain invariants — don't let an edit break these

Load-bearing facts the whole skill rests on; see `SKILL.md` for the full treatment.

- **`fl2va` and `ref2va` are separate weights, not modes of one model.** Mode → checkpoint
  table is `SKILL.md` §1. `fl2va` powers T2VA/I2VA/FL2VA/L2VA; `ref2va` powers Ref2VA.
- **There is no negative prompt** — the template uses `BasicGuider`, CFG ≈ 1, no negative
  socket. Rewrite every ban as a positive statement of the desired state.
- **There is no video-to-video.** Sampling starts from an empty latent; no source frame
  survives → no frame-preserving character swap. But "a new video in which the subject
  *resembles* my photo and *moves like* this clip" **is** `reference generation`, and works.
  Keep that distinction — users who say "swap" usually mean the second one.
- **Identity lives in `<Subject N>`, never a standalone `<Picture N>`.** `<Picture N>` is
  only a concrete frame anchor. Merge multiple assets into one subject to resolve reference
  conflicts.
- **Frame count snaps *up* to the `17k+5` grid** (124, 141, 158, … 362), silently. Not
  multiples of 4.
- **Duration is read literally as event speed.** An over-long beat renders as slow motion,
  not as headroom. Budget real-world beat durations.
- **Never write `camera` as a noun the subject interacts with** — `she holds the camera`
  renders a physical camera. Use the official move vocabulary; keep body and camera in
  separate sentences; use `POV` when the device *is* the viewpoint.
- **Structure beats instruction**, the model can't count, and bans amplify what they ban.
- **Terminology:** use `T2VA / I2VA / FL2VA / L2VA / Ref2VA` for modes; use `fl2va` /
  `ref2va` only for checkpoint files. Recognise the aliases (T2V/I2V/FLF2V/R2V) but don't
  emit them.

## File map

| File | Audience | Contents |
|---|---|---|
| `SKILL.md` | Claude Code | core: mode selection, output formats, labels, camera, hard rules |
| `references/prompting.md` | Claude Code | official T2VA/I2VA/FL2VA/L2VA format + length method |
| `references/reference-mode.md` | Claude Code | official six-section Ref2VA format |
| `references/templates.md` | Claude Code | fill-in templates + worked examples |
| `references/comfyui.md` | Claude Code | checkpoints, quants, VRAM tiers, node settings, wiring |
| `references/troubleshooting.md` | Claude Code | symptom → cause → fix |
| `references/reel-to-prompt.md` | Claude Code | rebuilding a reference clip into a prompt |
| `portable-prompt.md` | any chat model | all of the above except ComfyUI, in one block |
| `SOURCES.md` | maintainers | provenance ledger for every claim |
| `tools/reel_shots.py` | run manually | shot detection + frame/length extraction |

## The tool

`tools/reel_shots.py` turns a reference clip into measured cut times and frames, so beats
aren't guessed. Needs `ffmpeg` + `ffprobe` (and `yt-dlp` for URLs).

```bash
python3 tools/reel_shots.py <url-or-file> -o work/reel01     # --threshold 0.30, --no-audio
```

Writes `manifest.json` (measured cuts, per-shot start/end/duration, `h3_length_options`),
`frames/` (head/mid/tail per shot), and `audio.wav`. **Run it before writing a rebuild
prompt**, then read the frames — don't describe the clip from memory.

## Voice and editing conventions

- Terse, honest, evidence-aware. State which kind of claim (Official/Impl/Empirical/
  Community) you're relying on when it matters.
- Prefer *correcting* a claim over piling on hedges; **remove** claims found to be wrong —
  the git history does exactly this ("Correct claims the ComfyUI source contradicts").
- Don't duplicate content beyond what the two-deliverable split forces. One `SOURCES.md`
  row covers a rule and all the places it's restated.
- When the skill produces a prompt for a user, it emits the **complete** prompt in one code
  block every time, never a fragment or a diff.

## Hard constraint (from `~/.claude/CLAUDE.md`)

Do **not** build any mass/batch/parallel automation of Claude calls (API, SDK, or many
chat sessions) — e.g. a pipeline that fans out hundreds of H3 prompt generations. Single
interactive prompt-writing is fine; a batch generator is not. If asked, stop, name the rule,
and offer a manual/one-at-a-time alternative.
