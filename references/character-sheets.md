# Character reference sheets

A character sheet — a grid of studio views of one person on a neutral background, typically front, profile, back, three-quarter, face close-ups, an eye or tattoo macro and hands — is the most efficient identity asset available in Ref2VA. It is also the one most often attached wrongly.

## Why it works

Identity collapses where the shot reveals an angle the references never covered: the model invents the missing geometry, and invention is where likeness goes. A sheet closes that gap in a single slot. The neutral backdrop carries no location to bleed, the views are internally consistent, and macro panels pin the details a portrait cannot — a tattoo's exact placement, iris colour, freckle density, nail shape.

## The cost: resolution per panel

The sheet is resized as **one image**. At `ref_image_size: max` the short edge goes to 2048 px, so a 3 × 3 grid gives roughly **680 px per panel** — about a third the linear detail of a dedicated still at the same setting. At `match` it is worse.

So the sheet buys coverage, not fidelity. For a shot that holds on the face, attach a full-resolution face still **as well**. Nine image slots exist; a sheet plus two or three targeted stills is a better use of them than either alone.

## Assigning its role so wardrobe and backdrop do not transfer

The clothing in a sheet is usually a neutral bodysuit that has nothing to do with the target video, and the grey seamless is never wanted. Do not forbid them. **Never give the sheet that role in the first place**, using the official multi-asset merge:

```
<Subject 1> is the woman whose face, freckles, the small black cross tattoo beneath her
left eye, eye colour, hair length and layering, body proportions and hand shape all come
from <Picture 1> — a nine-panel studio character reference sheet on a plain grey
background — and whose clothing comes from <Picture 2>.
```

When there is no wardrobe reference, end it `…and whose clothing is described below`, then describe the outfit in `detailed_description`.

### Use `fully_preserved`, not `partially_preserved`

The marker states fidelity **within the role already defined for that label**. If the sheet's role is appearance and proportions, and those are kept, that is `fully_preserved` — the wardrobe was never part of the role, so its absence is not a loss. `partially_preserved` would claim some of the defined characteristics failed to hold. Attach the clarification to the marker rather than writing a ban:

```
<Subject 1> (appears in [Shot 1]): fully_preserved - her face, freckles, cross tattoo,
eye colour, hair and body proportions from <Picture 1> are retained; the neutral
bodysuit and grey studio backdrop of that sheet are not part of her defined role and do
not appear in the target video.
```

## Call it a sheet, not a photo

Name the asset for what it is — *a studio character reference sheet on a plain background* — inside the subject definition. A sheet is a recognisable format, and saying so is real information about the asset: it tells the model this is a set of views, not a scene to reproduce.

Per the guide, an image that only defines a character gets no standalone `<Picture N>` entry; cite it inside the `<Subject N>` definition, which is exactly where this description belongs.

## The grid-render risk

The sheet's own visual structure — framed panels, white gutters, seamless backdrop, repeated figure — can leak, producing a collage, a studio background, or a duplicated subject. Two mitigations, both structural:

1. **Describe the target scene concretely** in `detailed_description` — environment, light, surfaces, what is behind and beside her. A vague scene leaves room for the backdrop to win; a specific one does not.
2. **Define the environment as its own `<Subject N>`** with its own source, so the location has a positive owner rather than being merely absent.

If a grey seamless still shows up, the fix is more concrete scene description, not `no studio background`.

## Template

```
subject_definitions:
<Subject 1> is the woman whose face, freckles, <distinguishing marks>, eye colour, hair
length and layering, body proportions and hand shape come from <Picture 1> — a studio
character reference sheet on a plain background — and whose clothing comes from
<Picture 2>.
<Subject 2> is the <location>: <surfaces, light sources, what is behind and beside her>.

summary:
[reference generation] <one sentence>.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - her face, freckles, <marks>, hair
and body proportions from <Picture 1> are retained, with clothing from <Picture 2>; the
neutral wardrobe and plain backdrop of the sheet are not part of her defined role and do
not appear.
<Subject 2> (appears in [Shot 1]): fully_preserved - <listed features> are retained.

detailed_description:
<style>
[Shot 1] <concrete scene, so the sheet's backdrop has nothing to win against>
```

## When a sheet is not worth it

If the shot never shows the subject clearly — a wide, a silhouette, a back view at distance — the extra angles buy nothing and the per-panel resolution loss is pure cost. A single still is better. The sheet earns its slot when the camera moves around the subject, when several angles appear in one clip, or when a distinguishing mark must land exactly.
