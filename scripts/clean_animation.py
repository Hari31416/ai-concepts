"""Remove one animation's partial movie caches while preserving its outputs."""

import argparse
from pathlib import Path
import shutil


def clean_animation(source: Path, scene: str, media: Path) -> int:
    """Remove partial clips for a scene across cached quality presets."""
    if not scene.isidentifier():
        raise ValueError("Scene must be a Python class name")
    root = media.resolve()
    videos = root / "videos" / source.stem
    if not videos.is_dir() or videos.is_symlink():
        return 0
    removed = 0
    for quality in videos.iterdir():
        candidate = quality / "partial_movie_files" / scene
        if not candidate.is_dir() or candidate.is_symlink():
            continue
        if candidate.resolve() != candidate or not candidate.is_relative_to(root):
            continue
        shutil.rmtree(candidate)
        removed += 1
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("scene")
    parser.add_argument("--media", required=True, type=Path)
    args = parser.parse_args()
    removed = clean_animation(args.source, args.scene, args.media)
    print(f"Removed {removed} partial movie cache directories for {args.scene}.")


if __name__ == "__main__":
    main()
