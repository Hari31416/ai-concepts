"""Check cleanup boundaries using disposable files, not real topic assets."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.clean_animation import clean_animation


class CleanupTests(unittest.TestCase):
    def test_cleanup_preserves_outputs_and_other_scenes(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            media = root / "media"
            for quality in ("480p15", "1080p60"):
                parent = media / "videos" / "animation" / quality
                for scene in ("Attention", "OtherScene"):
                    cache = parent / "partial_movie_files" / scene
                    cache.mkdir(parents=True)
                    (cache / "clip.mp4").touch()
                (parent / "Attention.mp4").touch()
            final = root / "Attention.mp4"
            final.touch()
            tex = media / "Tex"
            tex.mkdir()
            (tex / "equation.svg").touch()
            outside = root / "outside"
            outside.mkdir()
            linked = media / "videos" / "animation" / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            cache = outside / "partial_movie_files" / "Attention"
            cache.mkdir(parents=True)
            self.assertEqual(
                clean_animation(Path("animation.py"), "Attention", media), 2
            )
            self.assertTrue(final.exists())
            self.assertTrue((tex / "equation.svg").exists())
            self.assertTrue(cache.exists())
            for quality in ("480p15", "1080p60"):
                parent = media / "videos" / "animation" / quality
                self.assertTrue((parent / "Attention.mp4").exists())
                self.assertTrue(
                    (parent / "partial_movie_files" / "OtherScene").exists()
                )
            self.assertEqual(
                clean_animation(Path("animation.py"), "Attention", media), 0
            )

    def test_invalid_scene_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            clean_animation(Path("animation.py"), "../other", Path("media"))
