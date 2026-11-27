"""Test generated audio assets and the ffmpeg mix graph."""

import wave
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from scripts.mix_audio import PEAK_LIMIT, build_filter
from shared.audio import SFX_GAIN_DB, SFX_NAMES, asset_path, play_sfx
from shared.audio.synth import GENERATORS, PEAK, SAMPLE_RATE, music_bed


def test_generators_are_deterministic() -> None:
    for name, generate in GENERATORS.items():
        if name == "music_bed":
            continue
        assert np.array_equal(generate(), generate())


def test_effects_are_short_and_peak_at_minus_three_dbfs() -> None:
    for name in SFX_NAMES:
        samples = GENERATORS[name]()
        assert 0.03 < samples.size / SAMPLE_RATE < 1.5
        assert np.max(np.abs(samples)) == pytest.approx(PEAK)


def test_music_bed_length_and_loop_seam() -> None:
    samples = music_bed()
    assert samples.size == 32 * SAMPLE_RATE
    assert np.max(np.abs(samples)) == pytest.approx(PEAK)
    # No click where the loop wraps: the jump across the seam is small.
    seam_jump = abs(samples[0] - samples[-1])
    assert seam_jump < 0.05


def test_asset_path_writes_mono_16_bit_wav() -> None:
    path = asset_path("tick")
    assert path.exists()
    with wave.open(str(path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == SAMPLE_RATE


def test_asset_path_rejects_unknown_name() -> None:
    with pytest.raises(KeyError):
        asset_path("nope")


def test_play_sfx_uses_shared_gain() -> None:
    scene = MagicMock()
    play_sfx(scene, "pop")
    args, kwargs = scene.add_sound.call_args
    assert Path(args[0]).name == "pop.wav"
    assert kwargs["gain"] == SFX_GAIN_DB


def test_play_sfx_rejects_music_name() -> None:
    with pytest.raises(KeyError):
        play_sfx(MagicMock(), "music_bed")


def test_filter_with_effects_mixes_without_normalizing() -> None:
    graph = build_filter(has_audio=True, duration=45.0, music_gain_db=-22.0)
    assert "amix=inputs=2:duration=first:normalize=0" in graph
    assert "loudnorm" not in graph
    assert f"alimiter=limit={PEAK_LIMIT}:level=0" in graph
    assert "volume=-22.0dB" in graph
    assert "afade=t=out:st=42.500" in graph
    # Pad the effects track so the bed plays to the end of the video.
    assert "apad=whole_dur=45.000" in graph


def test_filter_without_effects_uses_music_only() -> None:
    graph = build_filter(has_audio=False, duration=30.0, music_gain_db=-22.0)
    assert "amix" not in graph
    assert graph.endswith("[a]")
