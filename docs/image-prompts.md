# Image-model reference prompts

Prompts handed to the owner for manual image generation (see docs/DECISIONS.md, "Image-generation models as an occasional reference channel"). Returned images are reference only and go in `docs/reference/`.

## Batch 1 — 2026-10-26, after choosing the hybrid tone-field grammar

Context for all three: the puzzle artwork is a three-tone mosaic (dark indigo, olive/ochre mid-tone, cream light) made of small stochastic dabs and chips with no outlines, no gradients, no lighting; subjects are bold flat silhouettes whose edges are ragged, torn-paper-like; the same three tones and chip colours appear in every picture.

1. "A sitting cat in profile as a bold flat silhouette, dark indigo on a cream ground, with a band of olive-green earth below. The whole image is built from small irregular paint dabs and mosaic chips in only three tones (indigo, olive, cream) plus sparse rust and pale-blue chips; edges of the silhouette are ragged like torn paper; no outlines, no shading, no gradients; folk-art mosaic poster, flat, high contrast."

2. "A small sailing boat on the sea as a bold flat silhouette: dark indigo hull, olive-green triangular sail, olive sea band, cream sky with sparse pale-blue chips. The whole image is built from small irregular paint dabs and mosaic chips in only three tones (indigo, olive, cream); ragged torn-paper edges; no outlines, no shading, no gradients; folk-art mosaic poster, flat, high contrast."

3. "A single round-crowned tree as a bold flat silhouette: dark indigo canopy and trunk, olive ground band, cream sky. The whole image is built from small irregular paint dabs and mosaic chips in only three tones (indigo, olive, cream) plus sparse rust and pale-blue chips; ragged torn-paper edges; no outlines, no shading, no gradients; folk-art mosaic poster, flat, high contrast."

What we hope to learn: how an illustrator-quality version of this grammar handles silhouette edges, chip scale and the mid-tone band, and whether three such images read as a set.

## Batch 2 — 2026-10-27, after choosing the subject set "Field, Wood and Water"

Context: the three pictures are a hare at dawn, an owl at dusk and a swan at midnight, drawn as flat three-tone mosaics (dark indigo, olive, cream, plus dark leaf chips scattered on cream for foliage, and olive water with cream wave lenses). The sky darkens from picture to picture (light → mid → dark), so each tone plays a different role in each picture: the hare is dark on a light sky, the owl is mid on a mid sky against a light moon, the swan is light on a dark sky over mid water. Same ragged torn-paper edges and no outlines, shading or gradients.

1. "A hare standing upright at dawn, bold flat silhouette in dark indigo on a cream sky, olive meadow below with a few dark leaf chips as grass tufts; built from small irregular paint dabs and mosaic chips in three tones (indigo, olive, cream) with sparse rust and pale-blue chips; ragged torn-paper edges; no outlines, no shading, no gradients; folk-art mosaic poster."

2. "An owl perched on a branch at dusk in front of a large pale moon, flat silhouette in olive on an olive-grey sky, the moon in cream, the branch and a few scattered leaves in dark indigo; same three-tone mosaic of small dabs and chips, ragged torn-paper edges, no outlines, no shading, no gradients; folk-art mosaic poster."

3. "A swan at midnight, bold flat silhouette in cream on a dark indigo sky, gliding on olive water with cream wave lenses, a cream crescent moon and a few cream star chips; same three-tone mosaic of small dabs and chips, ragged torn-paper edges, no outlines, no shading, no gradients; folk-art mosaic poster."

What we hope to learn: how an illustrator would pose each animal so it reads at about 27 cells wide, how the moon and water can carry the mid-tone picture, and whether the three read as a set.
