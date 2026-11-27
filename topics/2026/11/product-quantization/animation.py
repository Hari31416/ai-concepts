"""Product quantization (PQ) for vector search.

Demonstrates:
1. The memory wall: 1B x 512-byte vectors versus 8-byte codes.
2. Split and snap: cut a vector into pieces, replace each with a centroid ID.
3. Why splitting works: codebooks multiply (12 stored -> 64 reachable).
4. Asymmetric distance: one lookup table per query, then only additions per vector.
5. The trade: 64x smaller, cheaper distances, approximate answers.

Each act takes a `CaptionTrack`, so every scene and the consolidated video carry
burned-in captions and write a matching `.srt`.

Every number shown comes from `toy.py` (seed 7, D=6, M=3, K=4).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Axes,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    FadeTransform,
    Indicate,
    LaggedStart,
    Line,
    Scene,
    Square,
    Transform,
    VGroup,
)
from shared.captions import CaptionTrack
from shared.theme import (
    ACCENT,
    BORDER,
    ENTITY_A,
    ENTITY_B,
    ENTITY_C,
    ERROR,
    LABEL_SIZE,
    MUTED,
    SUCCESS,
    TEXT,
    TRANSITION_TIME,
    apply_theme,
    math,
    panel,
    surrounding_panel,
    text,
    title,
)


def _load_toy() -> Any:
    path = Path(__file__).with_name("toy.py")
    spec = importlib.util.spec_from_file_location("product_quantization_toy", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# -----------------------------------------------------------------------------
# Data: computed by the verified reference implementation, not typed in by hand.
# -----------------------------------------------------------------------------

_toy = _load_toy()
DATA, _rng = _toy.make_toy_data()
PQ = _toy.ProductQuantizer.train(DATA, _toy.TOY_M, _toy.TOY_K, _rng)
CODES = PQ.encode(DATA)
M, K = PQ.m, PQ.k

X_IDX = 349  # database vector used in the worked example
X = DATA[X_IDX]
X_CODE = [int(c) for c in CODES[X_IDX]]
X_HAT = PQ.decode(CODES[X_IDX : X_IDX + 1])[0]
QUERY = np.array([0.5, -1.0, 1.2, 0.3, -0.8, 1.1])
LUT = np.round(PQ.lookup_table(QUERY), 2)  # displayed values, 2 decimals
ROW_IDS = [349, 0, 4, 3]  # database rows shown in the lookup scene
assert X_CODE == [0, 0, 3]
assert abs(sum(LUT[m, c] for m, c in enumerate(X_CODE)) - 2.93) < 0.02

# Entity colors: one per subspace, kept across every scene.
COLOR_SUBS = (ENTITY_A, ENTITY_B, ENTITY_C)
SUB_NAMES = ("dims 1-2", "dims 3-4", "dims 5-6")


def at(x: float, y: float) -> tuple[float, float, float]:
    return (x, y, 0.0)


def fmt(value: float) -> str:
    return f"{value:.2f}".replace("-", "−")


def pair_box(
    values: Sequence[float] | np.ndarray,
    color: str,
    *,
    width: float = 1.9,
    font_size: float = 24,
) -> VGroup:
    """A colored box holding one subvector's two numbers."""
    body = panel(
        width,
        0.62,
        fill_color=color,
        fill_opacity=0.18,
        stroke_color=color,
        corner_radius=0.12,
    )
    label = text("   ".join(fmt(v) for v in values), font_size=font_size)
    label.move_to(body)
    return VGroup(body, label)


def id_box(value: int, color: str, size: float = 0.62) -> VGroup:
    body = panel(
        size,
        size,
        fill_color=color,
        fill_opacity=0.25,
        stroke_color=color,
        corner_radius=0.1,
    )
    label = text(str(value), font_size=26, weight="BOLD").move_to(body)
    return VGroup(body, label)


# -----------------------------------------------------------------------------
# Act 1: the memory wall
# -----------------------------------------------------------------------------


