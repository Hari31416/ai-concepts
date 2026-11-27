"""Burned-in captions and a matching `.srt` file for voiceless videos.

Captions carry the narration. `CaptionTrack` shows one caption at a time inside a
pill, waits long enough to read it, and records every cue so the `.srt` always
matches what is on screen. Manim-only parts are kept thin; timing and SRT formatting
are plain Python and unit tested.
"""

import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from manim import (
    FadeIn,
    FadeOut,
    Mobject,
    RoundedRectangle,
    Scene,
    VGroup,
)

from shared.theme import (
    BODY_SIZE,
    CAPTION_MAX_CHARS,
    CAPTION_Y,
    MUTED,
    READ_PAUSE,
    SURFACE,
    TEXT,
    TRANSITION_TIME,
    text,
)

CHARS_PER_SECOND = 15.0
MAX_LINES = 2


@dataclass(frozen=True)
class Cue:
    """One caption: seconds from the start of the video."""

    start: float
    end: float
    text: str


def reading_time(content: str, *, minimum: float = READ_PAUSE) -> float:
    """Seconds a viewer needs to read `content` at about 15 characters per second."""
    return max(minimum, len(content) / CHARS_PER_SECOND)


def wrap_caption(content: str, max_chars: int) -> list[str]:
    """Wrap to at most two lines or raise, so captions never grow past the band."""
    lines = textwrap.wrap(content, width=max_chars, break_on_hyphens=False)
    if len(lines) > MAX_LINES:
        raise ValueError(
            f"Caption needs {len(lines)} lines at {max_chars} chars: {content!r}"
        )
    return lines


def format_timestamp(seconds: float) -> str:
    """SRT timestamp `HH:MM:SS,mmm`."""
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_srt(cues: list[Cue], *, max_chars: int | None = None) -> str:
    """Render cues as SRT. Pass `max_chars` to break lines as on screen."""
    blocks = []
    for number, cue in enumerate(cues, start=1):
        body = "\n".join(wrap_caption(cue.text, max_chars)) if max_chars else cue.text
        blocks.append(
            f"{number}\n"
            f"{format_timestamp(cue.start)} --> {format_timestamp(cue.end)}\n"
            f"{body}\n"
        )
    return "\n".join(blocks)


class CaptionTrack:
    """Shows captions in a scene and records them for `.srt` export.

    Typical beat: `track.show("...")`, play the mechanism, `track.hold()`. Call
    `track.finish()` as the last line of `construct`. For a consolidated video made
    of several scenes, pass `time_offset` (seconds before this scene starts).
    """

    def __init__(
        self,
        scene: Scene,
        *,
        position: tuple[float, float] = (0.0, CAPTION_Y),
        font_size: float = BODY_SIZE,
        max_chars: int = CAPTION_MAX_CHARS,
        time_offset: float = 0.0,
    ) -> None:
        self.scene = scene
        self.position = position
        self.font_size = font_size
        self.max_chars = max_chars
        self.time_offset = time_offset
        self.cues: list[Cue] = []
        self._current: Mobject | None = None
        self._current_text = ""
        self._current_start = 0.0
        self._shown_at = 0.0

    @property
    def current(self) -> Mobject | None:
        """The caption mobject on screen, so scenes can keep it when clearing."""
        return self._current

    def _now(self) -> float:
        return float(self.scene.time) + self.time_offset

    def _build(self, content: str) -> VGroup:
        lines = wrap_caption(content, self.max_chars)
        label = VGroup(
            *(text(line, font_size=self.font_size, color=TEXT) for line in lines)
        ).arrange(direction=(0, -1, 0), buff=0.12)
        pill = RoundedRectangle(
            width=label.width + 0.6,
            height=label.height + 0.4,
            corner_radius=0.2,
            fill_color=SURFACE,
            fill_opacity=0.92,
            stroke_color=MUTED,
            stroke_width=1.5,
        )
        group = VGroup(pill, label)
        label.move_to(pill)
        group.move_to((*self.position, 0.0))
        group.set_z_index(100)
        return group

    def _close_cue(self) -> None:
        if self._current_text:
            self.cues.append(Cue(self._current_start, self._now(), self._current_text))
            self._current_text = ""

    def show(self, content: str, *, run_time: float = TRANSITION_TIME / 2) -> None:
        """Replace the on-screen caption with `content`."""
        new = self._build(content)
        self._close_cue()
        anims: list[Any] = [FadeIn(new)]
        if self._current is not None:
            anims.append(FadeOut(self._current))
        self._current_start = self._now()
        self._shown_at = self._now()
        self.scene.play(*anims, run_time=run_time)
        self._current, self._current_text = new, content

    def hold(self, extra: float = 0.0) -> None:
        """Wait until the current caption has been up for its reading time."""
        remaining = reading_time(self._current_text) - (self._now() - self._shown_at)
        if remaining + extra > 0:
            self.scene.wait(remaining + extra)

    def clear(self, *, run_time: float = TRANSITION_TIME / 2) -> None:
        """Remove the caption and end its cue."""
        if self._current is None:
            return
        self._close_cue()
        self.scene.play(FadeOut(self._current), run_time=run_time)
        self._current = None

    def srt_path(self) -> Path:
        """Next to the rendered movie (`Scene.srt`), or the working dir if none."""
        writer = getattr(getattr(self.scene, "renderer", None), "file_writer", None)
        movie = getattr(writer, "movie_file_path", None)
        base = Path(str(movie)) if movie else Path(type(self.scene).__name__)
        return base.with_suffix(".srt")

    def finish(self, path: Path | None = None) -> Path:
        """End the last cue and write the `.srt`. Call at the end of `construct`."""
        self.clear()
        target = path or self.srt_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(format_srt(self.cues, max_chars=self.max_chars))
        return target
