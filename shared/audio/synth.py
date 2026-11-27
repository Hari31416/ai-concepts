"""Procedural stereo sound effects and a music bed, generated with NumPy only.

Everything here is original, synthesized by this repository's code, so it carries no
third-party license. Output is deterministic: the same call always writes the same
samples. All assets are stereo arrays of shape `(n, 2)` normalized to -3 dBFS peak.

Sound design follows the mechanism, not decoration:

- light, high, plucked notes = the small draft model (`blip_*`);
- bright bells = a verified token (`ping_*`);
- a heavy low hit = the big model or a big memory read (`thump`);
- a burst of fast clicks = data streaming over the memory bus (`stream`);
- a rising sweep = building up to a verification pass (`riser`).

Effects are panned left to right in the order tokens appear on screen, and a short
synthetic reverb gives them space. Phone speakers cannot reproduce below about
150 Hz, so low sounds carry upper harmonics that still read on a phone.
"""

import wave
from collections.abc import Callable
from functools import partial
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

SAMPLE_RATE = 44100
PEAK = 10 ** (-3 / 20)  # -3 dBFS

Samples = NDArray[np.float64]  # shape (n, 2): left, right

# C major pentatonic, so every note sits inside the bed's chords.
_DRAFT_NOTES = (523.25, 587.33, 659.25, 783.99)  # C5 D5 E5 G5
_PING_NOTES = (783.99, 880.00, 1046.50, 1318.51)  # G5 A5 C6 E6
_PAN_LADDER = (-0.55, -0.18, 0.18, 0.55)  # left to right, like tokens on screen
LADDER_STEPS = len(_DRAFT_NOTES)


def _t(seconds: float) -> NDArray[np.float64]:
    return np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE


def _normalize(samples: Samples, peak: float = PEAK) -> Samples:
    top = float(np.max(np.abs(samples)))
    return samples if top == 0 else samples * (peak / top)


def _pan(mono: NDArray[np.float64], position: float | NDArray[np.float64]) -> Samples:
    """Constant-power pan; `position` runs from -1 (left) to 1 (right), or a curve."""
    angle = (np.asarray(position) + 1.0) * np.pi / 4.0
    return np.column_stack((mono * np.cos(angle), mono * np.sin(angle)))


def _pad(samples: Samples, total: int) -> Samples:
    out = np.zeros((total, 2))
    out[: samples.shape[0]] += samples
    return out


def _lowpass_fft(x: NDArray[np.float64], cutoff: float) -> NDArray[np.float64]:
    """Smooth low-pass along axis 0 in the frequency domain (periodic, no phase loop)."""
    freqs = np.fft.rfftfreq(x.shape[0], 1.0 / SAMPLE_RATE)
    gain = 1.0 / (1.0 + (freqs / cutoff) ** 2)
    gain = gain.reshape((-1,) + (1,) * (x.ndim - 1))
    return np.asarray(np.fft.irfft(np.fft.rfft(x, axis=0) * gain, n=x.shape[0], axis=0))


def _impulse(seconds: float, seed: int) -> Samples:
    """A dark, decaying, decorrelated noise tail used as a room impulse response."""
    rng = np.random.default_rng(seed)
    t = _t(seconds)
    ir = rng.standard_normal((t.size, 2)) * np.exp(-t * 7.0 / seconds)[:, None]
    ir = _lowpass_fft(ir, 3500.0)
    return ir / np.sqrt(np.sum(ir**2, axis=0))


def _reverb(
    x: Samples,
    *,
    seconds: float = 0.6,
    wet: float = 0.25,
    seed: int = 3,
    circular: bool = False,
) -> Samples:
    """Convolve with a synthetic room. `circular` wraps the tail so loops stay seamless."""
    n = x.shape[0]
    ir = _impulse(seconds, seed)
    if circular:
        folded = np.zeros((n, 2))
        np.add.at(folded, np.arange(ir.shape[0]) % n, ir)
        tail = np.fft.irfft(
            np.fft.rfft(x, axis=0) * np.fft.rfft(folded, axis=0), n=n, axis=0
        )
        return np.asarray(x + wet * tail)
    size = n + ir.shape[0] - 1
    tail = np.fft.irfft(
        np.fft.rfft(x, size, axis=0) * np.fft.rfft(ir, size, axis=0), n=size, axis=0
    )
    return _pad(x, size) + wet * tail


def _smooth_noise(seed: int, seconds: float, alpha: NDArray[np.float64]) -> NDArray:
    """White noise through a one-pole low-pass whose coefficient follows `alpha`."""
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(int(seconds * SAMPLE_RATE))
    out = np.empty_like(noise)
    state = 0.0
    for i, (sample, a) in enumerate(zip(noise, alpha)):
        state += a * (sample - state)
        out[i] = state
    return out


def pop() -> Samples:
    """A soft bubble: a short downward pitch sweep (a block is claimed)."""
    t = _t(0.14)
    freq = 700 * np.exp(-t * 7.0) + 280
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    mono = np.sin(phase) * np.exp(-t * 28.0)
    return _normalize(_reverb(_pan(mono, 0.0), seconds=0.4, wet=0.2))


