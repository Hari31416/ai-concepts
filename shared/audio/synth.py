"""Procedural sound effects and a music bed, generated with NumPy only.

Everything here is original, synthesized by this repository's code, so it carries no
third-party license. Output is deterministic: the same call always writes the same
samples. Peaks are normalized to -3 dBFS.
"""

import wave
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

SAMPLE_RATE = 44100
PEAK = 10 ** (-3 / 20)  # -3 dBFS

Samples = NDArray[np.float64]


def _t(seconds: float) -> Samples:
    return np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE


def _normalize(samples: Samples, peak: float = PEAK) -> Samples:
    top = float(np.max(np.abs(samples)))
    return samples if top == 0 else samples * (peak / top)


def pop() -> Samples:
    """A soft bubble: a short downward pitch sweep (a block is claimed)."""
    t = _t(0.14)
    freq = 700 * np.exp(-t * 7.0) + 280
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return _normalize(np.sin(phase) * np.exp(-t * 28.0))


def tick() -> Samples:
    """A tiny click (one table entry or one token is written)."""
    t = _t(0.06)
    wave_ = np.sin(2 * np.pi * 1900 * t) + 0.4 * np.sin(2 * np.pi * 3800 * t)
    return _normalize(wave_ * np.exp(-t * 70.0))


def whoosh() -> Samples:
    """Filtered noise with a rising then falling brightness (a scene change)."""
    rng = np.random.default_rng(7)
    t = _t(0.55)
    noise = rng.standard_normal(t.size)
    envelope = np.sin(np.pi * t / t[-1]) ** 2
    alpha = 0.02 + 0.5 * envelope  # one-pole low-pass coefficient follows envelope
    out = np.empty_like(noise)
    state = 0.0
    for i, (sample, a) in enumerate(zip(noise, alpha)):
        state += a * (sample - state)
        out[i] = state
    return _normalize(out * envelope)


def deny() -> Samples:
    """A low two-note drop (a request is rejected)."""
    t = _t(0.38)
    freq = np.where(t < 0.16, 220.0, 165.0)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase) + 0.3 * np.sin(2 * phase)
    return _normalize(tone * np.exp(-t * 7.0) * np.minimum(t * 200, 1.0))


def chime() -> Samples:
    """A bright three-partial chime (the payoff at the end)."""
    t = _t(1.1)
    tone = sum(
        amp * np.sin(2 * np.pi * freq * t)
        for freq, amp in ((784.0, 1.0), (1174.7, 0.5), (1568.0, 0.3))
    )
    return _normalize(tone * np.exp(-t * 4.0) * np.minimum(t * 300, 1.0))


# Four 8-second chords (C add9, A minor, F, G sus) looped to a 32-second bed.
_CHORDS: tuple[tuple[float, ...], ...] = (
    (130.81, 164.81, 196.00, 293.66),
    (110.00, 164.81, 196.00, 261.63),
    (87.31, 130.81, 220.00, 261.63),
    (98.00, 146.83, 196.00, 220.00),
)
_CHORD_SECONDS = 8.0


def music_bed() -> Samples:
    """A calm ambient pad with sparse plucks; loops seamlessly."""
    total = int(len(_CHORDS) * _CHORD_SECONDS * SAMPLE_RATE)
    out = np.zeros(total)
    window = int(_CHORD_SECONDS * SAMPLE_RATE)
    tail = _t(_CHORD_SECONDS + 3.0)

    def add_wrapped(start: int, samples: Samples) -> None:
        idx = (start + np.arange(samples.size)) % total
        np.add.at(out, idx, samples)

    attack = np.minimum(tail / 2.0, 1.0)
    release = np.clip((tail[-1] - tail) / 3.0, 0.0, 1.0)
    pad_env = attack * release
    for i, chord in enumerate(_CHORDS):
        pad = np.zeros(tail.size)
        for freq in chord:
            pad += np.sin(2 * np.pi * freq * tail)
            pad += 0.6 * np.sin(2 * np.pi * (freq + 0.35) * tail)  # slow chorus
            pad += 0.2 * np.sin(2 * np.pi * 2 * freq * tail)
        add_wrapped(i * window, pad * pad_env * 0.12)
        for beat in range(4):  # one soft pluck every 2 seconds
            note = chord[(beat * 2 + i) % len(chord)] * 2
            pluck_t = _t(1.6)
            pluck = np.sin(2 * np.pi * note * pluck_t) * np.exp(-pluck_t * 3.5)
            add_wrapped(i * window + int(beat * 2.0 * SAMPLE_RATE), pluck * 0.07)
    return _normalize(out)


GENERATORS = {
    "pop": pop,
    "tick": tick,
    "whoosh": whoosh,
    "deny": deny,
    "chime": chime,
    "music_bed": music_bed,
}


def write_wav(path: Path, samples: Samples) -> None:
    """Write mono 16-bit PCM."""
    pcm = np.round(np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())
