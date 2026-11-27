"""Test caption timing, wrapping, and SRT formatting."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shared.captions import (
    CaptionTrack,
    Cue,
    format_srt,
    format_timestamp,
    reading_time,
    wrap_caption,
)
from manim import config

from shared.theme import CAPTION_MAX_CHARS, CONTENT_BOTTOM, READ_PAUSE


def test_reading_time_uses_minimum_for_short_text() -> None:
    assert reading_time("Hi") == READ_PAUSE


def test_reading_time_scales_with_length() -> None:
    assert reading_time("x" * 60) == pytest.approx(4.0)


def test_format_timestamp() -> None:
    assert format_timestamp(0) == "00:00:00,000"
    assert format_timestamp(61.5) == "00:01:01,500"
    assert format_timestamp(3661.007) == "01:01:01,007"


def test_wrap_caption_two_lines_and_no_hyphen_split() -> None:
    lines = wrap_caption("GPU memory is a pool of same-size blocks.", 24)
    assert lines == ["GPU memory is a pool of", "same-size blocks."]


def test_wrap_caption_rejects_three_lines() -> None:
    with pytest.raises(ValueError, match="lines at 20 chars"):
        wrap_caption("word " * 20, 20)


def test_format_srt_numbers_cues_in_order() -> None:
    cues = [Cue(1.0, 3.5, "One"), Cue(3.5, 6.0, "Two")]
    assert format_srt(cues) == (
        "1\n00:00:01,000 --> 00:00:03,500\nOne\n\n"
        "2\n00:00:03,500 --> 00:00:06,000\nTwo\n"
    )


def test_track_records_cues_and_writes_srt(tmp_path: Path) -> None:
    scene = MagicMock()
    clock = {"t": 0.0}
    type(scene).time = property(lambda _self: clock["t"])
    scene.play.side_effect = lambda *a, run_time=1.0, **k: clock.update(
        t=clock["t"] + run_time
    )
    scene.wait.side_effect = lambda seconds: clock.update(t=clock["t"] + seconds)

    track = CaptionTrack(scene, max_chars=30)
    track.show("First caption here.", run_time=0.3)
    track.hold()
    track.show("Second one.", run_time=0.3)
    track.hold()
    target = track.finish(tmp_path / "out.srt")

    first, second = track.cues
    assert first.text == "First caption here."
    assert first.start == 0.0
    assert second.start == pytest.approx(first.end)
    assert second.end > second.start
    assert target.read_text().startswith("1\n00:00:00,000 --> ")


def test_track_time_offset_shifts_cues() -> None:
    scene = MagicMock()
    type(scene).time = property(lambda _self: 0.0)
    track = CaptionTrack(scene, time_offset=10.0)
    track.show("Offset caption.")
    track.clear()
    assert track.cues[0].start == 10.0


def test_default_landscape_caption_fits_inside_frame() -> None:
    track = CaptionTrack(MagicMock())
    two_lines = " ".join(["word"] * 30)[: CAPTION_MAX_CHARS * 2 - 4]
    pill = track._build(two_lines)
    assert pill.get_bottom()[1] > -config.frame_height / 2
    assert pill.get_top()[1] < CONTENT_BOTTOM + 0.2
    assert pill.width < config.frame_width - 1.0