def tick() -> Samples:
    """A tiny click (one table entry or one token is written)."""
    t = _t(0.05)
    mono = (np.sin(2 * np.pi * 3200 * t) + 0.4 * np.sin(2 * np.pi * 6400 * t)) * np.exp(
        -t * 85.0
    )
    return _normalize(_reverb(_pan(mono, 0.0), seconds=0.3, wet=0.15))


def whoosh() -> Samples:
    """Filtered noise that sweeps from left to right (a scene change)."""
    t = _t(0.6)
    envelope = np.sin(np.pi * t / t[-1]) ** 2
    noise = _smooth_noise(7, 0.6, 0.02 + 0.5 * envelope)
    sweep = _pan(noise * envelope, -0.8 + 1.6 * t / t[-1])
    return _normalize(_reverb(sweep, seconds=0.7, wet=0.25))


def deny() -> Samples:
    """A low two-note drop with a dull thud (a request is rejected)."""
    t = _t(0.42)
    freq = np.where(t < 0.16, 220.0, 165.0)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase) + 0.45 * np.sin(2 * phase) + 0.2 * np.sin(3 * phase)
    thud = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18.0)
    mono = tone * np.exp(-t * 7.0) * np.minimum(t * 200, 1.0) + 0.8 * thud
    return _normalize(_reverb(_pan(mono, 0.0), seconds=0.5, wet=0.2))


def _bell(freq: float, seconds: float, decay: float = 5.0) -> NDArray[np.float64]:
    """Struck-metal tone: inharmonic partials that die away at different speeds."""
    t = _t(seconds)
    mono = np.zeros(t.size)
    for ratio, amp, rate in ((1.0, 1.0, 1.0), (2.76, 0.5, 1.4), (5.4, 0.25, 2.0)):
        mono += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * decay * rate)
    return mono * np.minimum(t * 800, 1.0)


def _tine(freq: float, seconds: float) -> NDArray[np.float64]:
    """Kalimba-like pluck: a fundamental plus a quick, bright overtone."""
    t = _t(seconds)
    mono = np.sin(2 * np.pi * freq * t) * np.exp(-t * 7.0)
    mono += 0.35 * np.sin(2 * np.pi * freq * 4.0 * t) * np.exp(-t * 26.0)
    mono += 0.15 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 14.0)
    return mono * np.minimum(t * 1500, 1.0)


def blip(step: int) -> Samples:
    """A light kalimba pluck for the small draft model; rises with `step` (0 to 3)."""
    mono = _tine(_DRAFT_NOTES[step], 0.5)
    return _normalize(_reverb(_pan(mono, _PAN_LADDER[step]), seconds=0.5, wet=0.25))


def ping(step: int) -> Samples:
    """A bright bell for a verified token; rises with `step` (0 to 3)."""
    mono = _bell(_PING_NOTES[step], 0.9)
    return _normalize(_reverb(_pan(mono, _PAN_LADDER[step]), seconds=0.7, wet=0.3))


def thump() -> Samples:
    """A heavy low hit for the big model; harmonics keep it audible on a phone."""
    t = _t(0.7)
    freq = 48 + 90 * np.exp(-t * 22.0)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    body = np.sin(phase) + 0.55 * np.sin(2 * phase) + 0.3 * np.sin(3 * phase)
    knock = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30.0)
    rng = np.random.default_rng(11)
    click = _lowpass_fft(rng.standard_normal(t.size), 2500.0) * np.exp(-t * 140.0)
    mono = body * np.exp(-t * 6.5) + 0.7 * knock + 0.4 * click
    return _normalize(_reverb(_pan(mono, 0.0), seconds=0.7, wet=0.25))


def riser() -> Samples:
    """A rising sweep that builds toward a verification pass."""
    seconds = 0.9
    t = _t(seconds)
    progress = t / seconds
    freq = 180.0 * (1400.0 / 180.0) ** progress
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    noise = _smooth_noise(5, seconds, 0.03 + 0.55 * progress**2)
    envelope = progress**2 * np.minimum((seconds - t) / 0.03, 1.0)
    mono = (0.5 * tone + noise) * envelope
    return _normalize(_reverb(_pan(mono, -0.3 + 0.6 * progress), seconds=0.6, wet=0.2))


def stream() -> Samples:
    """A burst of fast, panned clicks that speeds up (data crossing the memory bus)."""
    rng = np.random.default_rng(21)
    seconds = 0.6
    out = np.zeros((int(seconds * SAMPLE_RATE), 2))
    starts = np.sort(rng.random(38)) ** 0.6 * (seconds - 0.05)
    for start in starts:
        click = _tine(float(rng.uniform(1500, 4200)), 0.04) * rng.uniform(0.4, 1.0)
        left = int(start * SAMPLE_RATE)
        out[left : left + click.size] += _pan(click, float(rng.uniform(-0.9, 0.9)))[
            : out.shape[0] - left
        ]
    return _normalize(_reverb(out, seconds=0.4, wet=0.2))


