"""Continuous Batching in LLM Serving.

Contrasts static request-level batching (with head-of-line blocking and idle
bubbles) against iteration-level continuous batching (evicting completed
requests and admitting new ones at each token step).
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circumscribe,
    DashedVMobject,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Transform,
    VGroup,
)
from shared.theme import (
    ACCENT,
    BORDER,
    ENTITY_A,
    ENTITY_B,
    ENTITY_C,
    ERROR,
    LABEL_SIZE,
    MUTED,
    READ_PAUSE,
    SUCCESS,
    SURFACE,
    TEXT,
    TRANSITION_TIME,
    apply_theme,
    panel,
    surrounding_panel,
    text,
    title,
)

# Custom color assignments for distinct requests
COLOR_R1 = ENTITY_A  # Blue
COLOR_R2 = ENTITY_B  # Purple
COLOR_R3 = ENTITY_C  # Orange
COLOR_R4 = "#06b6d4"  # Cyan
COLOR_R5 = "#ec4899"  # Pink
COLOR_BUBBLE = ERROR  # Red for wasted bubble slots


def dashed_box(
    width: float,
    height: float,
    color: str = COLOR_BUBBLE,
    num_dashes: int = 12,
    fill_opacity: float = 0.15,
) -> VGroup:
    """Helper to create a rounded rectangle with dashed outline."""
    base = RoundedRectangle(
        corner_radius=0.08,
        width=width,
        height=height,
        color=color,
        stroke_width=1.5,
        fill_color=color,
        fill_opacity=fill_opacity,
    )
    dashed = DashedVMobject(base, num_dashes=num_dashes)
    bg = RoundedRectangle(
        corner_radius=0.08,
        width=width,
        height=height,
        fill_color=color,
        fill_opacity=fill_opacity,
        stroke_opacity=0,
    )
    return VGroup(bg, dashed)


# -----------------------------------------------------------------------------
# Modular Act Functions
# -----------------------------------------------------------------------------


def run_act1(scene: Scene) -> None:
    """Act 1: The Static Batching Bottleneck & Idle Bubbles."""
    scene_title = title("The Static Batching Bottleneck")
    subtitle = text(
        "Requests locked together until the slowest completes",
        font_size=LABEL_SIZE,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.5)

    # Grid parameters: shifted left so entire batch + queue fit with clear margin
    cell_w, cell_h = 1.05, 0.65
    grid_origin = LEFT * 2.7 + UP * 0.35

    # Timeline header labels t=1..6
    time_labels = VGroup()
    for t in range(1, 7):
        lbl = text(f"t={t}", font_size=LABEL_SIZE - 4, color=MUTED)
        lbl.move_to(grid_origin + RIGHT * ((t - 1) * cell_w) + UP * 0.55)
        time_labels.add(lbl)

    # Request labels on the left
    req_configs = [
        ("R1 (2 toks)", COLOR_R1),
        ("R2 (4 toks)", COLOR_R2),
        ("R3 (6 toks)", COLOR_R3),
    ]
    row_labels = VGroup()
    for i, (name, col) in enumerate(req_configs):
        lbl = text(name, font_size=LABEL_SIZE - 2, color=col, weight="BOLD")
        lbl.move_to(grid_origin + LEFT * 1.35 + DOWN * (i * (cell_h + 0.15)))
        row_labels.add(lbl)

    # Build cells
    token_cells = VGroup()
    bubble_cells = VGroup()

    # R1: 2 active tokens, 4 bubble slots
    for t in range(1, 7):
        center = grid_origin + RIGHT * ((t - 1) * cell_w)
        if t == 1:
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=COLOR_R1,
                fill_opacity=0.4,
                stroke_color=COLOR_R1,
                stroke_width=2,
            ).move_to(center)
            txt = text("tok 1", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))
        elif t == 2:
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=SUCCESS,
                fill_opacity=0.5,
                stroke_color=SUCCESS,
                stroke_width=2,
            ).move_to(center)
            txt = text("<eos>", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))
        else:
            db = dashed_box(
                cell_w - 0.08, cell_h, color=COLOR_BUBBLE, num_dashes=10
            ).move_to(center)
            txt = text("idle", font_size=LABEL_SIZE - 6, color=COLOR_BUBBLE).move_to(
                center
            )
            bubble_cells.add(VGroup(db, txt))

    # R2: 4 active tokens, 2 bubble slots
    for t in range(1, 7):
        center = grid_origin + RIGHT * ((t - 1) * cell_w) + DOWN * (cell_h + 0.15)
        if t in (1, 2, 3):
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=COLOR_R2,
                fill_opacity=0.4,
                stroke_color=COLOR_R2,
                stroke_width=2,
            ).move_to(center)
            txt = text(f"tok {t}", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))
        elif t == 4:
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=SUCCESS,
                fill_opacity=0.5,
                stroke_color=SUCCESS,
                stroke_width=2,
            ).move_to(center)
            txt = text("<eos>", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))
        else:
            db = dashed_box(
                cell_w - 0.08, cell_h, color=COLOR_BUBBLE, num_dashes=10
            ).move_to(center)
            txt = text("idle", font_size=LABEL_SIZE - 6, color=COLOR_BUBBLE).move_to(
                center
            )
            bubble_cells.add(VGroup(db, txt))

    # R3: 6 active tokens (slowest sequence)
    for t in range(1, 7):
        center = grid_origin + RIGHT * ((t - 1) * cell_w) + DOWN * (2 * (cell_h + 0.15))
        if t < 6:
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=COLOR_R3,
                fill_opacity=0.4,
                stroke_color=COLOR_R3,
                stroke_width=2,
            ).move_to(center)
            txt = text(f"tok {t}", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))
        else:
            c = RoundedRectangle(
                width=cell_w - 0.08,
                height=cell_h,
                corner_radius=0.1,
                fill_color=SUCCESS,
                fill_opacity=0.5,
                stroke_color=SUCCESS,
                stroke_width=2,
            ).move_to(center)
            txt = text("<eos>", font_size=LABEL_SIZE - 4, color=TEXT).move_to(center)
            token_cells.add(VGroup(c, txt))

    # Surrounding container for the active batch
    # Width 6.6 covers the 6 columns cleanly (X in [-3.375, +3.225])
    batch_box = panel(
        width=6.6,
        height=3.1,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(grid_origin + RIGHT * 2.625 + DOWN * 0.75)
    batch_label = text(
        "Active Static Batch (Size = 3)",
        font_size=LABEL_SIZE - 2,
        color=TEXT,
        weight="BOLD",
    ).next_to(batch_box, UP, buff=0.1)

    # Right Side: Blocked Queue Container
    # Positioned at X = 4.85, width 2.3 (left edge X = +3.70, 0.475 gap from batch)
    queue_box = panel(
        width=2.3,
        height=3.1,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(RIGHT * 4.85 + DOWN * 0.75)
    queue_label = text(
        "Waiting Queue",
        font_size=LABEL_SIZE - 2,
        color=TEXT,
        weight="BOLD",
    ).next_to(queue_box, UP, buff=0.1)

    # Queued items
    q_item1 = RoundedRectangle(
        width=2.0,
        height=0.6,
        corner_radius=0.1,
        fill_color=COLOR_R4,
        fill_opacity=0.3,
        stroke_color=COLOR_R4,
        stroke_width=1.5,
    ).move_to(queue_box.get_center() + UP * 0.6)
    q_text1 = text("R4 (Blocked)", font_size=LABEL_SIZE - 4, color=TEXT).move_to(
        q_item1
    )
    q1_group = VGroup(q_item1, q_text1)

    q_item2 = RoundedRectangle(
        width=2.0,
        height=0.6,
        corner_radius=0.1,
        fill_color=COLOR_R5,
        fill_opacity=0.3,
        stroke_color=COLOR_R5,
        stroke_width=1.5,
    ).move_to(queue_box.get_center() + DOWN * 0.3)
    q_text2 = text("R5 (Blocked)", font_size=LABEL_SIZE - 4, color=TEXT).move_to(
        q_item2
    )
    q2_group = VGroup(q_item2, q_text2)

    # Reveal Batch structure
    scene.play(
        FadeIn(batch_box),
        FadeIn(batch_label),
        FadeIn(queue_box),
        FadeIn(queue_label),
        FadeIn(row_labels),
        FadeIn(time_labels),
        run_time=TRANSITION_TIME,
    )
    scene.wait(0.4)

    # Animate active token generation
    scene.play(
        LaggedStart(*(FadeIn(c) for c in token_cells), lag_ratio=0.03),
        run_time=1.2,
    )
    scene.wait(0.4)

    # Reveal idle bubbles appearing
    scene.play(
        LaggedStart(*(FadeIn(b) for b in bubble_cells), lag_ratio=0.04),
        FadeIn(q1_group),
        FadeIn(q2_group),
        run_time=1.0,
    )
    scene.wait(0.6)

    # Callout highlighting bubble waste
    waste_callout = text(
        "6 of 18 Batch Slots Wasted as Idle Bubbles (33% GPU Waste)!",
        font_size=LABEL_SIZE - 2,
        color=ERROR,
        weight="BOLD",
    ).move_to(DOWN * 2.85)

    scene.play(
        Circumscribe(bubble_cells, color=ERROR, buff=0.1, run_time=1.2),
        FadeIn(waste_callout, shift=UP * 0.2),
    )
    scene.wait(1.4)


def run_act2(scene: Scene) -> None:
    """Act 2: Iteration-Level Continuous Scheduling Mechanics (~26s)."""
    scene_title = title("Iteration-Level Scheduling: Step-by-Step").to_edge(
        UP, buff=0.35
    )
    subtitle = text(
        "Evaluate completion at every token step. Evict finished, admit waiting.",
        font_size=LABEL_SIZE,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.12)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.5)

    # Status callout banner placed at UP * 2.15 (clear space below subtitle and above batch header)
    status_text = text(
        "Iteration t = 2: R1 emits <eos>! Slot 1 completes early.",
        font_size=LABEL_SIZE - 3,
        color=ACCENT,
        weight="BOLD",
    )
    status_badge = panel(
        width=9.6,
        height=0.62,
        fill_color=SURFACE,
        fill_opacity=0.6,
        stroke_color=ACCENT,
        stroke_width=1.5,
    ).move_to(UP * 2.15)
    status_text.move_to(status_badge)
    status_group = VGroup(status_badge, status_text)

    # Active GPU Batch on the left, center at DOWN * 0.25
    batch_frame = panel(
        width=5.0,
        height=2.9,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(LEFT * 2.8 + DOWN * 0.25)
    batch_hdr = text(
        "Active GPU Batch (B = 3)",
        font_size=LABEL_SIZE - 2,
        color=TEXT,
        weight="BOLD",
    ).next_to(batch_frame, UP, buff=0.15)

    # Waiting Queue on the right
    queue_frame = panel(
        width=3.6,
        height=2.9,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(RIGHT * 3.8 + DOWN * 0.25)
    queue_hdr = text(
        "Waiting Queue",
        font_size=LABEL_SIZE - 2,
        color=TEXT,
        weight="BOLD",
    ).next_to(queue_frame, UP, buff=0.15)

    # Initial slots in Active Batch
    s1_box = RoundedRectangle(
        width=4.4,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R1,
        fill_opacity=0.3,
        stroke_color=COLOR_R1,
        stroke_width=2,
    ).move_to(batch_frame.get_center() + UP * 0.82)
    s1_text = text(
        "Slot 1: R1  [tok 1, <eos>]",
        font_size=LABEL_SIZE - 3,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(s1_box)
    slot1 = VGroup(s1_box, s1_text)

    s2_box = RoundedRectangle(
        width=4.4,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R2,
        fill_opacity=0.3,
        stroke_color=COLOR_R2,
        stroke_width=2,
    ).move_to(batch_frame.get_center())
    s2_text = text(
        "Slot 2: R2  [tok 1, tok 2...]",
        font_size=LABEL_SIZE - 3,
        color=TEXT,
    ).move_to(s2_box)
    slot2 = VGroup(s2_box, s2_text)

    s3_box = RoundedRectangle(
        width=4.4,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R3,
        fill_opacity=0.3,
        stroke_color=COLOR_R3,
        stroke_width=2,
    ).move_to(batch_frame.get_center() + DOWN * 0.82)
    s3_text = text(
        "Slot 3: R3  [tok 1, tok 2...]",
        font_size=LABEL_SIZE - 3,
        color=TEXT,
    ).move_to(s3_box)
    slot3 = VGroup(s3_box, s3_text)

    # Queued Requests
    q_r4_box = RoundedRectangle(
        width=3.0,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R4,
        fill_opacity=0.35,
        stroke_color=COLOR_R4,
        stroke_width=2,
    ).move_to(queue_frame.get_center() + UP * 0.45)
    q_r4_txt = text(
        "R4 (Waiting)", font_size=LABEL_SIZE - 3, color=TEXT, weight="BOLD"
    ).move_to(q_r4_box)
    q_r4 = VGroup(q_r4_box, q_r4_txt)

    q_r5_box = RoundedRectangle(
        width=3.0,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R5,
        fill_opacity=0.35,
        stroke_color=COLOR_R5,
        stroke_width=2,
    ).move_to(queue_frame.get_center() + DOWN * 0.45)
    q_r5_txt = text(
        "R5 (Waiting)", font_size=LABEL_SIZE - 3, color=TEXT, weight="BOLD"
    ).move_to(q_r5_box)
    q_r5 = VGroup(q_r5_box, q_r5_txt)

    # Completed tray at bottom
    completed_tray = panel(
        width=5.0,
        height=0.65,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=SUCCESS,
        stroke_width=1.5,
    ).move_to(LEFT * 2.8 + DOWN * 2.45)
    completed_lbl = text(
        "Evicted / Returned to Client",
        font_size=LABEL_SIZE - 4,
        color=SUCCESS,
    ).move_to(completed_tray)
    completed_zone = VGroup(completed_tray, completed_lbl)

    scene.play(
        FadeIn(batch_frame),
        FadeIn(batch_hdr),
        FadeIn(slot1),
        FadeIn(slot2),
        FadeIn(slot3),
        FadeIn(queue_frame),
        FadeIn(queue_hdr),
        FadeIn(q_r4),
        FadeIn(q_r5),
        FadeIn(completed_zone),
        run_time=TRANSITION_TIME,
    )
    scene.wait(0.5)

    # Reveal initial status
    scene.play(FadeIn(status_group))
    scene.play(Circumscribe(slot1, color=SUCCESS, buff=0.08, run_time=1.0))
    scene.wait(0.6)

    # -------------------------------------------------------------------------
    # Transition 1 (t=2 -> 3): R1 evicts, R4 admitted to Slot 1
    # -------------------------------------------------------------------------
    evicted_r1 = text(
        "R1 Completed (2 tokens)",
        font_size=LABEL_SIZE - 4,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(completed_tray)

    # Evict R1
    scene.play(
        slot1.animate.set_opacity(0.0),
        Transform(completed_lbl, evicted_r1),
        run_time=0.8,
    )

    # Vacant slot outline
    vacant_slot1 = dashed_box(4.4, 0.65, color=ACCENT, num_dashes=14).move_to(
        batch_frame.get_center() + UP * 0.82
    )
    vacant_lbl1 = text(
        "Slot 1: Vacant (Admit new request!)",
        font_size=LABEL_SIZE - 4,
        color=ACCENT,
    ).move_to(vacant_slot1)
    vacant1_group = VGroup(vacant_slot1, vacant_lbl1)

    scene.play(FadeIn(vacant1_group))
    scene.wait(0.4)

    # Update status to R4 admission
    status_text_t3 = text(
        "Iteration t = 3: R4 immediately fills Slot 1. Zero idle bubbles!",
        font_size=LABEL_SIZE - 3,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(status_badge)

    # Animate R4 moving into Slot 1
    s1_r4_box = RoundedRectangle(
        width=4.4,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R4,
        fill_opacity=0.35,
        stroke_color=COLOR_R4,
        stroke_width=2,
    ).move_to(batch_frame.get_center() + UP * 0.82)
    s1_r4_text = text(
        "Slot 1: R4  [Prefill -> tok 1]",
        font_size=LABEL_SIZE - 3,
        color=COLOR_R4,
        weight="BOLD",
    ).move_to(s1_r4_box)
    slot1_r4 = VGroup(s1_r4_box, s1_r4_text)

    # Shift remaining queue items up
    scene.play(
        Transform(status_text, status_text_t3),
        FadeOut(vacant1_group),
        Transform(q_r4, slot1_r4),
        q_r5.animate.move_to(queue_frame.get_center() + UP * 0.45),
        run_time=1.2,
    )
    scene.wait(1.0)

    # -------------------------------------------------------------------------
    # Transition 2 (t=4 -> 5): R2 finishes, R5 admitted to Slot 2
    # -------------------------------------------------------------------------
    status_text_t5 = text(
        "Iteration t = 5: R2 completes. R5 admitted to Slot 2 immediately!",
        font_size=LABEL_SIZE - 3,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(status_badge)

    s2_finish_text = text(
        "Slot 2: R2  [4 toks, <eos>]",
        font_size=LABEL_SIZE - 3,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(s2_box)

    scene.play(
        Transform(s2_text, s2_finish_text),
        Circumscribe(slot2, color=SUCCESS, buff=0.08, run_time=0.8),
    )
    scene.wait(0.4)

    evicted_r2 = text(
        "R1, R2 Completed and Returned",
        font_size=LABEL_SIZE - 4,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(completed_tray)

    s2_r5_box = RoundedRectangle(
        width=4.4,
        height=0.65,
        corner_radius=0.10,
        fill_color=COLOR_R5,
        fill_opacity=0.35,
        stroke_color=COLOR_R5,
        stroke_width=2,
    ).move_to(batch_frame.get_center())
    s2_r5_text = text(
        "Slot 2: R5  [Prefill -> tok 1]",
        font_size=LABEL_SIZE - 3,
        color=COLOR_R5,
        weight="BOLD",
    ).move_to(s2_r5_box)
    slot2_r5 = VGroup(s2_r5_box, s2_r5_text)

    empty_queue_txt = text(
        "Queue Empty\n(All admitted!)",
        font_size=LABEL_SIZE - 4,
        color=MUTED,
    ).move_to(queue_frame.get_center())

    scene.play(
        Transform(status_text, status_text_t5),
        Transform(completed_lbl, evicted_r2),
        slot2.animate.set_opacity(0.0),
        Transform(q_r5, slot2_r5),
        FadeIn(empty_queue_txt),
        run_time=1.2,
    )

    # Highlight continuous saturation badge
    saturation_badge = SurroundingRectangle(
        batch_frame, color=SUCCESS, stroke_width=2.5, buff=0.05
    )
    scene.play(FadeIn(saturation_badge))
    scene.wait(1.5)


def run_act3(scene: Scene) -> None:
    """Act 3: Timeline Comparison (Static vs. Continuous Macro Comparison)."""
    scene_title = title("Execution Timelines: Static vs. Continuous")
    subtitle = text(
        "Comparing makespan and latency for 5 requests (B = 3)",
        font_size=LABEL_SIZE,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.5)

    track_w = 9.0
    bar_h = 0.42
    scale_step = track_w / 9.0  # 1.0 Manim unit per step
    x_start = -5.0

    # -------------------------------------------------------------------------
    # Track 1: Static Batching
    # -------------------------------------------------------------------------
    static_hdr = text(
        "Static Batching (Request-Level): 9 Steps",
        font_size=LABEL_SIZE - 1,
        color=ERROR,
        weight="BOLD",
    ).move_to(LEFT * 2.1 + UP * 1.55)

    static_bars = VGroup()
    # Batch 1 (t=0..6): R1 (len 2 + 4 bubble), R2 (len 4 + 2 bubble), R3 (len 6)
    # R1
    r1_act = RoundedRectangle(
        width=2 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R1,
        fill_opacity=0.5,
        stroke_color=COLOR_R1,
        stroke_width=1.5,
    ).move_to([x_start + 1.0 * scale_step, 0.95, 0])
    r1_lbl = text("R1", font_size=LABEL_SIZE - 4, color=TEXT).move_to(r1_act)
    r1_b = dashed_box(4 * scale_step, bar_h, color=COLOR_BUBBLE, num_dashes=10).move_to(
        [x_start + 4.0 * scale_step, 0.95, 0]
    )
    static_bars.add(VGroup(r1_act, r1_lbl, r1_b))

    # R2
    r2_act = RoundedRectangle(
        width=4 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R2,
        fill_opacity=0.5,
        stroke_color=COLOR_R2,
        stroke_width=1.5,
    ).move_to([x_start + 2.0 * scale_step, 0.45, 0])
    r2_lbl = text("R2", font_size=LABEL_SIZE - 4, color=TEXT).move_to(r2_act)
    r2_b = dashed_box(2 * scale_step, bar_h, color=COLOR_BUBBLE, num_dashes=8).move_to(
        [x_start + 5.0 * scale_step, 0.45, 0]
    )
    static_bars.add(VGroup(r2_act, r2_lbl, r2_b))

    # R3
    r3_act = RoundedRectangle(
        width=6 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R3,
        fill_opacity=0.5,
        stroke_color=COLOR_R3,
        stroke_width=1.5,
    ).move_to([x_start + 3.0 * scale_step, -0.05, 0])
    r3_lbl = text("R3", font_size=LABEL_SIZE - 4, color=TEXT).move_to(r3_act)
    static_bars.add(VGroup(r3_act, r3_lbl))

    # Batch 2 (t=6..9): R4 (len 3), R5 (len 3)
    r4_act = RoundedRectangle(
        width=3 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R4,
        fill_opacity=0.5,
        stroke_color=COLOR_R4,
        stroke_width=1.5,
    ).move_to([x_start + 7.5 * scale_step, 0.95, 0])
    r4_lbl = text("R4", font_size=LABEL_SIZE - 4, color=TEXT).move_to(r4_act)
    static_bars.add(VGroup(r4_act, r4_lbl))

    r5_act = RoundedRectangle(
        width=3 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R5,
        fill_opacity=0.5,
        stroke_color=COLOR_R5,
        stroke_width=1.5,
    ).move_to([x_start + 7.5 * scale_step, 0.45, 0])
    r5_lbl = text("R5", font_size=LABEL_SIZE - 4, color=TEXT).move_to(r5_act)
    static_bars.add(VGroup(r5_act, r5_lbl))

    static_group = static_bars
    static_finish_x = x_start + 9 * scale_step
    static_line = Line(
        [static_finish_x, 1.25, 0],
        [static_finish_x, -0.3, 0],
        color=ERROR,
        stroke_width=2.5,
    )
    static_finish_tag = text(
        "9 Steps", font_size=LABEL_SIZE - 4, color=ERROR, weight="BOLD"
    ).next_to(static_line, RIGHT, buff=0.15)

    # -------------------------------------------------------------------------
    # Track 2: Continuous Batching
    # -------------------------------------------------------------------------
    cont_hdr = text(
        "Continuous Batching (Iteration-Level): 7 Steps",
        font_size=LABEL_SIZE - 1,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(LEFT * 1.8 + DOWN * 0.7)

    cont_bars = VGroup()
    # Slot 1: R1 (t=0..2) then R4 (t=2..5)
    c_r1 = RoundedRectangle(
        width=2 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R1,
        fill_opacity=0.5,
        stroke_color=COLOR_R1,
        stroke_width=1.5,
    ).move_to([x_start + 1.0 * scale_step, -1.25, 0])
    c_r1_lbl = text("R1", font_size=LABEL_SIZE - 4, color=TEXT).move_to(c_r1)

    c_r4 = RoundedRectangle(
        width=3 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R4,
        fill_opacity=0.5,
        stroke_color=COLOR_R4,
        stroke_width=1.5,
    ).move_to([x_start + 3.5 * scale_step, -1.25, 0])
    c_r4_lbl = text("R4", font_size=LABEL_SIZE - 4, color=TEXT).move_to(c_r4)
    cont_bars.add(VGroup(c_r1, c_r1_lbl, c_r4, c_r4_lbl))

    # Slot 2: R2 (t=0..4) then R5 (t=4..7)
    c_r2 = RoundedRectangle(
        width=4 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R2,
        fill_opacity=0.5,
        stroke_color=COLOR_R2,
        stroke_width=1.5,
    ).move_to([x_start + 2.0 * scale_step, -1.75, 0])
    c_r2_lbl = text("R2", font_size=LABEL_SIZE - 4, color=TEXT).move_to(c_r2)

    c_r5 = RoundedRectangle(
        width=3 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R5,
        fill_opacity=0.5,
        stroke_color=COLOR_R5,
        stroke_width=1.5,
    ).move_to([x_start + 5.5 * scale_step, -1.75, 0])
    c_r5_lbl = text("R5", font_size=LABEL_SIZE - 4, color=TEXT).move_to(c_r5)
    cont_bars.add(VGroup(c_r2, c_r2_lbl, c_r5, c_r5_lbl))

    # Slot 3: R3 (t=0..6)
    c_r3 = RoundedRectangle(
        width=6 * scale_step,
        height=bar_h,
        corner_radius=0.06,
        fill_color=COLOR_R3,
        fill_opacity=0.5,
        stroke_color=COLOR_R3,
        stroke_width=1.5,
    ).move_to([x_start + 3.0 * scale_step, -2.25, 0])
    c_r3_lbl = text("R3", font_size=LABEL_SIZE - 4, color=TEXT).move_to(c_r3)
    cont_bars.add(VGroup(c_r3, c_r3_lbl))

    cont_group = cont_bars
    cont_finish_x = x_start + 7 * scale_step
    cont_line = Line(
        [cont_finish_x, -0.95, 0],
        [cont_finish_x, -2.48, 0],
        color=SUCCESS,
        stroke_width=2.5,
    )
    cont_finish_tag = text(
        "7 Steps", font_size=LABEL_SIZE - 4, color=SUCCESS, weight="BOLD"
    ).next_to(cont_line, RIGHT, buff=0.15)

    # Animate top static track
    scene.play(FadeIn(static_hdr), FadeIn(static_group), run_time=1.0)
    scene.play(FadeIn(static_line), FadeIn(static_finish_tag))
    scene.wait(0.6)

    # Animate bottom continuous track
    scene.play(FadeIn(cont_hdr), FadeIn(cont_group), run_time=1.0)
    scene.play(FadeIn(cont_line), FadeIn(cont_finish_tag))
    scene.wait(1.0)

    # Delta comparison banner with 2 wrapped lines (prevents text overflow)
    delta_t1 = text(
        "Key Takeaway: Total execution time shortened by 22% (7 steps vs. 9)",
        font_size=LABEL_SIZE - 2,
        color=ACCENT,
        weight="BOLD",
    )
    delta_t2 = text(
        "Queued request R4 finishes in 5 steps instead of waiting until step 9!",
        font_size=LABEL_SIZE - 4,
        color=TEXT,
    )
    delta_content = VGroup(delta_t1, delta_t2).arrange(DOWN, buff=0.1)
    delta_banner = surrounding_panel(
        delta_content,
        buff=0.22,
        fill_color=SURFACE,
        fill_opacity=0.7,
        stroke_color=ACCENT,
        stroke_width=2,
    ).move_to(DOWN * 3.20)
    delta_content.move_to(delta_banner)
    delta_group = VGroup(delta_banner, delta_content)

    scene.play(FadeIn(delta_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 0.5)


def run_act4(scene: Scene) -> None:
    """Act 4: Throughput & Latency Gains."""
    scene_title = title("Serving Performance Impact")
    subtitle = text(
        "Why modern engines (vLLM, TensorRT-LLM, TGI) use continuous batching",
        font_size=LABEL_SIZE,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.5)

    # 3 Summary Cards with comfortable width (4.0) and padding
    card_w, card_h = 4.0, 3.2
    card_y = DOWN * 0.35

    # Card 1: GPU Saturation
    c1 = panel(
        card_w,
        card_h,
        fill_color=SURFACE,
        fill_opacity=0.35,
        stroke_color=BORDER,
    ).move_to(LEFT * 4.2 + card_y)
    c1_title = text(
        "GPU Saturation",
        font_size=LABEL_SIZE - 3,
        color=ENTITY_A,
        weight="BOLD",
    ).move_to(c1.get_top() + DOWN * 0.4)
    c1_stat1 = text(
        "Static:  67% Active", font_size=LABEL_SIZE - 4, color=ERROR
    ).move_to(c1.get_center() + UP * 0.5)
    c1_stat2 = text(
        "Continuous:  95%+ Active",
        font_size=LABEL_SIZE - 4,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(c1.get_center() + DOWN * 0.1)
    c1_desc = text(
        "Idle bubble padding\neliminated completely",
        font_size=LABEL_SIZE - 6,
        color=MUTED,
    ).move_to(c1.get_bottom() + UP * 0.6)
    card1_group = VGroup(c1, c1_title, c1_stat1, c1_stat2, c1_desc)

    # Card 2: Queue Latency
    c2 = panel(
        card_w,
        card_h,
        fill_color=SURFACE,
        fill_opacity=0.35,
        stroke_color=BORDER,
    ).move_to(card_y)
    c2_title = text(
        "Queue Wait (TTFT)",
        font_size=LABEL_SIZE - 3,
        color=ENTITY_B,
        weight="BOLD",
    ).move_to(c2.get_top() + DOWN * 0.4)
    c2_stat1 = text(
        "Static:  6 Steps Delay", font_size=LABEL_SIZE - 4, color=ERROR
    ).move_to(c2.get_center() + UP * 0.5)
    c2_stat2 = text(
        "Continuous:  0 Steps Delay",
        font_size=LABEL_SIZE - 4,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(c2.get_center() + DOWN * 0.1)
    c2_desc = text(
        "No head-of-line blocking\nfor incoming requests",
        font_size=LABEL_SIZE - 6,
        color=MUTED,
    ).move_to(c2.get_bottom() + UP * 0.6)
    card2_group = VGroup(c2, c2_title, c2_stat1, c2_stat2, c2_desc)

    # Card 3: System Throughput
    c3 = panel(
        card_w,
        card_h,
        fill_color=SURFACE,
        fill_opacity=0.35,
        stroke_color=BORDER,
    ).move_to(RIGHT * 4.2 + card_y)
    c3_title = text(
        "Serving Throughput",
        font_size=LABEL_SIZE - 3,
        color=ENTITY_C,
        weight="BOLD",
    ).move_to(c3.get_top() + DOWN * 0.4)
    c3_stat1 = text(
        "Static:  1.0x Baseline", font_size=LABEL_SIZE - 4, color=MUTED
    ).move_to(c3.get_center() + UP * 0.5)
    c3_stat2 = text(
        "Continuous:  2.3x Gain",
        font_size=LABEL_SIZE - 4,
        color=ACCENT,
        weight="BOLD",
    ).move_to(c3.get_center() + DOWN * 0.1)
    c3_desc = text(
        "2x to 4x throughput\nincrease in production",
        font_size=LABEL_SIZE - 6,
        color=MUTED,
    ).move_to(c3.get_bottom() + UP * 0.6)
    card3_group = VGroup(c3, c3_title, c3_stat1, c3_stat2, c3_desc)

    scene.play(
        LaggedStart(
            FadeIn(card1_group, shift=UP * 0.2),
            FadeIn(card2_group, shift=UP * 0.2),
            FadeIn(card3_group, shift=UP * 0.2),
            lag_ratio=0.2,
        ),
        run_time=1.4,
    )
    scene.wait(0.8)

    # Bottom summary punchline
    summary_txt = text(
        "Continuous Batching transforms LLM serving\nfrom batch-bound to compute-bound.",
        font_size=LABEL_SIZE - 2,
        color=TEXT,
        weight="BOLD",
    )
    summary_box = surrounding_panel(
        summary_txt,
        buff=0.22,
        fill_color=SURFACE,
        fill_opacity=0.6,
        stroke_color=BORDER,
    ).move_to(DOWN * 2.85)
    summary_txt.move_to(summary_box)
    summary_group = VGroup(summary_box, summary_txt)

    scene.play(FadeIn(summary_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 1.0)


# -----------------------------------------------------------------------------
# Scene Classes
# -----------------------------------------------------------------------------


class StaticBatchingWasteScene(Scene):
    """Act 1: The Static Batching Bottleneck & Idle Bubbles (~18s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act1(self)


class ContinuousBatchingMechanismScene(Scene):
    """Act 2: Iteration-Level Scheduling Mechanics (~22s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act2(self)


class TimelineComparisonScene(Scene):
    """Act 3: Timeline Comparison (~20s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act3(self)


class ThroughputLatencyGainsScene(Scene):
    """Act 4: Throughput & Latency Gains (~16s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act4(self)


class ContinuousBatching(Scene):
    """Master Consolidated Scene (~75s)."""

    def construct(self) -> None:
        apply_theme(self)

        # Act 1
        run_act1(self)
        self.play(FadeOut(*self.mobjects), run_time=TRANSITION_TIME)
        self.wait(0.3)

        # Act 2
        run_act2(self)
        self.play(FadeOut(*self.mobjects), run_time=TRANSITION_TIME)
        self.wait(0.3)

        # Act 3
        run_act3(self)
        self.play(FadeOut(*self.mobjects), run_time=TRANSITION_TIME)
        self.wait(0.3)

        # Act 4
        run_act4(self)