def run_memory_wall(scene: Scene, caps: CaptionTrack) -> None:
    head = title("Storing a billion vectors")
    caps.show("A billion vectors need 512 GB. Can we shrink that?")
    scene.play(FadeIn(head, shift=DOWN * 0.2))

    def cells(count: int, side: float, buff: float) -> VGroup:
        return VGroup(
            *[
                Square(
                    side,
                    stroke_color=BORDER,
                    stroke_width=1.5,
                    fill_color=TEXT,
                    fill_opacity=0.15,
                )
                for _ in range(count)
            ]
        ).arrange(RIGHT, buff=buff)

    row = cells(32, 0.22, 0.04).move_to(UP * 1.6)
    row_label = text(
        "one embedding: 128 numbers × 4 bytes = 512 bytes", font_size=LABEL_SIZE
    ).next_to(row, DOWN, buff=0.3)
    scene.play(LaggedStart(*[FadeIn(c) for c in row], lag_ratio=0.03), run_time=1.2)
    scene.play(FadeIn(row_label))
    caps.hold()

    caps.show("Multiply by a billion vectors and RAM runs out.")
    times = text("× 1,000,000,000 vectors", font_size=LABEL_SIZE + 4, color=MUTED)
    times.move_to(UP * 0.2)
    big = text("512 GB", font_size=84, color=ERROR, weight="BOLD").move_to(DOWN * 1.0)
    scene.play(FadeIn(times))
    scene.play(FadeIn(big, scale=0.8))
    caps.hold()

    caps.show("Every search would also have to scan all of it.")
    scene.wait(0.3)
    caps.hold()

    caps.show("Product quantization keeps each vector in 8 bytes.")
    small = cells(8, 0.5, 0.08).move_to(row)
    small_label = text(
        "the same embedding in 8 bytes", font_size=LABEL_SIZE, color=TEXT
    ).next_to(small, DOWN, buff=0.3)
    big_ok = text("8 GB", font_size=84, color=SUCCESS, weight="BOLD").move_to(big)
    scene.play(
        Transform(row, small),
        Transform(row_label, small_label),
        Transform(big, big_ok),
        run_time=1.6,
    )
    caps.hold()

    caps.show("64× smaller. But can distances survive the squeeze?")
    scene.wait(0.3)
    caps.hold(extra=0.5)


# -----------------------------------------------------------------------------
# Act 2: split, then snap
# -----------------------------------------------------------------------------

PANEL_XS = (-4.3, 0.0, 4.3)
BOX_Y = 2.2
PANEL_Y = 0.15
CODE_Y = -1.85


class SubspacePanel(VGroup):
    """2-D scatter of one subspace with its K centroids and their IDs."""

    def __init__(self, j: int) -> None:
        super().__init__()
        color = COLOR_SUBS[j]
        frame = panel(3.8, 3.1, fill_opacity=0.3)
        self.axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            x_length=3.4,
            y_length=2.6,
            tips=False,
            axis_config={
                "stroke_color": BORDER,
                "stroke_width": 1.2,
                "include_ticks": False,
            },
        )
        sub = DATA.reshape(len(DATA), M, -1)[:, j]
        cloud = VGroup(
            *[
                Dot(self.axes.c2p(*p), radius=0.03, color=color).set_opacity(0.4)
                for p in sub[:150]
            ]
        )
        self.centroid_dots: list[Dot] = []
        marks = VGroup()
        for k in range(K):
            c = PQ.codebooks[j][k]
            dot = Dot(
                self.axes.c2p(*c),
                radius=0.12,
                color=color,
                stroke_color=TEXT,
                stroke_width=2,
            )
            tag = text(str(k), font_size=20, weight="BOLD").next_to(
                dot, UP + RIGHT, buff=0.02
            )
            self.centroid_dots.append(dot)
            marks.add(dot, tag)
        group = VGroup(frame, self.axes, cloud, marks).move_to(at(PANEL_XS[j], PANEL_Y))
        self.add(group)

    def point(self, xy: Sequence[float]) -> Any:
        return self.axes.c2p(*xy)


