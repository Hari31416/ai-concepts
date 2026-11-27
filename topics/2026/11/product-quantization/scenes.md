# Product Quantization Animation Plan

## Overview

- **Topic:** Product quantization (PQ) for vector search.
- **Hook:** A billion 128-dim vectors take 512 GB. How can 8 bytes per vector be enough to find nearest neighbors?
- **Audience:** Engineers who know what an embedding and a distance are. No prior ANN knowledge.
- **Structure:** 5 scenes plus a consolidated `ProductQuantization` scene in `animation.py` (about 114 s with captions).
- **Data:** All numbers come from `toy.py` (seed 7, D=6, M=3, K=4, 400 synthetic vectors). The 2-D scatter plots are real k-means output on that data.
- **Entity colors:** the three subspaces keep `ENTITY_A/B/C` in every scene. ACCENT marks the stored code and active step; SUCCESS/ERROR mark outcomes only.

## Narrative arc

Show the memory wall, then the one idea that fixes it: cut a vector into pieces and replace each piece with the ID of its nearest centroid. Explain why this is powerful (codebooks multiply), then answer the doubt "but how do we search?" with a per-query lookup table that turns each distance into a few additions. End with the trade: 64x smaller, cheaper distances, approximate results.

## Scenes

| #   | Class                | ~Time | Learning goal                                                                                                                                                                                              |
| --- | -------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `MemoryWallScene`    | 16 s  | 512 B x 1B = 512 GB; 8 B x 1B = 8 GB. Question: can we still measure distance?                                                                                                                             |
| 2   | `SplitAndSnapScene`  | 20 s  | Split x into 3 pairs; each pair becomes a point in its own 2-D subspace and snaps to the nearest of 4 centroids; stored code `[0, 0, 3]`; decoding gives x-hat.                                            |
| 3   | `CodebookPowerScene` | 22 s  | 3 x 4 = 12 stored centroids describe 4 x 4 x 4 = 64 vectors; real setting 8 x 256 = 2,048 stored vs 256^8 reachable.                                                                                       |
| 4   | `LookupTableScene`   | 26 s  | Query stays exact. Build the 3 x 4 table of subvector-to-centroid distances once. A stored code's distance = sum of 3 lookups (`0.44 + 0.15 + 2.33 = 2.92`). Exact is 2.50; the gap is quantization error. |
| 5   | `PQTakeawayScene`    | 9 s   | 64x memory, 8 lookups vs 128 multiplies, approximate so rerank. PQ shrinks vectors; IVF and HNSW pick which to visit.                                                                                      |

## Caption beats

Captions carry the narration (no voice-over). Each scene writes its own `.srt`; the consolidated `ProductQuantization` scene shares one track (about 114 s, 27 cues). Each beat shows first, then the animation plays, then it holds for reading time.

1. **Memory wall:** A billion vectors need 512 GB. Can we shrink that? / Multiply by a billion vectors and RAM runs out. / Every search would also have to scan all of it. / Product quantization keeps each vector in 8 bytes. / 64× smaller. But can distances survive the squeeze?
2. **Split and snap:** Idea: cut the vector into pieces, then compress each. / Each piece gets its own small codebook of 4 centroids. / Every piece is a point in its own 2-D space. / Snap each point to its nearest centroid, keep the ID. / Stored code [0, 0, 3]: 6 bits instead of 192. / Decoding joins the centroids into an approximate vector.
3. **Codebook power:** Why split? Because codebooks multiply. / Pick one centroid per piece: that names one vector. / Store 12 centroids, describe 4 × 4 × 4 = 64 vectors. / At scale, 2,048 centroids name 18 quintillion vectors. / Storage adds up while the possibilities multiply.
4. **Lookup table:** The query stays exact. Only the database is compressed. / Measure the query's distance to every centroid, once. / That is 12 numbers per query, reused for every vector. / A stored code just looks up its three entries. / Add the three lookups: that is the approximate distance. / Repeat for every code. The smallest sum is the nearest. / The gap from the exact answer is quantization error. / Real PQ: 8 lookups per vector instead of 128 multiplies.
5. **Takeaway:** The trade: 64× less memory, much cheaper distances. / The price is accuracy, so rerank a shortlist exactly. / PQ shrinks vectors. IVF and HNSW choose which to visit.

Layout: diagrams stay above `CONTENT_BOTTOM` (-2.3) so the caption pill at `CAPTION_Y` never covers them. The old step subtitles and bottom banners were removed because the captions say the same thing.

## Key checks (verified in `toy.py` and `tests/test_product_quantization.py`)

- ADC distance equals the exact distance to the reconstruction x-hat.
- Worked example values: table entries `0.44`, `0.15`, `2.33`; ADC `2.93` (shown as `2.92` because the displayed 2-decimal entries are summed); exact `2.50`.
- Real-setting arithmetic: 512 B to 8 B, 64x, 512 GB to 8 GB, 2,048 stored centroids, 128 KiB codebook.

## Not in scope (possible follow-ups)

Symmetric distance, OPQ rotation, IVF-PQ combination, a vertical Short, captions/audio (see the `youtube-publish` skill).
