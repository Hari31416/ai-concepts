# Audio licenses

Record every sound or music file used in a published video: source, license, and any
attribution the description must carry. Add a row before using a new file.

| Asset                                    | Source                                 | License                                                    | Attribution required |
| ---------------------------------------- | -------------------------------------- | ---------------------------------------------------------- | -------------------- |
| `pop`, `tick`, `whoosh`, `deny`, `chime` | Synthesized by `shared/audio/synth.py` | Original work of this repository (no third-party material) | No                   |
| `music_bed`                              | Synthesized by `shared/audio/synth.py` | Original work of this repository (no third-party material) | No                   |

Generated `.wav` files are not committed. Rebuild them with
`uv run --locked python -m shared.audio`.

Any third-party track (for example from the YouTube Audio Library) goes in this table
with its license text. Audio Library tracks are licensed for YouTube use only, and
CC-BY tracks need credit in the video description.