def run_split_and_snap(scene: Scene, caps: CaptionTrack) -> None:
    head = title("Split, then snap each piece")
    scene.play(FadeIn(head, shift=DOWN * 0.2))

    caps.show("Idea: cut the vector into pieces, then compress each.")
    boxes = [pair_box(X[2 * j : 2 * j + 2], COLOR_SUBS[j]) for j in range(M)]
    joined = VGroup(*boxes).arrange(RIGHT, buff=0).move_to(UP * BOX_Y)
    scene.play(FadeIn(joined))
    scene.wait(0.5)
    scene.play(
        *[b.animate.move_to(at(PANEL_XS[j], BOX_Y)) for j, b in enumerate(boxes)]
    )
    caps.hold()

    caps.show("Each piece gets its own small codebook of 4 centroids.")
    panels = [SubspacePanel(j) for j in range(M)]
    scene.play(LaggedStart(*[FadeIn(p) for p in panels], lag_ratio=0.25), run_time=1.5)
    caps.hold(extra=0.5)

    # Each pair becomes a point in its own subspace.
    caps.show("Every piece is a point in its own 2-D space.")
    dots = [Dot(radius=0.1, color=TEXT).move_to(b.get_bottom()) for b in boxes]
    scene.add(*dots)
    scene.play(
        *[
            d.animate.move_to(panels[j].point(X[2 * j : 2 * j + 2]))
            for j, d in enumerate(dots)
        ],
        run_time=1.2,
    )
    caps.hold()

    # Snap to the nearest centroid and record its ID.
    caps.show("Snap each point to its nearest centroid, keep the ID.")
    lines = [
        Line(
            dots[j].get_center(),
            panels[j].centroid_dots[X_CODE[j]].get_center(),
            color=COLOR_SUBS[j],
            stroke_width=3,
        )
        for j in range(M)
    ]
    scene.play(*[Create(ln) for ln in lines], run_time=0.8)
    scene.play(
        *[
            dots[j].animate.move_to(panels[j].centroid_dots[X_CODE[j]].get_center())
            for j in range(M)
        ],
        *[Indicate(panels[j].centroid_dots[X_CODE[j]]) for j in range(M)],
        FadeOut(*lines),
        run_time=1.0,
    )
    caps.hold()

    caps.show(
        f"Stored code [{', '.join(str(c) for c in X_CODE)}]: 6 bits instead of 192."
    )
    ids = [
        id_box(X_CODE[j], COLOR_SUBS[j]).move_to(at(PANEL_XS[j], CODE_Y))
        for j in range(M)
    ]
    scene.play(LaggedStart(*[FadeIn(i, shift=DOWN * 0.2) for i in ids], lag_ratio=0.2))
    caps.hold()

    # Decode: the IDs stand for centroids, so x-hat approximates x.
    caps.show("Decoding joins the centroids into an approximate vector.")
    hat_boxes = [
        pair_box(X_HAT[2 * j : 2 * j + 2], COLOR_SUBS[j]).move_to(boxes[j])
        for j in range(M)
    ]
    scene.play(*[Transform(boxes[j], hat_boxes[j]) for j in range(M)], run_time=1.2)
    caps.hold(extra=0.5)


# -----------------------------------------------------------------------------
# Act 3: why splitting works
# -----------------------------------------------------------------------------


