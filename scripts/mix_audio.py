"""Mix a quiet music bed under a rendered video's sound effects with ffmpeg.

The video keeps its own audio (Manim's `add_sound` cues). The music is looped to the
video length, faded in and out, set below the effects, and the mix is peak-limited.
There is no loudness normalization: with no voice, normalizing would push the quiet
bed up to full level. Levels are in dBFS.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from shared.audio import MUSIC_NAME, asset_path

# The bed peaks at -3 dBFS; at -13 dB it plays near -26 LUFS, about 10 dB under the
# effects (which peak near -7 dBFS after their -4 dB gain).
MUSIC_GAIN_DB = -14.0
FADE_IN = 1.5
FADE_OUT = 2.5
PEAK_LIMIT = 0.89  # -1 dBFS ceiling
DUCK_THRESHOLD = 0.1  # linear, about -20 dBFS
DUCK_RATIO = 2.5
DUCK_ATTACK_MS = 15
DUCK_RELEASE_MS = 400


def build_filter(*, has_audio: bool, duration: float, music_gain_db: float) -> str:
    """Return the ffmpeg `-filter_complex` graph (music is input 1)."""
    fade_out_start = max(0.0, duration - FADE_OUT)
    music = (
        f"[1:a]atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d={FADE_IN},afade=t=out:st={fade_out_start:.3f}:d={FADE_OUT},"
        f"volume={music_gain_db}dB,aformat=channel_layouts=stereo[m]"
    )
    if not has_audio:
        return f"{music};[m]alimiter=limit={PEAK_LIMIT}:level=0[a]"
    # Effects go to both the mix and a sidechain: the bed dips a few dB under each
    # effect so it stays clear, then swells back (about 5 dB at the effects' peaks).
    return (
        f"{music};[0:a]aformat=channel_layouts=stereo,"
        f"apad=whole_dur={duration:.3f},asplit=2[s][k];"
        f"[m][k]sidechaincompress=threshold={DUCK_THRESHOLD}:ratio={DUCK_RATIO}:"
        f"attack={DUCK_ATTACK_MS}:release={DUCK_RELEASE_MS}[d];"
        f"[s][d]amix=inputs=2:duration=first:normalize=0,"
        f"alimiter=limit={PEAK_LIMIT}:level=0[a]"
    )


def probe(video: Path) -> tuple[float, bool]:
    """Return (duration seconds, has audio stream) using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(result.stdout)
    streams = [stream["codec_type"] for stream in info.get("streams", [])]
    return float(info["format"]["duration"]), "audio" in streams


def mix(video: Path, output: Path, music: Path, music_gain_db: float) -> None:
    """Write `output` with the music bed mixed under the video's own audio."""
    duration, has_audio = probe(video)
    graph = build_filter(
        has_audio=has_audio, duration=duration, music_gain_db=music_gain_db
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(video),
            "-stream_loop",
            "-1",
            "-i",
            str(music),
            "-filter_complex",
            graph,
            "-map",
            "0:v",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{duration:.3f}",
            str(output),
        ],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--music", type=Path, default=None)
    parser.add_argument("--music-gain", type=float, default=MUSIC_GAIN_DB)
    args = parser.parse_args(argv)
    if not args.video.is_file():
        print(f"Video not found: {args.video}", file=sys.stderr)
        return 1
    if args.output.resolve() == args.video.resolve():
        print("Output must differ from the input video.", file=sys.stderr)
        return 1
    mix(args.video, args.output, args.music or asset_path(MUSIC_NAME), args.music_gain)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
