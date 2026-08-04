# Where each claim comes from

This repository mixes three very different kinds of statement, and they do not deserve equal trust. Everything below is tagged so you can tell them apart.

| Type | Meaning |
|---|---|
| **Official** | stated in MiniMax's own documentation |
| **Implementation** | read from the ComfyUI source; true of local inference, and can change when ComfyUI does |
| **Empirical** | observed across real renders; a tendency, not a guarantee |
| **Community** | reported in third-party write-ups, not verified against a primary source |

Primary sources:

- [`VIDEO_PROMPT_WRITING_GUIDE_base_en.md`](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md) — T2VA / I2VA / FL2VA / L2VA
- [`VIDEO_PROMPT_WRITING_GUIDE_ref_en.md`](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md) — full reference
- `comfy/text_encoders/minimax.py` and `comfy_extras/nodes_minimax_h3.py` in ComfyUI
- `Comfy-Org/workflow_templates` → `video_minimax_h3_r2v.json`

Implementation facts below were read on **2026-08-04** against ComfyUI `master`.

## Prompt format

| Claim | Type |
|---|---|
| Three fields for T2VA / I2VA / FL2VA / L2VA; six sections for full reference | Official |
| Exact alignment instruction strings per mode | Official |
| `[Shot 1]` carries no timestamp; later shots use increasing `At MM:SS.mmm` | Official |
| Camera vocabulary, amplitude and speed modifiers | Official |
| Style list (`Cinematic`, `live-action`, `2D-animated`, `3D CG`, `claymation`, `watercolor`, `vintage film`) | Official |
| `<Subject N>` carries identity; a standalone `<Picture N>` is only a frame anchor | Official |
| One `<Subject N>` may cite several assets, stating what each provides | Official |
| Doing so reduces reference competition in the rendered output | Empirical |
| `retention_analysis` markers and `summary` task types | Official |
| Speaker IDs, `<d>` tags, `<scenetrans>`, `<cutoff>`, voiceover phrasing | Official |
| `detailed_description` runs 350–500 words for generation tasks | Official |
| Prefer camera motion over a cut when only distance or angle changes | Official |

## ComfyUI implementation

| Claim | Type |
|---|---|
| No prompt rewriter — text is tokenized verbatim, not chat-templated | Implementation |
| ComfyUI injects `<Picture i>` / `<Video k>` / `<Audio j>` labels before the prompt | Implementation |
| Label order is fixed by category and numbered by slot index, not by wiring order | Implementation |
| A reference video's soundtrack takes `<Audio 1>` ahead of standalone audio | Implementation |
| The alignment instruction is **not** emitted for you | Implementation |
| Reference audio never reaches the text encoder | Implementation |
| Reference video reaches the encoder at 2 fps in 2-frame blocks | Implementation |
| Frame count snaps up to a `17k+5` grid | Implementation |
| Trained range roughly 124–362 frames | Implementation (node tooltip) |
| Sampling always starts from an empty latent — no frame of a source clip is preserved | Implementation |
| Reference video is truncated to the target length, then trimmed down to the `17k+5` grid | Implementation |
| Reference video is resized to a 768 short edge with a 768 × 1344 area cap | Implementation |
| Whether `[video editing]` behaves differently from `[reference generation]` locally | **Untested** |
| `ref_image_size` formulas; both downscale only | Implementation |
| `max` can be several times slower — reference tokens ride every step | Implementation (node tooltip) |
| Slot maxima: 9 images, 3 videos, 3 video soundtracks, 3 standalone audio | Implementation |
| `BasicGuider`, CFG 1, no negative socket | Implementation (template) |
| Template defaults: `res_multistep`, `simple`, 20 steps, 1344 × 768, length 124 | Implementation (template) |
| `MiniMaxH3SigmaShift` exists with `shift_video` 12.0, `shift_audio` 3.0 | Implementation |
| Model file names and sizes | Implementation (HF repo listing) |

## Empirical

Observed while building this, not measured under controlled conditions. Each is a tendency that held often enough to be worth encoding, not a law.

| Claim | Type |
|---|---|
| `she holds the camera` renders a physical camera | Empirical |
| The model rotates the subject instead of moving the camera unless parallax is described | Empirical |
| Camera behind + no body rotation + eye contact produces inverted heads and scrambled anatomy | Empirical |
| Beat duration is read literally as event speed; over-long beats render as slow motion | Empirical |
| Falls need intermediate poses and the ground in frame | Empirical |
| Counting fails and prohibitions raise the salience of what they forbid | Empirical |
| A reference video containing a person competes with a reference still on identity | Empirical, with an implementation explanation |
| Identity holds better with several reference photos covering different angles | Empirical |
| `beta` or `normal` scheduler may beat `simple` on reference-heavy graphs | Community, unverified here |
| 20 `res_multistep` steps ≈ 35–40 Euler steps | Rule of thumb, unmeasured on this model |
| 30 steps buy nothing visible over 20 | Unmeasured |
| H3 was not trained with guidance | **Unsupported** — inferred from the template using CFG 1 |

## Production heuristics

Not from MiniMax, not from the source — craft rules adopted because they held up in practice. Useful, but none of them is a law.

| Claim | Type |
|---|---|
| The event-duration table and ~2.7 spoken words per second | Empirical, general production knowledge |
| Frame defaults 124 / 158 / 192 / 209 / 243+ per shot type | Empirical |
| One primary camera move per shot | Empirical |
| An omitted `non_diegetic_music` field tends to produce unwanted music | Empirical |
| Objects absent from the references rarely materialise mid-shot | Empirical |
| Cropping heavily foreshortened hands reduces finger artifacts | Empirical |
| `ref_image_size: max` is never worse for identity | Inferred from the formulas; the slowdown is Implementation |
| A higher-precision encoder improves identity in Ref2VA | Inferred from the architecture, not measured |
| The ~170° neck-twist explanation for scrambled anatomy | Empirical interpretation of an observed artifact |
| Reference-video frames outweigh a portrait on identity | Empirical; the earlier "same channel" explanation was wrong and has been removed |

## Community, unverified

Widely repeated but not found in MiniMax's docs or the ComfyUI source. Treat as approximate.

| Claim | Type |
|---|---|
| Output up to 2K, short edge 1440 | Community |
| Prompt field holds 7000 characters | Community |
| 12 reference files total | Community — **contradicted** by the node schema |
| Reference video and audio 15 s combined | Community — no such cap in the execution path |
| Standalone audio is rejected without an image or video | Community — **contradicted**; the node accepts it unconditionally |
| Sage Attention roughly doubles speed | Community (ComfyUI docs) |
| Quantisation quality ordering `bf16` > `int8_convrot` > `pruned int8` | Inferred from method properties; no published benchmark for H3 |

## What is missing

No controlled A/B data exists here for: the scheduler comparison, the sigma-shift defaults, quality deltas between quants, whether 20 steps differ visibly from 30, whether `[video editing]` behaves differently from `[reference generation]` under local inference, or whether writing in MiniMax's documented format measurably beats plain prose given that ComfyUI runs no rewriter. Those would need fixed-seed paired renders. Until someone does that, none of them should be stated as measured.