def run_codebook_power(scene: Scene, caps: CaptionTrack) -> None:
    head = title("Why splitting is the trick")
    scene.play(FadeIn(head, shift=DOWN * 0.2))

    caps.show("Why split? Because codebooks multiply.")
    col_x = (-5.3, -3.5, -1.7)
    chips: list[list[VGroup]] = []
    headers = []
    for j in range(M):
        header = text(SUB_NAMES[j], font_size=20, color=COLOR_SUBS[j]).move_to(
            at(col_x[j], 2.05)
        )
        headers.append(header)
        col = []
        for k in range(K):
            body = panel(
                1.4,
                0.52,
                fill_color=COLOR_SUBS[j],
                fill_opacity=0.15,
                stroke_color=COLOR_SUBS[j],
                corner_radius=0.1,
            )
            label = text(f"centroid {k}", font_size=18).move_to(body)
            chip = VGroup(body, label).move_to(at(col_x[j], 1.3 - 0.75 * k))
            col.append(chip)
        chips.append(col)
    scene.play(
        FadeIn(VGroup(*headers)),
        LaggedStart(*[FadeIn(c) for col in chips for c in col], lag_ratio=0.05),
        run_time=1.5,
    )
    caps.hold()

    caps.show("Pick one centroid per piece: that names one vector.")
    hint = text("pick one centroid per subspace", font_size=LABEL_SIZE, color=MUTED)
    hint.move_to(at(3.4, 2.05))

    def readout_text(path: Sequence[int]) -> Any:
        return text(
            "[ " + " , ".join(str(p) for p in path) + " ]",
            font_size=48,
            color=ACCENT,
            weight="BOLD",
        ).move_to(at(3.4, 1.2))

    readout = readout_text((0, 0, 0))
    scene.play(FadeIn(hint), FadeIn(readout))
    for path in ((2, 0, 3), (1, 3, 0), (X_CODE[0], X_CODE[1], X_CODE[2])):
        scene.play(
            Transform(readout, readout_text(path)),
            *[
                chips[j][k][0].animate.set_fill(COLOR_SUBS[j], 0.85)
                for j, k in enumerate(path)
            ],
            run_time=0.6,
        )
        scene.wait(0.6)
        scene.play(
            *[
                chips[j][k][0].animate.set_fill(COLOR_SUBS[j], 0.15)
                for j, k in enumerate(path)
            ],
            run_time=0.3,
        )
    caps.hold()

    caps.show("Store 12 centroids, describe 4 × 4 × 4 = 64 vectors.")
    stored_lbl = text("centroids we store", font_size=LABEL_SIZE - 2, color=MUTED)
    stored_lbl.move_to(at(3.4, 0.2))
    stored_val = math(r"3 \times 4 = 12").move_to(at(3.4, -0.35))
    reach_lbl = text(
        "different vectors we can describe", font_size=LABEL_SIZE - 2, color=MUTED
    )
    reach_lbl.move_to(at(3.4, -1.2))
    reach_val = math(r"4 \times 4 \times 4 = 64", color=SUCCESS).move_to(at(3.4, -1.75))
    scene.play(FadeIn(stored_lbl), FadeIn(stored_val))
    scene.wait(0.6)
    scene.play(FadeIn(reach_lbl), FadeIn(reach_val))
    caps.hold()

    caps.show("At scale, 2,048 centroids name 18 quintillion vectors.")
    real_hint = text(
        "real setting: 128 dims, 8 subspaces,\n256 centroids each",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).move_to(at(3.4, 1.9))
    real_stored = math(r"8 \times 256 = 2{,}048").move_to(stored_val)
    real_reach = math(r"256^{8} \approx 1.8 \times 10^{19}", color=SUCCESS).move_to(
        reach_val
    )
    scene.play(
        FadeTransform(hint, real_hint),
        FadeTransform(stored_val, real_stored),
        FadeTransform(reach_val, real_reach),
        FadeOut(readout),
        run_time=1.2,
    )
    caps.hold()

    caps.show("Storage adds up while the possibilities multiply.")
    scene.wait(0.3)
    caps.hold(extra=0.5)


# -----------------------------------------------------------------------------
# Act 4: asymmetric distance with a lookup table
# -----------------------------------------------------------------------------

CELL_XS = (-3.7, -2.5, -1.3, -0.1)
ROW_YS = (1.35, 0.55, -0.25)


