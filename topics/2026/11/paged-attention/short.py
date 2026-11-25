"""PagedAttention as a vertical YouTube Short (9:16, ~50 s, captions + SFX).

Run from the repository root:

    make preview FILE=topics/2026/11/paged-attention/short.py \
        SCENE=PagedAttentionShort FORMAT=shorts

Story: reserved-but-empty KV memory -> logical blocks + block table + physical pool
-> allocate a block only when the last one is full -> waste falls below 4%.
All slot counts are illustrative; the 60-80% and <4% figures come from the vLLM paper
(Kwon et al., 2023).
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    LaggedStart,
    RoundedRectangle,
    Scene,
    Square,
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
    SHORTS_CONTENT_CENTER_X,
    SHORTS_LABEL_SIZE,
    SHORTS_TITLE_SIZE,
    SUCCESS,
    SURFACE,
    TEXT,
    apply_theme,
    text,
)

X0 = SHORTS_CONTENT_CENTER_X
TITLE_Y = 6.9
LOGICAL_COLORS = (ENTITY_A, ENTITY_B, ENTITY_C, ACCENT)


def slot(
    size: float,
    label: str = "",
    *,
    color: str = BORDER,
    filled: bool = False,
    label_size: float = 20,
) -> VGroup:
    """One KV-cache slot: a square with an optional token label."""
    box = Square(side_length=size, stroke_width=2, stroke_color=color)
    if filled:
        box.set_fill(color, 0.55)
    mark = text(label, font_size=label_size, color=TEXT)
    mark.move_to(box)
    return VGroup(box, mark)


def fill_slot(item: VGroup, color: str) -> None:
    """Turn an empty slot into a filled one in place."""
    item[0].set_fill(color, 0.55).set_stroke(color)


def block(
    count: int,
    size: float,
    *,
    color: str,
    filled: int,
    first_token: int | None = None,
) -> VGroup:
    """A row of `count` slots; the first `filled` are in use."""
    slots = VGroup(
        *(
            slot(
                size,
                "" if first_token is None else str(first_token + i),
                color=color if i < filled else BORDER,
                filled=i < filled,
            )
            for i in range(count)
        )
    ).arrange(RIGHT, buff=0)
    return slots


def caption_track(scene: Scene) -> CaptionTrack:
    return CaptionTrack(
        scene,
        position=(X0, SHORTS_CAPTION_Y),
        font_size=SHORTS_CAPTION_SIZE,
        max_chars=30,
    )


def section_label(content: str, y: float) -> VGroup:
    return VGroup(text(content, font_size=SHORTS_LABEL_SIZE, color=MUTED)).move_to(
        [X0, y, 0]
    )


# -----------------------------------------------------------------------------
# Part 1: reserved memory that sits empty
# -----------------------------------------------------------------------------


def problem(scene: Scene, caps: CaptionTrack) -> VGroup:
    head = text("KV cache memory", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    head.move_to([X0, TITLE_Y, 0])
    scene.play(FadeIn(head))

    used = (3, 5, 7)
    colors = (ENTITY_A, ENTITY_B, ENTITY_C)
    rows = VGroup()
    for i, (n_used, color) in enumerate(zip(used, colors)):
        row = block(12, 0.5, color=color, filled=0)
        row.move_to([X0 + 0.5, 5.0 - 0.95 * i, 0])
        tag = text(f"Req {i + 1}", font_size=24, color=color).next_to(
            row, LEFT, buff=0.2
        )
        rows.add(VGroup(row, tag))

    caps.show("Every request reserves memory for its maximum length.")
    scene.play(LaggedStart(*(FadeIn(r) for r in rows), lag_ratio=0.25))
    caps.hold()

    caps.show("Only a few slots hold real tokens. The rest sit idle.")
    fills = []
    for row, n_used, color in zip(rows, used, colors):
        for index in range(n_used):
            fill_slot(row[0][index], color)
        fills.append(row)
    play_sfx(scene, "tick")
    scene.play(
        LaggedStart(*(Indicate(r[0], color=TEXT, scale_factor=1.03) for r in rows)),
        run_time=1.2,
    )
    for row, n_used in zip(rows, used):
        for index in range(n_used, 12):
            row[0][index][0].set_stroke(ERROR).set_fill(ERROR, 0.12)
    badge = VGroup(
        text("58% unused", font_size=64, color=ERROR, weight="BOLD"),
        text("illustrative: 21 of 36 slots", font_size=26, color=MUTED),
    ).arrange(DOWN, buff=0.15)
    badge.move_to([X0, 1.7, 0])
    scene.play(FadeIn(badge, shift=UP * 0.2))
    caps.hold()

    caps.show("A new request is rejected, even though memory sits idle.")
    req4 = block(12, 0.5, color=ACCENT, filled=0)
    req4.move_to([X0 + 0.5, 0.2, 0])
    tag4 = text("Req 4", font_size=24, color=ACCENT).next_to(req4, LEFT, buff=0.2)
    oom = text("Out of memory", font_size=44, color=ERROR, weight="BOLD")
    oom.move_to([X0, -0.8, 0])
    scene.play(FadeIn(VGroup(req4, tag4)))
    play_sfx(scene, "deny")
    scene.play(FadeIn(oom, shift=UP * 0.2))
    caps.hold()
    return head


# -----------------------------------------------------------------------------
# Part 2: logical blocks, block table, physical pool
# -----------------------------------------------------------------------------

LOGICAL_Y = 5.1
TABLE_Y = (3.0, 2.3, 1.6, 0.9)
POOL_Y = (-0.8, -1.9)
SLOT = 0.4
BLOCK_W = 4 * SLOT
BLOCK_GAP = 0.2
# Physical block index -> (owner logical block or None for other/free)
OWNERS: dict[int, int | None] = {1: 1, 4: 2, 6: 0, 2: None}
OTHER_REQUESTS = (0, 3, 5, 7)
MAPPING = {0: 6, 1: 1, 2: 4, 3: 2}  # logical -> physical (illustrative)


def row_x(index: int, count: int = 4) -> float:
    span = count * BLOCK_W + (count - 1) * BLOCK_GAP
    return X0 - span / 2 + BLOCK_W / 2 + index * (BLOCK_W + BLOCK_GAP)


def table_row(logical: int, y: float) -> VGroup:
    color = LOGICAL_COLORS[logical]
    frame = RoundedRectangle(
        width=3.6,
        height=0.6,
        corner_radius=0.12,
        stroke_color=color,
        stroke_width=2,
        fill_color=SURFACE,
        fill_opacity=0.9,
    )
    label = text(
        f"L{logical}   →   P{MAPPING[logical]}", font_size=30, color=TEXT
    ).move_to(frame)
    return VGroup(frame, label).move_to([X0, y, 0])


def pool_blocks() -> list[VGroup]:
    blocks = []
    for index in range(8):
        owner = OWNERS.get(index)
        if index in OTHER_REQUESTS:
            item = block(4, SLOT, color=BORDER, filled=4)
        else:
            item = block(4, SLOT, color=BORDER, filled=0)
        row, col = divmod(index, 4)
        item.move_to([row_x(col), POOL_Y[row], 0])
        name_color = (
            SUCCESS if (owner is None and index not in OTHER_REQUESTS) else MUTED
        )
        name = text(
            f"P{index}" + (" free" if index == 2 else ""),
            font_size=24,
            color=name_color,
        ).next_to(item, DOWN, buff=0.12)
        blocks.append(VGroup(item, name))
    return blocks


def claim(
    scene: Scene,
    row: VGroup,
    target: VGroup,
    logical: int,
    filled: int,
    sfx: str = "tick",
) -> None:
    """Fly a dot from a table row to its physical block, then tint the block."""
    color = LOGICAL_COLORS[logical]
    dot = Dot(color=color, radius=0.1).move_to(row.get_right())
    dot.set_z_index(50)
    play_sfx(scene, sfx)
    scene.play(FadeIn(dot, run_time=0.15))
    scene.play(dot.animate.move_to(target[0].get_top()), run_time=0.6)
    for index in range(filled):
        fill_slot(target[0][index], color)
    target[0].set_stroke(color)
    scene.play(FadeOut(dot), Indicate(target[0], color=color, scale_factor=1.06))


def mechanism(scene: Scene, caps: CaptionTrack, head: VGroup) -> None:
    play_sfx(scene, "whoosh")
    new_head = text("PagedAttention", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    new_head.move_to([X0, TITLE_Y, 0])
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    scene.play(FadeOut(*others), Transform(head, new_head), run_time=0.8)
    caps.show("PagedAttention borrows paging from operating systems.")
    caps.hold(extra=-0.5)

    # Logical blocks (a sequence of 10 tokens in blocks of 4)
    caps.show("Split the sequence into small fixed-size blocks.")
    logical_label = section_label("Logical blocks (one sequence)", 5.85)
    logical = VGroup()
    counts = (4, 4, 2)
    first = (0, 4, 8)
    for i in range(3):
        item = block(
            4, SLOT, color=LOGICAL_COLORS[i], filled=counts[i], first_token=first[i]
        )
        item.move_to([row_x(i), LOGICAL_Y, 0])
        name = text(f"L{i}", font_size=24, color=LOGICAL_COLORS[i]).next_to(
            item, DOWN, buff=0.12
        )
        logical.add(VGroup(item, name))
    scene.play(FadeIn(logical_label))
    scene.play(LaggedStart(*(FadeIn(b) for b in logical), lag_ratio=0.3))
    caps.hold()

    # Physical pool, then the table that links the two
    caps.show("GPU memory is a pool of same-size blocks.")
    pool_label = section_label("Physical memory (grey: others)", -0.05)
    pool = pool_blocks()
    table_label = section_label("Block table", 3.7)
    scene.play(
        FadeIn(pool_label), LaggedStart(*(FadeIn(b) for b in pool), lag_ratio=0.1)
    )
    caps.hold()

    caps.show("A block table maps each logical block to any free one.")
    scene.play(FadeIn(table_label))
    rows = []
    for i in range(3):
        row = table_row(i, TABLE_Y[i])
        rows.append(row)
        scene.play(FadeIn(row, run_time=0.3))
        claim(scene, row, pool[MAPPING[i]], i, counts[i])
    caps.hold()

    caps.show("Blocks can sit anywhere. No contiguous space needed.")
    scene.play(
        *(
            Indicate(pool[MAPPING[i]][0], color=LOGICAL_COLORS[i], scale_factor=1.08)
            for i in range(3)
        ),
        run_time=1.2,
    )
    caps.hold()

    # Token-by-token allocation
    caps.show("New token? Write it into the last block.")
    for token in (10, 11):
        slot_index = token - 8
        label = text(str(token), font_size=18, color=TEXT)
        logical_slot = logical[2][0][slot_index]
        physical_slot = pool[MAPPING[2]][0][slot_index]
        label.move_to(logical_slot[0])
        fill_slot(logical_slot, ENTITY_C)
        fill_slot(physical_slot, ENTITY_C)
        play_sfx(scene, "tick")
        scene.play(
            Indicate(logical_slot[0], color=ENTITY_C, scale_factor=1.3),
            Indicate(physical_slot[0], color=ENTITY_C, scale_factor=1.3),
            run_time=0.6,
        )
        logical_slot[1].become(label)
    caps.hold()

    caps.show("Block full? Claim a free block, add a table row.")
    new_logical = block(4, SLOT, color=ACCENT, filled=1, first_token=12)
    new_logical.move_to([row_x(3), LOGICAL_Y, 0])
    new_name = text("L3", font_size=24, color=ACCENT).next_to(
        new_logical, DOWN, buff=0.12
    )
    play_sfx(scene, "pop")
    scene.play(FadeIn(VGroup(new_logical, new_name), shift=DOWN * 0.2))
    row = table_row(3, TABLE_Y[3])
    scene.play(FadeIn(row, run_time=0.3))
    claim(scene, row, pool[MAPPING[3]], 3, 1, sfx="pop")
    old_name = pool[MAPPING[3]][1]
    new_name_label = text("P2", font_size=24, color=ACCENT).move_to(old_name)
    scene.play(FadeOut(old_name), FadeIn(new_name_label), run_time=0.4)
    caps.hold(extra=1.0)


# -----------------------------------------------------------------------------
# Part 3: the payoff
# -----------------------------------------------------------------------------


def payoff(scene: Scene, caps: CaptionTrack, head: VGroup) -> None:
    caps.show("Result: waste drops from 60-80% to under 4%.")
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    scene.play(FadeOut(*others), run_time=0.8)
    old = VGroup(
        text("60-80%", font_size=88, color=ERROR, weight="BOLD"),
        text("wasted with contiguous allocation", font_size=28, color=MUTED),
    ).arrange(DOWN, buff=0.2)
    new = VGroup(
        text("< 4%", font_size=88, color=SUCCESS, weight="BOLD"),
        text("wasted with PagedAttention", font_size=28, color=MUTED),
    ).arrange(DOWN, buff=0.2)
    old.move_to([X0, 4.4, 0])
    new.move_to([X0, 1.2, 0])
    source = text("Source: vLLM paper (Kwon et al., 2023)", font_size=24, color=MUTED)
    source.move_to([X0, -1.3, 0])
    scene.play(FadeIn(old, shift=UP * 0.2))
    scene.wait(0.6)
    play_sfx(scene, "chime")
    scene.play(FadeIn(new, shift=UP * 0.2), FadeIn(source))
    caps.hold()

    caps.show("Same GPU, more requests served at once.")
    caps.hold(extra=0.8)


class PagedAttentionShort(Scene):
    """Vertical Short, about 50 s. Render with FORMAT=shorts."""

    def construct(self) -> None:
        apply_theme(self)
        caps = caption_track(self)
        head = problem(self, caps)
        mechanism(self, caps, head)
        payoff(self, caps, head)
        caps.finish()
