"""Minimal simulation of Static Batching vs Continuous Batching in LLM serving.

Demonstrates iteration-level scheduling, slot utilization, bubble elimination,
and throughput comparison using concrete request workloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Request:
    request_id: str
    tokens_to_generate: int
    arrival_time: int
    tokens_generated: int = 0
    start_time: int | None = None
    finish_time: int | None = None

    @property
    def is_finished(self) -> bool:
        return self.tokens_generated >= self.tokens_to_generate


@dataclass
class SimulationResult:
    total_steps: int
    total_slots_allocated: int
    useful_token_steps: int
    wasted_bubble_steps: int
    utilization_rate: float
    average_latency: float


def simulate_static_batching(
    requests: List[Request], batch_size: int = 3
) -> SimulationResult:
    """Simulate static (request-level) batching.

    Requests are batched in groups of up to `batch_size`.
    A batch executes until all requests in the batch complete.
    Finished requests sit idle in the batch until the slowest finishes.
    """
    pending = [
        Request(r.request_id, r.tokens_to_generate, r.arrival_time) for r in requests
    ]
    completed: List[Request] = []
    current_time = 0
    total_slots = 0
    useful_tokens = 0

    while pending:
        # Form next static batch from currently available requests
        batch = pending[:batch_size]
        pending = pending[batch_size:]

        for req in batch:
            req.start_time = current_time

        max_tokens_in_batch = max(req.tokens_to_generate for req in batch)
        batch_capacity = batch_size * max_tokens_in_batch
        total_slots += batch_capacity

        tokens_in_this_batch = sum(req.tokens_to_generate for req in batch)
        useful_tokens += tokens_in_this_batch

        current_time += max_tokens_in_batch
        for req in batch:
            req.tokens_generated = req.tokens_to_generate
            req.finish_time = current_time
            completed.append(req)

    wasted = total_slots - useful_tokens
    utilization = useful_tokens / total_slots if total_slots > 0 else 0.0
    avg_latency = (
        sum(r.finish_time - r.arrival_time for r in completed) / len(completed)
        if completed
        else 0.0
    )

    return SimulationResult(
        total_steps=current_time,
        total_slots_allocated=total_slots,
        useful_token_steps=useful_tokens,
        wasted_bubble_steps=wasted,
        utilization_rate=utilization,
        average_latency=avg_latency,
    )


def simulate_continuous_batching(
    requests: List[Request], batch_size: int = 3
) -> SimulationResult:
    """Simulate continuous (iteration-level) batching.

    At each decoding iteration:
    - Running requests generate 1 token.
    - Requests reaching their target length are immediately evicted.
    - Waiting requests in queue are immediately admitted into free slots.
    """
    pending = [
        Request(r.request_id, r.tokens_to_generate, r.arrival_time) for r in requests
    ]
    active: List[Request] = []
    completed: List[Request] = []
    current_time = 0
    total_slots = 0
    useful_tokens = 0

    while pending or active:
        # Admit waiting requests into free slots
        while len(active) < batch_size and pending:
            req = pending.pop(0)
            if req.start_time is None:
                req.start_time = current_time
            active.append(req)

        if not active:
            break

        slots_this_step = batch_size
        total_slots += slots_this_step
        useful_this_step = len(active)
        useful_tokens += useful_this_step

        current_time += 1

        # Generate 1 token for each active request
        survivors: List[Request] = []
        for req in active:
            req.tokens_generated += 1
            if req.is_finished:
                req.finish_time = current_time
                completed.append(req)
            else:
                survivors.append(req)
        active = survivors

    wasted = total_slots - useful_tokens
    utilization = useful_tokens / total_slots if total_slots > 0 else 0.0
    avg_latency = (
        sum(r.finish_time - r.arrival_time for r in completed) / len(completed)
        if completed
        else 0.0
    )

    return SimulationResult(
        total_steps=current_time,
        total_slots_allocated=total_slots,
        useful_token_steps=useful_tokens,
        wasted_bubble_steps=wasted,
        utilization_rate=utilization,
        average_latency=avg_latency,
    )


def test_simulation_verification() -> None:
    """Verify metrics match expected theoretical calculations."""
    workload = [
        Request("R1", tokens_to_generate=2, arrival_time=0),
        Request("R2", tokens_to_generate=4, arrival_time=0),
        Request("R3", tokens_to_generate=6, arrival_time=0),
        Request("R4", tokens_to_generate=3, arrival_time=0),
        Request("R5", tokens_to_generate=3, arrival_time=0),
    ]

    static_res = simulate_static_batching(workload, batch_size=3)
    cont_res = simulate_continuous_batching(workload, batch_size=3)

    # Static:
    # Batch 1: max(2, 4, 6) = 6 steps. 3 * 6 = 18 slots. Useful = 12. Wasted = 6.
    # Batch 2: max(3, 3) = 3 steps. 3 * 3 = 9 slots. Useful = 6. Wasted = 3.
    # Total steps = 9. Total slots = 27. Useful = 18. Wasted = 9.
    assert static_res.total_steps == 9
    assert static_res.total_slots_allocated == 27
    assert static_res.useful_token_steps == 18
    assert static_res.wasted_bubble_steps == 9
    assert abs(static_res.utilization_rate - (18 / 27)) < 1e-4

    # Continuous:
    # Step 1: [R1, R2, R3] active
    # Step 2: [R1, R2, R3] active -> R1 finishes (2 tokens)
    # Step 3: [R4, R2, R3] active
    # Step 4: [R4, R2, R3] active -> R2 finishes (4 tokens)
    # Step 5: [R4, R5, R3] active -> R4 (3 tokens) & R3 (6 tokens) finish
    # Step 6: [R5] active
    # Step 7: [R5] active -> R5 finishes (3 tokens)
    # Total steps = 7.
    assert cont_res.total_steps == 7
    assert cont_res.useful_token_steps == 18
    assert cont_res.total_steps < static_res.total_steps
    assert cont_res.average_latency < static_res.average_latency
    print("All verification tests passed successfully!")


if __name__ == "__main__":
    test_simulation_verification()
