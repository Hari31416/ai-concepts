"""Sound effects and a music bed for voiceless videos.

Assets are synthesized by `shared.audio.synth` on first use and cached as `.wav`
files next to this module (ignored by Git). Cut-time helpers live here; the final
mix with the music bed is `scripts/mix_audio.py`.
"""

from pathlib import Path
from typing import Protocol

from shared.audio.synth import GENERATORS, write_wav

AUDIO_DIR = Path(__file__).resolve().parent
SFX_NAMES = ("pop", "tick", "whoosh", "deny", "chime")
MUSIC_NAME = "music_bed"

# add_sound gain in dB, applied to a -3 dBFS peak sample. The music bed is mixed
# about 10 dB below the SFX, so cues stay audible without the bed competing.
SFX_GAIN_DB = -4.0


class _SoundScene(Protocol):
    def add_sound(
        self, sound_file: str, time_offset: float = 0, gain: float | None = None
    ) -> None: ...


def asset_path(name: str) -> Path:
    """Return the `.wav` path for `name`, generating it on first use."""
    if name not in GENERATORS:
        raise KeyError(
            f"Unknown audio asset {name!r}; choose from {sorted(GENERATORS)}"
        )
    path = AUDIO_DIR / f"{name}.wav"
    if not path.exists():
        write_wav(path, GENERATORS[name]())
    return path


def play_sfx(scene: _SoundScene, name: str, *, gain: float = SFX_GAIN_DB) -> None:
    """Play a sound effect at the scene's current time."""
    if name not in SFX_NAMES:
        raise KeyError(f"Unknown SFX {name!r}; choose from {SFX_NAMES}")
    scene.add_sound(str(asset_path(name)), gain=gain)
