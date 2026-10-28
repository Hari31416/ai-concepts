"""Test shared theme tokens and visual primitives."""

from unittest.mock import MagicMock

from manim import RoundedRectangle, SurroundingRectangle, Text

from shared import theme


def test_theme_color_tokens() -> None:
    assert theme.BACKGROUND == "#0B1020"
    assert theme.SURFACE == "#151E32"
    assert theme.TEXT == "#F1F5F9"
    assert theme.MUTED == "#A8B3C7"
    assert theme.BORDER == "#64748B"
    assert theme.ACCENT == "#FBBF24"
    assert len(theme.ENTITY_COLORS) == 3


def test_css_variables_sync() -> None:
    assert theme.CSS_VARIABLES["--bg"] == theme.BACKGROUND
    assert theme.CSS_VARIABLES["--surface"] == theme.SURFACE
    assert theme.CSS_VARIABLES["--text"] == theme.TEXT
    assert theme.CSS_VARIABLES["--border"] == theme.BORDER


def test_apply_theme() -> None:
    mock_scene = MagicMock()
    mock_scene.camera.background_color = None
    theme.apply_theme(mock_scene)
    assert mock_scene.camera.background_color == theme.BACKGROUND


def test_panel_creation() -> None:
    p = theme.panel(4.0, 2.0)
    assert isinstance(p, RoundedRectangle)
    assert p.width == 4.0
    assert p.height == 2.0


def test_surrounding_panel_creation() -> None:
    t = Text("Attention")
    sp = theme.surrounding_panel(t)
    assert isinstance(sp, SurroundingRectangle)


def test_title_creation() -> None:
    t = theme.title("Overview")
    assert isinstance(t, Text)
    assert t.text == "Overview"
