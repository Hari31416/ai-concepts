"""Minimal product quantization (PQ) with asymmetric distance computation (ADC).

Demonstrates:
1. Splitting D-dim vectors into M subvectors and running k-means per subspace.
2. Encoding each vector as M small centroid IDs (the "PQ code").
3. Asymmetric distance: one query-to-centroid lookup table, then M lookups per vector.
4. The compression arithmetic for the real-world setting (D=128, M=8, K=256).

Run `uv run python topics/2026/11/product-quantization/toy.py` to check every claim.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]

# Toy setting used by the animation: 6-dim vectors, 3 subspaces, 4 centroids each.
TOY_DIM = 6
TOY_M = 3
TOY_K = 4
TOY_SEED = 7


def kmeans(
    data: FloatArray, k: int, rng: np.random.Generator, iters: int = 25
) -> FloatArray:
    """Plain Lloyd's k-means with farthest-point seeding; returns (k, d) centroids."""
    centroids = [data[rng.integers(len(data))]]
    for _ in range(k - 1):
        dist = np.min([((data - c) ** 2).sum(axis=1) for c in centroids], axis=0)
        centroids.append(data[int(np.argmax(dist))])
    cent = np.array(centroids)
    for _ in range(iters):
        assign = ((data[:, None, :] - cent[None]) ** 2).sum(axis=2).argmin(axis=1)
        for j in range(k):
            members = data[assign == j]
            if len(members):
                cent[j] = members.mean(axis=0)
    return cent


@dataclass
class ProductQuantizer:
    """Per-subspace codebooks of shape (M, K, D // M)."""

    codebooks: FloatArray

    @property
    def m(self) -> int:
        return int(self.codebooks.shape[0])

    @property
    def k(self) -> int:
        return int(self.codebooks.shape[1])

    @property
    def sub_dim(self) -> int:
        return int(self.codebooks.shape[2])

    @classmethod
    def train(
        cls, data: FloatArray, m: int, k: int, rng: np.random.Generator
    ) -> ProductQuantizer:
        n, dim = data.shape
        assert dim % m == 0, "D must be divisible by M"
        subs = data.reshape(n, m, dim // m)
        return cls(np.stack([kmeans(subs[:, j], k, rng) for j in range(m)]))

    def encode(self, data: FloatArray) -> IntArray:
        """Return (N, M) centroid IDs: each subvector snaps to its nearest centroid."""
        subs = data.reshape(len(data), self.m, self.sub_dim)
        diff = subs[:, :, None, :] - self.codebooks[None]  # (N, M, K, d)
        return (diff**2).sum(axis=3).argmin(axis=2).astype(np.int64)

    def decode(self, codes: IntArray) -> FloatArray:
        """Rebuild the approximate vector by concatenating the chosen centroids."""
        parts = [self.codebooks[j][codes[:, j]] for j in range(self.m)]
        return np.concatenate(parts, axis=1)

    def lookup_table(self, query: FloatArray) -> FloatArray:
        """(M, K) squared distances from each query subvector to each centroid."""
        subs = query.reshape(self.m, self.sub_dim)
        return ((subs[:, None, :] - self.codebooks) ** 2).sum(axis=2)

    def adc(self, query: FloatArray, codes: IntArray) -> FloatArray:
        """Asymmetric distance: sum M table lookups per stored code."""
        table = self.lookup_table(query)
        return table[np.arange(self.m), codes].sum(axis=1)


def make_toy_data(
    n: int = 400, seed: int = TOY_SEED
) -> tuple[FloatArray, np.random.Generator]:
    """Vectors whose every 2-d slice clusters around 4 hubs, so k-means is clean."""
    rng = np.random.default_rng(seed)
    hubs = rng.uniform(-2.0, 2.0, size=(TOY_M, TOY_K, TOY_DIM // TOY_M))
    pick = rng.integers(TOY_K, size=(n, TOY_M))
    parts = [
        hubs[j][pick[:, j]] + rng.normal(0.0, 0.35, size=(n, TOY_DIM // TOY_M))
        for j in range(TOY_M)
    ]
    return np.concatenate(parts, axis=1), rng


def compression(dim: int, m: int, k: int, n_vectors: int) -> dict[str, float]:
    """Byte accounting for raw float32 vectors versus PQ codes plus codebooks."""
    raw = dim * 4
    code = m * int(np.ceil(np.log2(k))) / 8
    return {
        "raw_bytes_per_vector": raw,
        "code_bytes_per_vector": code,
        "ratio": raw / code,
        "raw_total_gb": raw * n_vectors / 1e9,
        "code_total_gb": code * n_vectors / 1e9,
        "codebook_bytes": m * k * (dim // m) * 4,
        "implicit_centroids": float(k) ** m,
        "stored_centroids": m * k,
    }


def verify() -> None:
    """Assert the claims the animation makes."""
    data, rng = make_toy_data()
    pq = ProductQuantizer.train(data, TOY_M, TOY_K, rng)
    codes = pq.encode(data)

    # ADC equals the exact distance to the *reconstructed* vector.
    query = data[0] + rng.normal(0.0, 0.2, size=TOY_DIM)
    adc = pq.adc(query, codes)
    to_recon = ((pq.decode(codes) - query) ** 2).sum(axis=1)
    assert np.allclose(adc, to_recon)

    # Quantization error is small next to the data spread.
    exact = ((data - query) ** 2).sum(axis=1)
    mse = ((data - pq.decode(codes)) ** 2).sum(axis=1).mean()
    assert mse < 0.5 * data.var(axis=0).sum()

    # Ranking by ADC keeps the true nearest neighbor inside the top 10 candidates
    # (PQ is a shortlist step: rerank those few with exact vectors).
    hits = 0
    trials = 100
    for i in range(trials):
        q = data[i] + rng.normal(0.0, 0.2, size=TOY_DIM)
        true_nn = int(((data - q) ** 2).sum(axis=1).argmin())
        approx = pq.adc(q, codes)
        hits += int((approx < approx[true_nn]).sum()) < 10
    recall = hits / trials
    assert recall >= 0.9, recall

    # Real-world arithmetic quoted in the video.
    real = compression(128, 8, 256, 1_000_000_000)
    assert real["raw_bytes_per_vector"] == 512
    assert real["code_bytes_per_vector"] == 8
    assert real["ratio"] == 64
    assert real["raw_total_gb"] == 512.0
    assert real["code_total_gb"] == 8.0
    assert real["codebook_bytes"] == 131072
    assert real["stored_centroids"] == 2048
    assert real["implicit_centroids"] == 256.0**8

    toy = compression(TOY_DIM, TOY_M, TOY_K, len(data))
    assert toy["implicit_centroids"] == 64
    assert toy["stored_centroids"] == 12
    logger.info("all PQ checks passed; recall@10 of true NN via ADC = %.2f", recall)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    verify()