def chime() -> Samples:
    """A rising three-bell arpeggio with a long tail (the payoff at the end)."""
    out = np.zeros((int(1.5 * SAMPLE_RATE), 2))
    for i, (freq, pan_pos) in enumerate(
        ((783.99, -0.3), (1046.50, 0.0), (1567.98, 0.3))
    ):
        start = int(i * 0.1 * SAMPLE_RATE)
        bell = _bell(freq, 1.4 - i * 0.1, decay=3.2)
        out[start : start + bell.size] += _pan(bell, pan_pos)
    return _normalize(_reverb(out, seconds=1.3, wet=0.45))


# Four 8-second chords (C add9, A minor, F, G sus) looped to a 32-second bed.
_CHORDS: tuple[tuple[float, ...], ...] = (
    (130.81, 164.81, 196.00, 293.66),
    (110.00, 164.81, 196.00, 261.63),
    (87.31, 130.81, 220.00, 261.63),
    (98.00, 146.83, 196.00, 220.00),
)
_CHORD_SECONDS = 8.0
_BED_SECONDS = len(_CHORDS) * _CHORD_SECONDS
# Plucked notes per chord window: (start second, index into the chord, octave factor).
_ARPEGGIO = (
    (0.0, 3, 2),
    (1.0, 1, 4),
    (2.5, 2, 4),
    (3.5, 0, 4),
    (5.0, 3, 2),
    (6.0, 2, 4),
)


def music_bed() -> Samples:
    """A warm stereo pad with a bass, a breathing air layer and echoing plucks.

    Loops seamlessly: every layer wraps around the end and the reverb is circular.
    """
    total = int(_BED_SECONDS * SAMPLE_RATE)
    out = np.zeros((total, 2))
    window = int(_CHORD_SECONDS * SAMPLE_RATE)

    def add_wrapped(start: int, samples: Samples, gain: float = 1.0) -> None:
        idx = (start + np.arange(samples.shape[0])) % total
        np.add.at(out, idx, samples * gain)

    tail = _t(_CHORD_SECONDS + 3.0)
    attack = np.minimum(tail / 2.0, 1.0)
    release = np.clip((tail[-1] - tail) / 3.0, 0.0, 1.0)
    swell = 0.8 + 0.2 * np.sin(2 * np.pi * tail / 4.0)  # slow breathing
    pad_env = attack * release * swell

    for i, chord in enumerate(_CHORDS):
        left = np.zeros(tail.size)
        right = np.zeros(tail.size)
        for freq in chord:
            left += np.sin(2 * np.pi * (freq - 0.3) * tail) + 0.2 * np.sin(
                2 * np.pi * 2 * freq * tail
            )
            right += np.sin(2 * np.pi * (freq + 0.3) * tail) + 0.2 * np.sin(
                2 * np.pi * 2 * freq * tail
            )
        pad = np.column_stack((left, right)) * (pad_env * 0.11)[:, None]
        add_wrapped(i * window, pad)

        root = chord[0] / 2.0  # bass note, with a harmonic that small speakers keep
        bass = np.sin(2 * np.pi * root * tail) + 0.5 * np.sin(
            2 * np.pi * 2 * root * tail
        )
        add_wrapped(i * window, _pan(bass * attack * release, 0.0), 0.17)

        for start, index, octave in _ARPEGGIO:
            note = chord[(index + i) % len(chord)] * octave
            pluck = _tine(note, 1.8)
            pos = -0.5 if int(start * 2) % 2 == 0 else 0.5
            begin = i * window + int(start * SAMPLE_RATE)
            add_wrapped(begin, _pan(pluck, pos), 0.075)
            add_wrapped(  # a soft echo on the opposite side
                begin + int(0.5 * SAMPLE_RATE), _pan(pluck, -pos), 0.032
            )

    # Air layer: noise filtered in the frequency domain (so it wraps cleanly) that
    # breathes four times per loop.
    rng = np.random.default_rng(2)
    air = _lowpass_fft(rng.standard_normal((total, 2)), 900.0)
    air *= (0.55 + 0.45 * np.sin(2 * np.pi * 4 * np.arange(total) / total))[:, None]
    out += air * (0.75 / float(np.max(np.abs(air))) * 0.05)

    return _normalize(_reverb(out, seconds=2.0, wet=0.3, circular=True))


GENERATORS: dict[str, Callable[[], Samples]] = {
    "pop": pop,
    "tick": tick,
    "whoosh": whoosh,
    "deny": deny,
    "chime": chime,
    "thump": thump,
    "riser": riser,
    "stream": stream,
    **{f"blip_{i}": partial(blip, i) for i in range(LADDER_STEPS)},
    **{f"ping_{i}": partial(ping, i) for i in range(LADDER_STEPS)},
    "music_bed": music_bed,
}


def write_wav(path: Path, samples: Samples) -> None:
    """Write stereo 16-bit PCM."""
    pcm = np.round(np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())
