"""Visual defaults for Manim scenes and matching HTML explanations.

Importing this module does not change Manim's global defaults.
"""

from manim import (
    UP,
    MathTex,
    Mobject,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
)

# Semantic colors. Keep these meanings consistent within a topic.
BACKGROUND = "#0B1020"
SURFACE = "#151E32"
TEXT = "#F1F5F9"
MUTED = "#A8B3C7"
BORDER = "#64748B"
ACCENT = "#FBBF24"
SUCCESS = "#6EE7B7"
ERROR = "#FDA4AF"
ENTITY_A = "#7DD3FC"
ENTITY_B = "#C4B5FD"
ENTITY_C = "#FDBA74"
ENTITY_COLORS = (ENTITY_A, ENTITY_B, ENTITY_C)

CSS_VARIABLES: dict[str, str] = {
    "--bg": BACKGROUND,
    "--surface": SURFACE,
    "--text": TEXT,
    "--muted": MUTED,
    "--border": BORDER,
    "--accent": ACCENT,
    "--success": SUCCESS,
    "--error": ERROR,
    "--entity-a": ENTITY_A,
    "--entity-b": ENTITY_B,
    "--entity-c": ENTITY_C,
}

FONT = "Arial"
TITLE_SIZE = 44
BODY_SIZE = 30
LABEL_SIZE = 24
MATH_SIZE = 36

# Spacing uses Manim scene units; durations use seconds.
MARGIN = 0.5
GAP = 0.3
STROKE_WIDTH = 2.0
FILL_OPACITY = 0.15
TRANSITION_TIME = 0.6
STEP_TIME = 1.0
READ_PAUSE = 1.5


def apply_theme(scene: Scene) -> None:
    """Set the background without changing global text or animation defaults."""
    setattr(scene.camera, "background_color", BACKGROUND)


def text(
    content: str,
    *,
    font_size: float = BODY_SIZE,
    color: str = TEXT,
    weight: str = "NORMAL",
) -> Text:
    """Create readable text with the project font and foreground color."""
    return Text(content, font=FONT, font_size=font_size, color=color, weight=weight)


def math(
    expression: str, *, font_size: float = MATH_SIZE, color: str = TEXT
) -> MathTex:
    """Create a LaTeX equation using the project's size and foreground color."""
    return MathTex(expression, font_size=font_size, color=color)


def title(content: str, *, color: str = TEXT) -> Text:
    """Create a themed title positioned at the top of the scene."""
    return text(content, font_size=TITLE_SIZE, color=color, weight="BOLD").to_edge(
        UP, buff=MARGIN
    )


def panel(
    width: float,
    height: float,
    *,
    fill_color: str = SURFACE,
    fill_opacity: float = FILL_OPACITY,
    stroke_color: str = BORDER,
    stroke_width: float = STROKE_WIDTH,
    corner_radius: float = 0.2,
) -> RoundedRectangle:
    """Create a themed container panel for grouping mobjects."""
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=corner_radius,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
    )


def surrounding_panel(
    mobject: Mobject,
    *,
    buff: float = GAP,
    fill_color: str = SURFACE,
    fill_opacity: float = FILL_OPACITY,
    stroke_color: str = BORDER,
    stroke_width: float = STROKE_WIDTH,
    corner_radius: float = 0.15,
) -> SurroundingRectangle:
    """Create a themed boundary surrounding an active or grouped mobject."""
    return SurroundingRectangle(
        mobject,
        buff=buff,
        color=stroke_color,
        fill_color=fill_color,
        fill_opacity=fill_opacity,
        stroke_width=stroke_width,
        corner_radius=corner_radius,
    )
