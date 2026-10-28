"""Visual defaults for Manim scenes and matching HTML explanations.

Importing this module does not change Manim's global defaults.
"""

from manim import MathTex, Scene, Text

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
    scene.camera.background_color = BACKGROUND


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
