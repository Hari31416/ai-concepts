"""Continuous Batching as a vertical YouTube Short (9:16, ~32 s, captions + SFX).

Run from the repository root:

    make preview FILE=topics/2026/10/continuous-batching/short.py \
        SCENE=ContinuousBatchingShort FORMAT=shorts

Story: static batching wastes 33% of slots as idle bubbles and blocks queued
requests -> iteration-level scheduling evicts finished sequences and admits
waiting ones at every token step -> makespan drops from 9 to 7 steps (22%
faster) and production throughput jumps 2x - 4x (Orca, Yu et al., 2022).
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
    Indicate,
    LaggedStart,
    Line,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    Transform,
    VGroup,
)

from shared.audio import play_sfx
from shared.captions import CaptionTrack
from shared.theme import (
    ACCENT,
    BORDER,
    ENTITY_A,
    ENTITY_B,
    ENTITY_C,
    ERROR,
    MUTED,
    SHORTS_CAPTION_SIZE,
    SHORTS_CAPTION_Y,
    SHORTS_LABEL_SIZE,
    SHORTS_TITLE_SIZE,
    SUCCESS,
    TEXT,
    apply_theme,
    panel,
    text,
)

X0 = 0.0
TITLE_Y = 6.9

COLOR_R1 = ENTITY_A
COLOR_R2 = ENTITY_B
COLOR_R3 = ENTITY_C
COLOR_R4 = "#06b6d4"
COLOR_R5 = "#ec4899"
COLOR_BUBBLE = ERROR


def caption_track(scene: Scene) -> CaptionTrack:
    return CaptionTrack(
        scene,
        position=(X0, SHORTS_CAPTION_Y),
        font_size=SHORTS_CAPTION_SIZE,
        max_chars=30,
    )


def section_label(content: str, y: float, *, color: str = MUTED) -> VGroup:
    return VGroup(text(content, font_size=SHORTS_LABEL_SIZE, color=color)).move_to(
        (X0, y, 0)
    )


def dashed_box(
    width: float,
    height: float,
    *,
    color: str = COLOR_BUBBLE,
    num_dashes: int = 10,
    fill_opacity: float = 0.14,
) -> VGroup:
    """Rounded rectangle with a dashed border for idle or vacant slots."""
    base = RoundedRectangle(
        corner_radius=0.08,
        width=width,
        height=height,
        color=color,
        stroke_width=1.8,
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


def token_cell(
    width: float,
    height: float,
    label: str,
    color: str,
    *,
    is_eos: bool = False,
) -> VGroup:
    """Single decoding step cell inside the static batching grid."""
    cell_color = SUCCESS if is_eos else color
    box = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.08,
        fill_color=cell_color,
        fill_opacity=0.45 if is_eos else 0.35,
        stroke_color=cell_color,
        stroke_width=2,
    )
    lbl = text(label, font_size=20, color=TEXT, weight="BOLD" if is_eos else "NORMAL")
    lbl.move_to(box)
    return VGroup(box, lbl)


def slot_bar(
    width: float,
    height: float,
    label: str,
    color: str,
    *,
    text_color: str = TEXT,
    bold: bool = False,
) -> VGroup:
    """Horizontal slot card for the active batch or waiting queue."""
    box = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.1,
        fill_color=color,
        fill_opacity=0.32,
        stroke_color=color,
        stroke_width=2,
    )
    lbl = text(
        label,
        font_size=26,
        color=text_color,
        weight="BOLD" if bold else "NORMAL",
    ).move_to(box)
    return VGroup(box, lbl)


# -----------------------------------------------------------------------------
# Part 1: Static batching wastes compute and blocks the queue
# -----------------------------------------------------------------------------


def problem(scene: Scene, caps: CaptionTrack) -> Text:
    head = text("Static batching", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    head.move_to((X0, TITLE_Y, 0))

    cell_w, cell_h = 0.86, 0.58
    row_gap = 0.78
    grid_x0 = X0 - 1.55
    grid_y0 = 4.9

    time_labels = VGroup(
        *(
            text(f"t={t}", font_size=22, color=MUTED).move_to(
                (grid_x0 + (t - 1) * cell_w, grid_y0 + 0.58, 0)
            )
            for t in range(1, 7)
        )
    )

    req_meta = (("R1", COLOR_R1, 2), ("R2", COLOR_R2, 4), ("R3", COLOR_R3, 6))
    row_labels = VGroup()
    token_cells = VGroup()
    bubble_cells = VGroup()

    for r_idx, (name, color, length) in enumerate(req_meta):
        y = grid_y0 - r_idx * row_gap
        r_lbl = text(name, font_size=26, color=color, weight="BOLD").move_to(
            (grid_x0 - 0.85, y, 0)
        )
        row_labels.add(r_lbl)
        for t in range(1, 7):
            x = grid_x0 + (t - 1) * cell_w
            if t < length:
                cell = token_cell(cell_w - 0.08, cell_h, f"t{t}", color).move_to(
                    (x, y, 0)
                )
                token_cells.add(cell)
            elif t == length:
                cell = token_cell(
                    cell_w - 0.08, cell_h, "eos", color, is_eos=True
                ).move_to((x, y, 0))
                token_cells.add(cell)
            else:
                db = dashed_box(cell_w - 0.08, cell_h, color=COLOR_BUBBLE).move_to(
                    (x, y, 0)
                )
                idle_lbl = text("idle", font_size=18, color=COLOR_BUBBLE).move_to(
                    (x, y, 0)
                )
                bubble_cells.add(VGroup(db, idle_lbl))

    caps.show("Why do LLM servers waste 33% of GPU compute?")
    scene.play(FadeIn(head), FadeIn(time_labels), FadeIn(row_labels), run_time=0.6)
    play_sfx(scene, "tick")
    scene.play(
        LaggedStart(*(FadeIn(c) for c in token_cells), lag_ratio=0.05),
        run_time=1.2,
    )
    caps.hold()

    caps.show("Short requests finish early, leaving idle padding bubbles.")
    play_sfx(scene, "tick")
    scene.play(
        LaggedStart(*(FadeIn(b) for b in bubble_cells), lag_ratio=0.08),
        run_time=0.9,
    )
    badge = VGroup(
        text("33% wasted", font_size=58, color=ERROR, weight="BOLD"),
        text("illustrative: 6 of 18 slots (B = 3)", font_size=24, color=MUTED),
    ).arrange(DOWN, buff=0.12)
    badge.move_to((X0, 1.8, 0))
    scene.play(
        Circumscribe(bubble_cells, color=ERROR, buff=0.08, run_time=0.9),
        FadeIn(badge, shift=UP * 0.2),
    )
    caps.hold()

    caps.show("New requests stay blocked until the slowest finishes.")
    queue_box = panel(6.2, 1.65, stroke_color=BORDER, fill_opacity=0.25).move_to(
        (X0, -0.45, 0)
    )
    queue_hdr = text(
        "Waiting queue (blocked until t = 6)", font_size=24, color=MUTED
    ).next_to(queue_box, UP, buff=0.12)
    q4 = slot_bar(2.6, 0.72, "R4 (Blocked)", COLOR_R4, bold=True).move_to(
        (X0 - 1.45, -0.45, 0)
    )
    q5 = slot_bar(2.6, 0.72, "R5 (Blocked)", COLOR_R5, bold=True).move_to(
        (X0 + 1.45, -0.45, 0)
    )
    play_sfx(scene, "deny")
    scene.play(
        FadeIn(queue_box),
        FadeIn(queue_hdr),
        FadeIn(q4, shift=UP * 0.15),
        FadeIn(q5, shift=UP * 0.15),
    )
    caps.hold()
    return head


# -----------------------------------------------------------------------------
# Part 2: Iteration-level scheduling (evict & admit per token step)
# -----------------------------------------------------------------------------


def mechanism(scene: Scene, caps: CaptionTrack, head: Text) -> None:
    play_sfx(scene, "whoosh")
    new_head = text("Continuous batching", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    new_head.move_to((X0, TITLE_Y, 0))
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    scene.play(FadeOut(*others), Transform(head, new_head), run_time=0.8)

    step_box = panel(2.8, 0.54, stroke_color=ACCENT, fill_opacity=0.4).move_to(
        (X0, 6.02, 0)
    )
    step_lbl = text("Step t = 2", font_size=28, color=ACCENT, weight="BOLD").move_to(
        step_box
    )

    batch_box = panel(6.4, 3.0, stroke_color=BORDER, fill_opacity=0.25).move_to(
        (X0, 3.5, 0)
    )
    batch_hdr = section_label("Active batch (B = 3)", 5.28)

    slot_y = (4.4, 3.5, 2.6)
    s1 = slot_bar(5.8, 0.68, "Slot 1: R1  [tok 1, <eos>]", COLOR_R1, bold=True).move_to(
        (X0, slot_y[0], 0)
    )
    s2 = slot_bar(5.8, 0.68, "Slot 2: R2  [tok 1, tok 2...]", COLOR_R2).move_to(
        (X0, slot_y[1], 0)
    )
    s3 = slot_bar(5.8, 0.68, "Slot 3: R3  [tok 1, tok 2...]", COLOR_R3).move_to(
        (X0, slot_y[2], 0)
    )

    done_box = panel(6.4, 0.62, stroke_color=SUCCESS, fill_opacity=0.2).move_to(
        (X0, 1.35, 0)
    )
    done_lbl = text("Completed: none yet", font_size=24, color=SUCCESS).move_to(
        done_box
    )

    queue_box = panel(6.4, 1.95, stroke_color=BORDER, fill_opacity=0.25).move_to(
        (X0, -0.7, 0)
    )
    queue_hdr = section_label("Waiting queue", 0.52)
    q4 = slot_bar(5.2, 0.65, "R4 (3 toks, waiting)", COLOR_R4, bold=True).move_to(
        (X0, -0.3, 0)
    )
    q5 = slot_bar(5.2, 0.65, "R5 (3 toks, waiting)", COLOR_R5, bold=True).move_to(
        (X0, -1.12, 0)
    )

    caps.show("Continuous batching schedules at every single token step.")
    scene.play(
        FadeIn(step_box),
        FadeIn(step_lbl),
        FadeIn(batch_hdr),
        FadeIn(batch_box),
        FadeIn(s1),
        FadeIn(s2),
        FadeIn(s3),
        FadeIn(done_box),
        FadeIn(done_lbl),
        FadeIn(queue_hdr),
        FadeIn(queue_box),
        FadeIn(q4),
        FadeIn(q5),
        run_time=0.9,
    )
    caps.hold(extra=-0.3)

    # Evict R1 at t = 2
    caps.show("R1 finishes at step 2 and is evicted immediately.")
    s1_eos = slot_bar(
        5.8,
        0.68,
        "Slot 1: R1  [2 toks, <eos>]",
        SUCCESS,
        text_color=SUCCESS,
        bold=True,
    ).move_to((X0, slot_y[0], 0))
    play_sfx(scene, "tick")
    scene.play(Transform(s1, s1_eos), run_time=0.5)

    vacant1 = dashed_box(5.8, 0.68, color=ACCENT, num_dashes=16).move_to(
        (X0, slot_y[0], 0)
    )
    vacant1_lbl = text("Slot 1: Vacant", font_size=24, color=ACCENT).move_to(vacant1)
    vacant1_group = VGroup(vacant1, vacant1_lbl)
    done_r1 = text(
        "Completed: R1 (2 toks)", font_size=24, color=SUCCESS, weight="BOLD"
    ).move_to(done_box)
    scene.play(
        FadeOut(s1, shift=LEFT * 0.3),
        Transform(done_lbl, done_r1),
        FadeIn(vacant1_group),
        run_time=0.7,
    )
    caps.hold()

    # Admit R4 at t = 3
    caps.show("R4 enters Slot 1 right away with zero bubbles.")
    step_t3 = text("Step t = 3", font_size=28, color=ACCENT, weight="BOLD").move_to(
        step_box
    )
    s1_r4 = slot_bar(5.8, 0.68, "Slot 1: R4  [tok 1]", COLOR_R4, bold=True).move_to(
        (X0, slot_y[0], 0)
    )
    play_sfx(scene, "pop")
    scene.play(
        Transform(step_lbl, step_t3),
        FadeOut(vacant1_group),
        Transform(q4, s1_r4),
        q5.animate.move_to((X0, -0.3, 0)),
        run_time=0.9,
    )
    caps.hold()

    # Evict R2 at t = 4 and admit R5 at t = 5
    caps.show("At step 4, R2 finishes and R5 takes its slot.")
    step_t4 = text("Step t = 4", font_size=28, color=ACCENT, weight="BOLD").move_to(
        step_box
    )
    s2_eos = slot_bar(
        5.8,
        0.68,
        "Slot 2: R2  [4 toks, <eos>]",
        SUCCESS,
        text_color=SUCCESS,
        bold=True,
    ).move_to((X0, slot_y[1], 0))
    play_sfx(scene, "tick")
    scene.play(Transform(step_lbl, step_t4), Transform(s2, s2_eos), run_time=0.55)

    step_t5 = text("Step t = 5", font_size=28, color=SUCCESS, weight="BOLD").move_to(
        step_box
    )
    s2_r5 = slot_bar(5.8, 0.68, "Slot 2: R5  [tok 1]", COLOR_R5, bold=True).move_to(
        (X0, slot_y[1], 0)
    )
    done_r12 = text(
        "Completed: R1, R2", font_size=24, color=SUCCESS, weight="BOLD"
    ).move_to(done_box)
    empty_q = text("Queue empty (all admitted)", font_size=24, color=MUTED).move_to(
        queue_box
    )
    play_sfx(scene, "pop")
    scene.play(
        Transform(step_lbl, step_t5),
        FadeOut(s2, shift=LEFT * 0.3),
        Transform(done_lbl, done_r12),
        Transform(q5, s2_r5),
        FadeIn(empty_q),
        run_time=0.9,
    )
    sat = SurroundingRectangle(batch_box, color=SUCCESS, stroke_width=2.5, buff=0.06)
    scene.play(FadeIn(sat), Indicate(batch_box, color=SUCCESS, scale_factor=1.02))
    caps.hold(extra=0.4)


# -----------------------------------------------------------------------------
# Part 3: The payoff
# -----------------------------------------------------------------------------


def timeline_bar(
    x_start: float,
    step_start: float,
    steps: int,
    scale: float,
    y: float,
    label: str,
    color: str,
) -> VGroup:
    width = steps * scale
    box = RoundedRectangle(
        width=width,
        height=0.42,
        corner_radius=0.06,
        fill_color=color,
        fill_opacity=0.5,
        stroke_color=color,
        stroke_width=1.5,
    ).move_to((x_start + (step_start + steps / 2) * scale, y, 0))
    lbl = text(label, font_size=20, color=TEXT).move_to(box)
    return VGroup(box, lbl)


def payoff(scene: Scene, caps: CaptionTrack, head: Text) -> None:
    new_head = text("Static vs. Continuous", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    new_head.move_to((X0, TITLE_Y, 0))
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    scene.play(FadeOut(*others), Transform(head, new_head), run_time=0.7)

    caps.show("Total time drops from 9 steps to just 7.")
    scale = 0.62
    x_start = X0 - 9 * scale / 2 - 0.35

    static_hdr = text(
        "Static: 9 steps", font_size=28, color=ERROR, weight="BOLD"
    ).move_to((X0, 5.7, 0))
    static_y = (5.1, 4.55, 4.0)
    static_bars = VGroup(
        timeline_bar(x_start, 0, 2, scale, static_y[0], "R1", COLOR_R1),
        dashed_box(4 * scale, 0.42, color=COLOR_BUBBLE, num_dashes=8).move_to(
            (x_start + 4 * scale, static_y[0], 0)
        ),
        timeline_bar(x_start, 6, 3, scale, static_y[0], "R4", COLOR_R4),
        timeline_bar(x_start, 0, 4, scale, static_y[1], "R2", COLOR_R2),
        dashed_box(2 * scale, 0.42, color=COLOR_BUBBLE, num_dashes=6).move_to(
            (x_start + 5 * scale, static_y[1], 0)
        ),
        timeline_bar(x_start, 6, 3, scale, static_y[1], "R5", COLOR_R5),
        timeline_bar(x_start, 0, 6, scale, static_y[2], "R3", COLOR_R3),
    )
    static_line = Line(
        (x_start + 9 * scale, 5.35, 0),
        (x_start + 9 * scale, 3.75, 0),
        color=ERROR,
        stroke_width=2.5,
    )

    cont_hdr = text(
        "Continuous: 7 steps (22% faster)", font_size=28, color=SUCCESS, weight="BOLD"
    ).move_to((X0, 3.1, 0))
    cont_y = (2.5, 1.95, 1.4)
    cont_bars = VGroup(
        timeline_bar(x_start, 0, 2, scale, cont_y[0], "R1", COLOR_R1),
        timeline_bar(x_start, 2, 3, scale, cont_y[0], "R4", COLOR_R4),
        timeline_bar(x_start, 0, 4, scale, cont_y[1], "R2", COLOR_R2),
        timeline_bar(x_start, 4, 3, scale, cont_y[1], "R5", COLOR_R5),
        timeline_bar(x_start, 0, 6, scale, cont_y[2], "R3", COLOR_R3),
    )
    cont_line = Line(
        (x_start + 7 * scale, 2.75, 0),
        (x_start + 7 * scale, 1.15, 0),
        color=SUCCESS,
        stroke_width=2.5,
    )

    scene.play(FadeIn(static_hdr), FadeIn(static_bars), FadeIn(static_line))
    play_sfx(scene, "chime")
    scene.play(FadeIn(cont_hdr), FadeIn(cont_bars), FadeIn(cont_line))
    caps.hold()

    caps.show("In production, serving throughput jumps 2x to 4x.")
    gain = VGroup(
        text("2x - 4x", font_size=84, color=SUCCESS, weight="BOLD"),
        text("serving throughput", font_size=30, color=MUTED),
    ).arrange(DOWN, buff=0.15)
    gain.move_to((X0, -0.5, 0))
    scene.play(FadeIn(gain, shift=UP * 0.2))
    caps.hold(extra=0.8)


class ContinuousBatchingShort(Scene):
    """Vertical Short, about 32 s. Render with FORMAT=shorts."""

    def construct(self) -> None:
        apply_theme(self)
        caps = caption_track(self)
        head = problem(self, caps)
        mechanism(self, caps, head)
        payoff(self, caps, head)
        caps.finish()
