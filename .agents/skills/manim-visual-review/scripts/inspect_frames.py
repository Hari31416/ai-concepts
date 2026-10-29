"""Extract full-resolution video frames and timestamped contact sheets locally."""

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageOps


def run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout


def sample_times(
    duration: float,
    fps: float,
    at: list[float] | None,
    start: float,
    end: float | None,
    every: float | None,
    max_frames: int,
) -> list[float]:
    """Choose seek positions, including the ending when sampling a range."""
    if max_frames < 1:
        raise ValueError("max-frames must be positive")
    if at is not None:
        if every is not None or start != 0 or end is not None:
            raise ValueError("Use --at alone, or a --start/--end/--every range")
        times = sorted(set(at))
        if not times or any(
            not math.isfinite(t) or t < 0 or t >= duration for t in times
        ):
            raise ValueError("Every timestamp must be finite and inside the video")
    else:
        stop = min(duration - 1 / fps, end if end is not None else duration)
        if (
            not math.isfinite(start)
            or not math.isfinite(stop)
            or not 0 <= start <= stop
        ):
            raise ValueError("Range must be finite and inside the video")
        if end is not None and end > duration:
            raise ValueError("End is beyond the video duration")
        interval = every if every is not None else max((stop - start) / 11, 1 / fps)
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("every must be finite and positive")
        count = math.floor((stop - start) / interval) + 1
        if count > max_frames:
            raise ValueError("Too many frames; narrow the range or increase --every")
        times = [start + i * interval for i in range(count)]
        if stop - times[-1] > 0.000001:
            times.append(stop)
    if len(times) > max_frames:
        raise ValueError("Too many frames; raise --max-frames explicitly if needed")
    return times


def inspect(
    video: Path,
    output: Path,
    *,
    at: list[float] | None = None,
    start: float = 0,
    end: float | None = None,
    every: float | None = None,
    max_frames: int = 120,
) -> Path:
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise ValueError(f"Install {executable} and make it available on PATH")
    video = video.resolve(strict=True)
    metadata = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,avg_frame_rate,duration:format=duration",
                "-of",
                "json",
                str(video),
            ]
        )
    )
    stream = metadata["streams"][0]
    duration = float(stream.get("duration") or metadata["format"]["duration"])
    numerator, denominator = stream["avg_frame_rate"].split("/")
    fps = float(numerator) / float(denominator)
    if (
        not math.isfinite(duration)
        or duration <= 0
        or not math.isfinite(fps)
        or fps <= 0
    ):
        raise ValueError("Video must have a positive duration and frame rate")
    times = sample_times(duration, fps, at, start, end, every, max_frames)
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory is not empty; choose a new review directory")
    output.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, str | float]] = []
    for index, timestamp in enumerate(times):
        filename = f"frame-{index:03d}-{timestamp:.6f}s.png"
        run(
            [
                "ffmpeg",
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp:.9f}",
                "-i",
                str(video),
                "-map",
                "0:v:0",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(output / filename),
            ]
        )
        if not (output / filename).is_file():
            raise ValueError(f"No frame decoded at {timestamp:.6f}s")
        frames.append({"seek_seconds": timestamp, "image": filename})
    sheets: list[str] = []
    for offset in range(0, len(frames), 12):
        batch = frames[offset : offset + 12]
        sheet = Image.new("RGB", (1152, math.ceil(len(batch) / 3) * 246), "#101828")
        draw = ImageDraw.Draw(sheet)
        for index, frame in enumerate(batch):
            x, y = index % 3 * 384, index // 3 * 246
            with Image.open(output / str(frame["image"])) as original:
                thumb = ImageOps.contain(original.convert("RGB"), (384, 216))
                sheet.paste(
                    thumb, (x + (384 - thumb.width) // 2, y + (216 - thumb.height) // 2)
                )
            draw.text(
                (x + 8, y + 220), f"{float(frame['seek_seconds']):.3f}s", fill="white"
            )
        name = f"contact-{offset // 12 + 1:02d}.png"
        sheet.save(output / name)
        sheets.append(name)
    manifest = output / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "video": str(video),
                "duration_seconds": duration,
                "width": stream["width"],
                "height": stream["height"],
                "fps": fps,
                "timestamp_note": "Requested seek positions, not exact decoded presentation timestamps.",
                "frames": frames,
                "contact_sheets": sheets,
            },
            indent=2,
        )
        + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--at", nargs="+", type=float)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--every", type=float)
    parser.add_argument("--max-frames", type=int, default=120)
    args = parser.parse_args()
    try:
        manifest = inspect(
            args.video,
            args.output,
            at=args.at,
            start=args.start,
            end=args.end,
            every=args.every,
            max_frames=args.max_frames,
        )
    except (
        ValueError,
        OSError,
        KeyError,
        IndexError,
        ZeroDivisionError,
        subprocess.CalledProcessError,
    ) as error:
        detail = (
            error.stderr
            if isinstance(error, subprocess.CalledProcessError)
            else str(error)
        )
        parser.exit(1, f"Frame inspection failed: {detail}\n")
    print(manifest)


if __name__ == "__main__":
    main()
