# Product Quantization (PQ)

## The problem

Vector databases store one embedding per item. A 128-dim `float32` vector is
128 × 4 = **512 bytes**. A billion of them is **512 GB**: too big for RAM on one
machine, and every search would stream all of it from memory or disk.

PQ compresses each vector to a few bytes (typically 8–64) and, crucially, lets you
**compute approximate distances directly on the compressed codes**. Compression
that you must decompress before use would not help search speed.

## Why not plain k-means (vector quantization)?

Plain vector quantization learns `C` centroids over the whole space and stores the
index of the nearest one. A code of `b` bits needs `C = 2^b` centroids. For 64 bits
that is 1.8 × 10¹⁹ centroids: impossible to train or store.

## The PQ trick

1. **Split** each `D`-dim vector into `M` subvectors of `D/M` dims.
2. **Train** a separate small codebook of `K` centroids (k-means) in each subspace.
3. **Encode**: replace each subvector with the ID of its nearest centroid. The vector
   becomes `M` IDs, i.e. `M · log₂K` bits. With `K = 256` each ID is one byte.
4. **Decode** (approximately): concatenate the chosen centroids.

Key insight: the effective codebook is the **Cartesian product** of the subspace
codebooks. We store only `M · K` centroids but can represent `K^M` distinct
reconstructions.

| Setting                     | Stored centroids          | Representable vectors |
| --------------------------- | ------------------------- | --------------------- |
| Toy (D=6, M=3, K=4)         | 12                        | 64                    |
| Typical (D=128, M=8, K=256) | 2,048 (128 KiB of floats) | 256⁸ ≈ 1.8 × 10¹⁹     |

Typical compression: 512 B → 8 B per vector, **64×**. A billion vectors drop from
512 GB to 8 GB (plus a 128 KiB shared codebook).

## Distance computation without decompressing (ADC)

*Asymmetric distance computation*: the query stays exact; only database vectors are
quantized.

1. For a query `q`, split it the same way.
2. Build a lookup table `T[m][k] = ‖q_m − c_{m,k}‖²`, an `M × K` array. This costs
   `K · D` multiply-adds, once per query.
3. For each stored code `(i₁ … i_M)`: `d(q, x) ≈ Σ_m T[m][i_m]`. That is `M` table
   lookups and additions per database vector instead of `D` multiplications.

This is exactly `‖q − x̂‖²` where `x̂` is the reconstruction, so the only error is
the quantization error `x − x̂`. (Symmetric distance, SDC, also quantizes the query
and is faster but less accurate; ADC is the standard.)

## Limits and how it is used

- PQ is **lossy**. Vectors in the same cell share a code and get identical
  distances (the toy has four database vectors with code `[0,0,3]` and the same
  score). Real systems use PQ to shortlist, then **rerank** the top candidates with
  exact vectors.
- Splitting assumes the subspaces are roughly independent and balanced. OPQ learns a
  rotation first so that variance spreads evenly across subspaces.
- PQ shrinks the *size* of each vector; it does not reduce *how many* you compare.
  It is combined with IVF (`IVF-PQ`: scan only a few clusters) or a graph index
  (HNSW + PQ) to also cut the candidate count.
- Scanning codes is fast on CPUs: tables of `K=16` fit in SIMD registers (FAISS
  "fast scan"), and on GPUs tables sit in shared memory.

## Checked numbers (see `toy.py`)

Toy example, seed 7, 400 vectors, D=6, M=3, K=4:

- Query `q = [0.5, −1.0 | 1.2, 0.3 | −0.8, 1.1]`.
- Database vector `x = [1.08, −0.83 | 1.60, 0.21 | 0.55, 1.49]` → code `[0, 0, 3]`.
- Lookup table values used: `T[0][0] = 0.44`, `T[1][0] = 0.15`, `T[2][3] = 2.33`;
  ADC distance `= 2.92`. Exact `‖q − x‖² = 2.50`; the gap is quantization error.
- Over 100 noisy queries, the true nearest neighbor is within the ADC top-10 in 93%
  of cases.

The 400 vectors are synthetic: each 2-D slice is drawn around 4 random hubs with
Gaussian noise (σ = 0.35), so that the 2-D scatter plots in the animation show clean
clusters. Real embeddings are messier.

## References

- Jégou, Douze, Schmid. *Product Quantization for Nearest Neighbor Search.* IEEE
  TPAMI 2011. https://inria.hal.science/inria-00514462
- FAISS wiki: indexes and PQ parameters.
  https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
- Ge et al. *Optimized Product Quantization.* CVPR 2013 (OPQ rotation).
