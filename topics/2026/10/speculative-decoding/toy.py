"""Minimal reference implementation of speculative decoding.

Implements speculative sampling and greedy verification, validating that
speculative decoding produces the exact same distribution as the target model.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
import random
from typing import Callable, Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpeculativeResult:
    """Outcome of a speculative verification cycle."""

    accepted_tokens: list[int]
    terminal_token: int
    num_drafted: int
    num_accepted: int

    @property
    def total_tokens(self) -> int:
        """Total tokens emitted in this step."""
        return self.num_accepted + 1

    @property
    def all_emitted(self) -> list[int]:
        """All tokens emitted from this cycle."""
        return self.accepted_tokens + [self.terminal_token]


def compute_residual_distribution(
    target_probs: Sequence[float], draft_probs: Sequence[float]
) -> list[float]:
    """Compute normalized residual distribution max(0, p - q) / Z."""
    if len(target_probs) != len(draft_probs):
        raise ValueError(
            "Target and draft distributions must have equal vocabulary size."
        )

    raw_residuals = [max(0.0, p - q) for p, q in zip(target_probs, draft_probs)]
    norm = sum(raw_residuals)

    if norm <= 1e-12:
        # p and q are practically identical; return target distribution
        return list(target_probs)

    return [r / norm for r in raw_residuals]


def sample_from_distribution(probs: Sequence[float], rng: random.Random) -> int:
    """Sample an index from a categorical distribution."""
    r = rng.random()
    cumulative = 0.0
    for idx, prob in enumerate(probs):
        cumulative += prob
        if r <= cumulative:
            return idx
    return len(probs) - 1


def verify_draft_tokens_stochastic(
    target_distributions: Sequence[Sequence[float]],
    draft_distributions: Sequence[Sequence[float]],
    draft_tokens: Sequence[int],
    rng: random.Random,
) -> SpeculativeResult:
    """Verify draft tokens with modified rejection sampling.

    Args:
        target_distributions: Target distribution for each draft position (length K+1).
        draft_distributions: Draft distribution for each draft position (length K).
        draft_tokens: The K tokens drafted by the draft model.
        rng: Random number generator.

    Returns:
        SpeculativeResult with accepted tokens and final emitted token.
    """
    k = len(draft_tokens)
    if len(draft_distributions) != k:
        raise ValueError("Must have draft distribution for every drafted token.")
    if len(target_distributions) != k + 1:
        raise ValueError("Target distributions must provide K+1 distributions.")

    accepted: list[int] = []

    for i in range(k):
        token = draft_tokens[i]
        p_val = target_distributions[i][token]
        q_val = draft_distributions[i][token]

        # Rejection sampling acceptance threshold: min(1, p/q)
        threshold = 1.0 if q_val <= 0.0 else min(1.0, p_val / q_val)
        draw = rng.random()

        if draw < threshold:
            accepted.append(token)
        else:
            # Rejection: sample from normalized residual (p - q)+
            residual = compute_residual_distribution(
                target_distributions[i], draft_distributions[i]
            )
            corrected_token = sample_from_distribution(residual, rng)
            logger.debug(
                "Draft token %d rejected at position %d, resampled %d",
                token,
                i,
                corrected_token,
            )
            return SpeculativeResult(
                accepted_tokens=accepted,
                terminal_token=corrected_token,
                num_drafted=k,
                num_accepted=len(accepted),
            )

    # All K accepted: sample bonus token from target_distributions[K]
    bonus_token = sample_from_distribution(target_distributions[k], rng)
    return SpeculativeResult(
        accepted_tokens=accepted,
        terminal_token=bonus_token,
        num_drafted=k,
        num_accepted=k,
    )


def verify_draft_tokens_greedy(
    target_argmax_tokens: Sequence[int],
    draft_tokens: Sequence[int],
) -> SpeculativeResult:
    """Verify draft tokens under greedy (argmax) decoding.

    Args:
        target_argmax_tokens: Target argmax predictions for positions 0..K (length K+1).
        draft_tokens: The K tokens drafted by the draft model.

    Returns:
        SpeculativeResult matching target greedy output.
    """
    k = len(draft_tokens)
    if len(target_argmax_tokens) != k + 1:
        raise ValueError("Target argmax must have length K+1.")

    accepted: list[int] = []
    for i in range(k):
        draft_token = draft_tokens[i]
        target_token = target_argmax_tokens[i]
        if draft_token == target_token:
            accepted.append(draft_token)
        else:
            return SpeculativeResult(
                accepted_tokens=accepted,
                terminal_token=target_token,
                num_drafted=k,
                num_accepted=len(accepted),
            )

    bonus_token = target_argmax_tokens[k]
    return SpeculativeResult(
        accepted_tokens=accepted,
        terminal_token=bonus_token,
        num_drafted=k,
        num_accepted=k,
    )


def simulate_single_token_distribution(
    p: Sequence[float],
    q: Sequence[float],
    trials: int = 100_000,
    seed: int = 42,
) -> list[float]:
    """Empirically test that speculative sampling recovers target distribution p."""
    rng = random.Random(seed)
    counts = [0] * len(p)

    for _ in range(trials):
        # Draft model samples one token
        draft_token = sample_from_distribution(q, rng)
        # Verify single token
        result = verify_draft_tokens_stochastic(
            target_distributions=[p, p],  # dummy bonus
            draft_distributions=[q],
            draft_tokens=[draft_token],
            rng=rng,
        )
        first_token = result.all_emitted[0]
        counts[first_token] += 1

    return [c / trials for c in counts]
