"""Unit tests verifying continuous batching simulation mechanics and metrics."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import pytest


def _load_toy_module() -> ModuleType:
    module_path = (
        Path(__file__).parent.parent
        / "topics"
        / "2026"
        / "10"
        / "continuous-batching"
        / "toy.py"
    )
    spec = importlib.util.spec_from_file_location("cb_toy", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


toy = _load_toy_module()


def test_static_batching_simulation() -> None:
    workload = [
        toy.Request("R1", tokens_to_generate=2, arrival_time=0),
        toy.Request("R2", tokens_to_generate=4, arrival_time=0),
        toy.Request("R3", tokens_to_generate=6, arrival_time=0),
        toy.Request("R4", tokens_to_generate=3, arrival_time=0),
        toy.Request("R5", tokens_to_generate=3, arrival_time=0),
    ]

    res = toy.simulate_static_batching(workload, batch_size=3)

    assert res.total_steps == 9
    assert res.useful_token_steps == 18
    assert res.wasted_bubble_steps == 9
    assert pytest.approx(res.utilization_rate, abs=1e-3) == 0.667


def test_continuous_batching_simulation() -> None:
    workload = [
        toy.Request("R1", tokens_to_generate=2, arrival_time=0),
        toy.Request("R2", tokens_to_generate=4, arrival_time=0),
        toy.Request("R3", tokens_to_generate=6, arrival_time=0),
        toy.Request("R4", tokens_to_generate=3, arrival_time=0),
        toy.Request("R5", tokens_to_generate=3, arrival_time=0),
    ]

    res = toy.simulate_continuous_batching(workload, batch_size=3)

    assert res.total_steps == 7
    assert res.useful_token_steps == 18
    assert res.wasted_bubble_steps == 3  # Tail drain after all requests admitted
    assert pytest.approx(res.utilization_rate, abs=1e-3) == 0.857
    assert res.total_steps < 9
    assert res.average_latency < 6.5