def run_lookup_table(scene: Scene, caps: CaptionTrack) -> None:
    head = title("Distance without decompressing")
    scene.play(FadeIn(head, shift=DOWN * 0.2))

    caps.show("The query stays exact. Only the database is compressed.")
    q_head = text("query q", font_size=20, color=MUTED).move_to(at(-5.3, 2.0))
    col_heads = VGroup(
        *[
            text(f"ID {k}", font_size=20, color=MUTED).move_to(at(CELL_XS[k], 2.0))
            for k in range(K)
        ]
    )
    q_boxes = [
        pair_box(
            QUERY[2 * m : 2 * m + 2], COLOR_SUBS[m], width=1.95, font_size=22
        ).move_to(at(-5.3, ROW_YS[m]))
        for m in range(M)
    ]
    scene.play(FadeIn(q_head), FadeIn(col_heads), *[FadeIn(b) for b in q_boxes])
    caps.hold()

    cells: list[list[VGroup]] = []
    for m in range(M):
        row = []
        for k in range(K):
            body = panel(
                1.05,
                0.62,
                fill_color=COLOR_SUBS[m],
                fill_opacity=0.1,
                stroke_color=BORDER,
                corner_radius=0.08,
            )
            val = text(f"{LUT[m, k]:.2f}", font_size=22).move_to(body)
            row.append(VGroup(body, val).move_to(at(CELL_XS[k], ROW_YS[m])))
        cells.append(row)

    # One worked cell: distance from q's first pair to centroid 0 of subspace 1.
    caps.show("Measure the query's distance to every centroid, once.")
    c0 = PQ.codebooks[0][0]
    calc = math(
        rf"({QUERY[0]:.1f}-{c0[0]:.2f})^2+({QUERY[1]:.1f}-({c0[1]:.2f}))^2={LUT[0, 0]:.2f}",
        font_size=32,
    ).move_to(DOWN * 1.65)
    scene.play(FadeIn(cells[0][0]), FadeIn(calc))
    caps.hold(extra=0.5)

    caps.show("That is 12 numbers per query, reused for every vector.")
    rest = [cells[m][k] for m in range(M) for k in range(K) if (m, k) != (0, 0)]
    scene.play(
        LaggedStart(*[FadeIn(c) for c in rest], lag_ratio=0.08),
        FadeOut(calc),
        run_time=1.6,
    )
    caps.hold()

    # Database side.
    caps.show("A stored code just looks up its three entries.")
    db_head = text("stored codes", font_size=20, color=MUTED).move_to(at(4.1, 2.0))
    db_rows = []
    sums = []
    for r, idx in enumerate(ROW_IDS):
        y = (1.35, 0.55, -0.25, -1.05)[r]
        tag = text(f"#{idx}", font_size=22, color=MUTED).move_to(at(1.7, y))
        squares = VGroup(
            *[
                id_box(int(CODES[idx][m]), COLOR_SUBS[m], size=0.5).move_to(
                    at(2.7 + 0.6 * m, y)
                )
                for m in range(M)
            ]
        )
        parts = [LUT[m, int(CODES[idx][m])] for m in range(M)]
        total = text(
            f"= {sum(parts):.2f}", font_size=26, color=ACCENT, weight="BOLD"
        ).move_to(at(5.5, y))
        db_rows.append(VGroup(tag, squares))
        sums.append((total, parts))
    scene.play(FadeIn(db_head), *[FadeIn(r) for r in db_rows])

    def highlight(r: int, on: bool) -> list[Any]:
        idx = ROW_IDS[r]
        return [
            cells[m][int(CODES[idx][m])][0].animate.set_fill(
                COLOR_SUBS[m], 0.65 if on else 0.1
            )
            for m in range(M)
        ]

    scene.play(*highlight(0, True))
    caps.hold()

    caps.show("Add the three lookups: that is the approximate distance.")
    first_parts = sums[0][1]
    formula = math(
        rf"{first_parts[0]:.2f}+{first_parts[1]:.2f}+{first_parts[2]:.2f}={sum(first_parts):.2f}",
        font_size=34,
    ).move_to(DOWN * 1.65)
    scene.play(FadeIn(formula))
    scene.play(FadeIn(sums[0][0], shift=LEFT * 0.2))
    caps.hold()
    scene.play(*highlight(0, False), FadeOut(formula))

    caps.show("Repeat for every code. The smallest sum is the nearest.")
    for r in range(1, len(ROW_IDS)):
        scene.play(*highlight(r, True), run_time=0.4)
        scene.play(FadeIn(sums[r][0], shift=LEFT * 0.2), run_time=0.4)
        scene.play(*highlight(r, False), run_time=0.3)
    best = surrounding_panel(
        VGroup(db_rows[0], sums[0][0]),
        buff=0.12,
        stroke_color=SUCCESS,
        fill_opacity=0.08,
    )
    scene.play(Create(best))
    caps.hold()

    caps.show("The gap from the exact answer is quantization error.")
    exact = float(((X - QUERY) ** 2).sum())
    approx_note = text(
        f"#{X_IDX}: exact distance {exact:.2f}, approximate {sum(sums[0][1]):.2f}",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).move_to(DOWN * 1.65)
    scene.play(FadeIn(approx_note))
    caps.hold()

    caps.show("Real PQ: 8 lookups per vector instead of 128 multiplies.")
    scene.wait(0.3)
    caps.hold(extra=0.5)


