"""Unit tests verifying speculative decoding mathematics and implementations."""

import importlib.util
from pathlib import Path
import random
import sys
from types import ModuleType
import pytest


def _load_toy_module() -> ModuleType:
    module_path = (
        Path(__file__).parent.parent
        / "topics"
        / "2026"
        / "10"
        / "speculative-decoding"
        / "toy.py"
    )
    spec = importlib.util.spec_from_file_location("speculative_toy", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


toy = _load_toy_module()


def test_residual_distribution_sums_to_one() -> None:
    target = [0.60, 0.25, 0.10, 0.05]
    draft = [0.40, 0.40, 0.10, 0.10]
    residual = toy.compute_residual_distribution(target, draft)

    assert len(residual) == 4
    assert pytest.approx(sum(residual), abs=1e-6) == 1.0
    # From notes.md: target - draft for token 0 is 0.20, others <= 0.
    assert pytest.approx(residual[0], abs=1e-6) == 1.0
    assert pytest.approx(residual[1], abs=1e-6) == 0.0


def test_distribution_preservation() -> None:
    p = [0.55, 0.30, 0.10, 0.05]
    q = [0.35, 0.45, 0.10, 0.10]

    empirical_p = toy.simulate_single_token_distribution(p, q, trials=50_000, seed=123)

    for i in range(len(p)):
        assert pytest.approx(empirical_p[i], abs=0.015) == p[i]


def test_greedy_verification_partial_acceptance() -> None:
    target_tokens = [10, 20, 99, 40]
    draft_tokens = [10, 20, 30]  # token at index 2 (30) differs from target (99)

    result = toy.verify_draft_tokens_greedy(target_tokens, draft_tokens)

    assert result.accepted_tokens == [10, 20]
    assert result.terminal_token == 99
    assert result.all_emitted == [10, 20, 99]
    assert result.num_accepted == 2
    assert result.total_tokens == 3


def test_greedy_verification_full_acceptance() -> None:
    target_tokens = [10, 20, 30, 40]
    draft_tokens = [10, 20, 30]

    result = toy.verify_draft_tokens_greedy(target_tokens, draft_tokens)

    assert result.accepted_tokens == [10, 20, 30]
    assert result.terminal_token == 40
    assert result.all_emitted == [10, 20, 30, 40]
    assert result.num_accepted == 3
    assert result.total_tokens == 4


def test_stochastic_all_accepted_gives_bonus() -> None:
    target_distributions = [
        [0.8, 0.2],
        [0.9, 0.1],
        [0.7, 0.3],
        [0.5, 0.5],
    ]
    draft_distributions = [
        [0.7, 0.3],
        [0.8, 0.2],
        [0.6, 0.4],
    ]
    draft_tokens = [0, 0, 0]
    rng = random.Random(42)

    result = toy.verify_draft_tokens_stochastic(
        target_distributions=target_distributions,
        draft_distributions=draft_distributions,
        draft_tokens=draft_tokens,
        rng=rng,
    )

    assert result.accepted_tokens == [0, 0, 0]
    assert result.num_accepted == 3
    assert result.terminal_token in [0, 1]
    assert result.total_tokens == 4
