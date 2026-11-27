"""Tests for the product quantization reference implementation."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np


def _load_toy_module() -> ModuleType:
    module_path = (
        Path(__file__).parent.parent
        / "topics"
        / "2026"
        / "11"
        / "product-quantization"
        / "toy.py"
    )
    spec = importlib.util.spec_from_file_location(
        "product_quantization_toy", module_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


toy = _load_toy_module()


def _trained() -> tuple[np.ndarray, Any, np.ndarray]:
    data, rng = toy.make_toy_data()
    pq = toy.ProductQuantizer.train(data, toy.TOY_M, toy.TOY_K, rng)
    return data, pq, pq.encode(data)


def test_codes_have_one_small_id_per_subspace() -> None:
    data, pq, codes = _trained()
    assert codes.shape == (len(data), toy.TOY_M)
    assert codes.min() >= 0 and codes.max() < toy.TOY_K


def test_adc_equals_distance_to_reconstruction() -> None:
    data, pq, codes = _trained()
    query = np.array([0.5, -1.0, 1.2, 0.3, -0.8, 1.1])
    expected = ((pq.decode(codes) - query) ** 2).sum(axis=1)
    assert np.allclose(pq.adc(query, codes), expected)


def test_worked_example_numbers_in_video() -> None:
    data, pq, codes = _trained()
    assert list(codes[349]) == [0, 0, 3]
    query = np.array([0.5, -1.0, 1.2, 0.3, -0.8, 1.1])
    lut = np.round(pq.lookup_table(query), 2)
    assert (lut[0, 0], lut[1, 0], lut[2, 3]) == (0.44, 0.15, 2.33)
    assert abs(pq.adc(query, codes)[349] - 2.93) < 0.01
    assert abs(((data[349] - query) ** 2).sum() - 2.50) < 0.01


def test_compression_arithmetic() -> None:
    real = toy.compression(128, 8, 256, 1_000_000_000)
    assert real["ratio"] == 64
    assert real["raw_total_gb"] == 512.0 and real["code_total_gb"] == 8.0
    assert real["stored_centroids"] == 2048
    assert toy.compression(6, 3, 4, 400)["implicit_centroids"] == 64


def test_verify_passes() -> None:
    toy.verify()