# -----------------------------------------------------------------------------
# Act 5: the trade
# -----------------------------------------------------------------------------


def run_takeaway(scene: Scene, caps: CaptionTrack) -> None:
    head = title("Product quantization: the trade")
    scene.play(FadeIn(head, shift=DOWN * 0.2))

    caps.show("The trade: 64× less memory, much cheaper distances.")
    specs = [
        ("Memory", "64×", "512 B → 8 B per vector", SUCCESS),
        ("Distance", "8 lookups", "instead of 128 multiplies", SUCCESS),
        (
            "Accuracy",
            "approximate",
            "shortlist, then rerank\nwith exact vectors",
            ACCENT,
        ),
    ]
    cards = VGroup()
    for i, (label, big, small, color) in enumerate(specs):
        frame = panel(4.0, 2.7, fill_opacity=0.3, stroke_color=color).move_to(
            at((-4.3, 0.0, 4.3)[i], 0.3)
        )
        lbl = text(label, font_size=LABEL_SIZE, color=MUTED)
        lbl.align_to(frame, UP).shift(DOWN * 0.3).match_x(frame)
        val = text(big, font_size=44, color=color, weight="BOLD").move_to(frame)
        sm = text(small, font_size=LABEL_SIZE - 5, color=TEXT).move_to(
            frame.get_bottom() + UP * 0.6
        )
        cards.add(VGroup(frame, lbl, val, sm))
    scene.play(
        LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.3),
        run_time=2.0,
    )
    caps.hold()

    caps.show("The price is accuracy, so rerank a shortlist exactly.")
    scene.play(Indicate(cards[2], color=ACCENT, scale_factor=1.04))
    caps.hold()

    caps.show("PQ shrinks vectors. IVF and HNSW choose which to visit.")
    scene.wait(0.3)
    caps.hold(extra=1.0)


# -----------------------------------------------------------------------------
# Scene classes
# -----------------------------------------------------------------------------


class MemoryWallScene(Scene):
    """Act 1: why 512 GB of vectors is a problem."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        run_memory_wall(self, caps)
        caps.finish()


class SplitAndSnapScene(Scene):
    """Act 2: split a vector, snap pieces to centroids, store IDs."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        run_split_and_snap(self, caps)
        caps.finish()


class CodebookPowerScene(Scene):
    """Act 3: 12 stored centroids describe 64 vectors."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        run_codebook_power(self, caps)
        caps.finish()


class LookupTableScene(Scene):
    """Act 4: asymmetric distance via a per-query lookup table."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        run_lookup_table(self, caps)
        caps.finish()


class PQTakeawayScene(Scene):
    """Act 5: memory, speed, accuracy trade."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        run_takeaway(self, caps)
        caps.finish()


class ProductQuantization(Scene):
    """Consolidated video linking all five acts, with one shared caption track."""

    def construct(self) -> None:
        apply_theme(self)
        caps = CaptionTrack(self)
        acts = (
            run_memory_wall,
            run_split_and_snap,
            run_codebook_power,
            run_lookup_table,
            run_takeaway,
        )
        for i, act in enumerate(acts):
            act(self, caps)
            if i < len(acts) - 1:
                caps.clear()
                self.play(FadeOut(*self.mobjects), run_time=TRANSITION_TIME)
                self.wait(0.3)
        caps.finish()
