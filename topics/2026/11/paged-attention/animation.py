"""PagedAttention in LLM Serving.

Demonstrates:
1. The Contiguous Allocation Crisis (internal/external fragmentation and waste).
2. PagedAttention Architecture (Logical Blocks, Block Table, Physical HBM pool).
3. On-Demand Dynamic Allocation (filling blocks token-by-token and fetching from free pool).
4. Prompt Sharing and Copy-on-Write for parallel sampling.
"""

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circumscribe,
    DashedVMobject,
    FadeIn,
    FadeOut,
    LaggedStart,
    RoundedRectangle,
    Scene,
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

COLOR_REQ1 = ENTITY_A  # Sky Blue
COLOR_REQ2 = ENTITY_B  # Purple
COLOR_REQ3 = ENTITY_C  # Orange
COLOR_FREE = BORDER  # Muted Slate
COLOR_WASTE = ERROR  # Red tint


def dashed_box(
    width: float,
    height: float,
    color: str = COLOR_WASTE,
    num_dashes: int = 12,
    fill_opacity: float = 0.15,
) -> VGroup:
    """Create a rounded rectangle with dashed outline."""
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
# Act 1: The Contiguous KV Cache Crisis
# -----------------------------------------------------------------------------


def run_act1(scene: Scene) -> None:
    """Act 1: The Contiguous Allocation Problem and Memory Fragmentation."""
    scene_title = title("The Contiguous KV Cache Crisis")
    subtitle = text(
        "Pre-allocating contiguous buffers for max sequence length wastes VRAM",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.4)

    # Big GPU Memory Container (width 12.0 comfortably spans -6.0 to +6.0)
    mem_width = 12.2
    mem_height = 3.5
    mem_panel = panel(
        width=mem_width,
        height=mem_height,
        fill_color=SURFACE,
        fill_opacity=0.3,
        stroke_color=BORDER,
    ).move_to(DOWN * 0.25)

    mem_label = text(
        "GPU High-Bandwidth Memory (KV Cache Pool: 48 Contiguous Slots)",
        font_size=LABEL_SIZE - 3,
        color=TEXT,
        weight="BOLD",
    ).next_to(mem_panel, UP, buff=0.15)

    scene.play(FadeIn(mem_panel), FadeIn(mem_label))

    # 3 Requests, each reserving 16 contiguous slots.
    # Total 48 slots. Displayed as 3 rows of 16 slots.
    # slot_w = 0.50, gap = 0.06 -> 16 slots take 16*0.50 + 15*0.06 = 8.90 width.
    slot_w = 0.50
    slot_h = 0.60
    slot_gap = 0.06
    start_x = -3.45

    row_y_coords = [0.65, -0.20, -1.05]
    req_data = [
        ("Req 1 (4/16)", COLOR_REQ1, 4, 16),
        ("Req 2 (6/16)", COLOR_REQ2, 6, 16),
        ("Req 3 (10/16)", COLOR_REQ3, 10, 16),
    ]

    all_slots_group = VGroup()
    used_boxes = VGroup()
    waste_boxes = VGroup()
    labels_group = VGroup()

    for row_idx, (r_name, r_col, used, total) in enumerate(req_data):
        y = row_y_coords[row_idx]
        lbl = text(r_name, font_size=LABEL_SIZE - 4, color=r_col, weight="BOLD")
        lbl.move_to([-4.8, y, 0])
        labels_group.add(lbl)

        for s in range(total):
            x = start_x + s * (slot_w + slot_gap)
            if s < used:
                box = RoundedRectangle(
                    width=slot_w,
                    height=slot_h,
                    corner_radius=0.06,
                    fill_color=r_col,
                    fill_opacity=0.6,
                    stroke_color=r_col,
                    stroke_width=1.5,
                ).move_to([x, y, 0])
                t_lbl = text(
                    f"t{s}", font_size=LABEL_SIZE - 8, color=TEXT, weight="BOLD"
                ).move_to(box)
                used_boxes.add(VGroup(box, t_lbl))
            else:
                w_box = dashed_box(slot_w, slot_h, color=COLOR_WASTE, num_dashes=8)
                w_box.move_to([x, y, 0])
                waste_boxes.add(w_box)

    all_slots_group.add(labels_group, used_boxes, waste_boxes)

    scene.play(
        FadeIn(labels_group),
        LaggedStart(*(FadeIn(b) for b in used_boxes), lag_ratio=0.03),
        LaggedStart(*(FadeIn(b) for b in waste_boxes), lag_ratio=0.02),
        run_time=1.3,
    )
    scene.wait(0.5)

    # Waste callout badge
    badge_text1 = text(
        "28 of 48 reserved slots (58.3%) sit completely idle",
        font_size=LABEL_SIZE - 2,
        color=ERROR,
        weight="BOLD",
    )
    badge_text2 = text(
        "Memory locked for maximum sequence length, but generation finished early",
        font_size=LABEL_SIZE - 4,
        color=TEXT,
    )
    badge_content = VGroup(badge_text1, badge_text2).arrange(DOWN, buff=0.1)
    callout = surrounding_panel(
        badge_content,
        buff=0.18,
        fill_color=SURFACE,
        fill_opacity=0.85,
        stroke_color=ERROR,
        stroke_width=2,
    ).move_to(DOWN * 2.70)
    badge_content.move_to(callout)
    badge_group = VGroup(callout, badge_content)

    scene.play(FadeIn(badge_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE)

    # External Fragmentation Demonstration
    scene.play(FadeOut(badge_group), run_time=0.4)

    err_text1 = text(
        "New Request 4 arrives needing 12 contiguous slots",
        font_size=LABEL_SIZE - 2,
        color=ACCENT,
        weight="BOLD",
    )
    err_text2 = text(
        "Total free slots = 28, but largest contiguous hole is too small to fit!",
        font_size=LABEL_SIZE - 4,
        color=ERROR,
    )
    err_content = VGroup(err_text1, err_text2).arrange(DOWN, buff=0.1)
    err_panel = surrounding_panel(
        err_content,
        buff=0.18,
        fill_color=SURFACE,
        fill_opacity=0.85,
        stroke_color=ACCENT,
        stroke_width=2,
    ).move_to(DOWN * 2.70)
    err_content.move_to(err_panel)
    err_group = VGroup(err_panel, err_content)

    scene.play(FadeIn(err_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 0.5)


# -----------------------------------------------------------------------------
# Act 2: The PagedAttention Architecture
# -----------------------------------------------------------------------------


def run_act2(scene: Scene) -> None:
    """Act 2: Logical Blocks, Block Table, and Physical GPU Memory."""
    scene_title = title("PagedAttention: Virtual Memory for LLMs")
    subtitle = text(
        "Non-contiguous physical blocks mapped through a dynamic Block Table",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.4)

    # Left Container: Logical Blocks (Sequence View)
    l_panel = panel(
        width=3.6,
        height=3.9,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(LEFT * 4.6 + DOWN * 0.35)
    l_hdr = text(
        "Logical Blocks (Req 1)",
        font_size=LABEL_SIZE - 3,
        color=COLOR_REQ1,
        weight="BOLD",
    ).next_to(l_panel, UP, buff=0.12)

    # Center Container: Block Table
    t_panel = panel(
        width=3.4,
        height=3.9,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(LEFT * 0.7 + DOWN * 0.35)
    t_hdr = text(
        "Block Table", font_size=LABEL_SIZE - 3, color=ACCENT, weight="BOLD"
    ).next_to(t_panel, UP, buff=0.12)

    # Right Container: Physical GPU Memory Pool
    p_panel = panel(
        width=4.8,
        height=3.9,
        fill_color=SURFACE,
        fill_opacity=0.25,
        stroke_color=BORDER,
    ).move_to(RIGHT * 3.8 + DOWN * 0.35)
    p_hdr = text(
        "Physical GPU Memory", font_size=LABEL_SIZE - 3, color=SUCCESS, weight="BOLD"
    ).next_to(p_panel, UP, buff=0.12)

    scene.play(
        FadeIn(l_panel),
        FadeIn(l_hdr),
        FadeIn(t_panel),
        FadeIn(t_hdr),
        FadeIn(p_panel),
        FadeIn(p_hdr),
    )

    # Create Logical Blocks
    # Block 0: tokens 0..3, Block 1: tokens 4..7, Block 2: tokens 8..9
    l_blocks = VGroup()
    l_y_positions = [0.70, -0.30, -1.30]
    l_data = [
        ("Logical Block 0", "Tokens [t0..t3]", COLOR_REQ1),
        ("Logical Block 1", "Tokens [t4..t7]", COLOR_REQ1),
        ("Logical Block 2", "Tokens [t8..t9]", COLOR_REQ1),
    ]
    for idx, (title_str, sub_str, col) in enumerate(l_data):
        y = l_y_positions[idx]
        b_box = RoundedRectangle(
            width=3.1,
            height=0.80,
            corner_radius=0.08,
            fill_color=col,
            fill_opacity=0.35,
            stroke_color=col,
            stroke_width=1.5,
        ).move_to([l_panel.get_center()[0], y, 0])
        b_t1 = text(
            title_str, font_size=LABEL_SIZE - 4, color=TEXT, weight="BOLD"
        ).move_to(b_box.get_center() + UP * 0.16)
        b_t2 = text(sub_str, font_size=LABEL_SIZE - 6, color=MUTED).move_to(
            b_box.get_center() + DOWN * 0.16
        )
        l_blocks.add(VGroup(b_box, b_t1, b_t2))

    # Block Table Rows
    # In table: L0 -> P3, L1 -> P6, L2 -> P9 (all in col 0 of physical grid for clean arrow paths)
    t_rows = VGroup()
    t_headers = text(
        "Logical   Phys   Filled", font_size=LABEL_SIZE - 5, color=MUTED
    ).move_to([t_panel.get_center()[0], 1.20, 0])
    t_rows.add(t_headers)

    table_data = [
        ("Block 0", "P3", "4 / 4"),
        ("Block 1", "P6", "4 / 4"),
        ("Block 2", "P9", "2 / 4"),
    ]
    for idx, (l_str, p_str, f_str) in enumerate(table_data):
        y = l_y_positions[idx]
        r_box = RoundedRectangle(
            width=3.0,
            height=0.80,
            corner_radius=0.08,
            fill_color=SURFACE,
            fill_opacity=0.5,
            stroke_color=BORDER,
            stroke_width=1.5,
        ).move_to([t_panel.get_center()[0], y, 0])
        r_text = text(
            f"{l_str}  ->  {p_str}    ({f_str})",
            font_size=LABEL_SIZE - 5,
            color=TEXT,
            weight="BOLD",
        ).move_to(r_box)
        t_rows.add(VGroup(r_box, r_text))

    # Physical Blocks Grid (12 blocks total in 4 rows x 3 cols)
    # P3 (row 1, col 0) = L0
    # P6 (row 2, col 0) = L1
    # P9 (row 3, col 0) = L2
    # Because they are in col 0, arrows from Block Table enter their left edge directly!
    phys_blocks = VGroup()
    p_cols = 3
    p_w = 1.3
    p_h = 0.58
    p_grid_origin = p_panel.get_center() + LEFT * 1.5 + UP * 1.15

    assigned_phys = {3: "L0", 6: "L1", 9: "L2"}

    for p_id in range(12):
        row = p_id // p_cols
        col = p_id % p_cols
        pos = p_grid_origin + RIGHT * (col * 1.5) + DOWN * (row * 0.75)

        if p_id in assigned_phys:
            fill_col = COLOR_REQ1
            opac = 0.65
            border_col = COLOR_REQ1
            t_col = TEXT
            t_str = f"P{p_id} ({assigned_phys[p_id]})"
        elif p_id in [1, 5, 8]:
            fill_col = COLOR_REQ2
            opac = 0.35
            border_col = COLOR_REQ2
            t_col = MUTED
            t_str = f"P{p_id} (R2)"
        else:
            fill_col = COLOR_FREE
            opac = 0.15
            border_col = BORDER
            t_col = MUTED
            t_str = f"P{p_id} (free)"

        p_box = RoundedRectangle(
            width=p_w,
            height=p_h,
            corner_radius=0.06,
            fill_color=fill_col,
            fill_opacity=opac,
            stroke_color=border_col,
            stroke_width=1.5,
        ).move_to(pos)
        p_txt = text(t_str, font_size=LABEL_SIZE - 7, color=t_col).move_to(p_box)
        phys_blocks.add(VGroup(p_box, p_txt))

    scene.play(
        LaggedStart(*(FadeIn(b) for b in l_blocks), lag_ratio=0.15),
        LaggedStart(*(FadeIn(r) for r in t_rows), lag_ratio=0.15),
        LaggedStart(*(FadeIn(p) for p in phys_blocks), lag_ratio=0.05),
        run_time=1.6,
    )
    scene.wait(0.6)

    # Animate routing arrows from Logical -> Table -> Physical
    arrows = VGroup()
    p_targets = {0: phys_blocks[3], 1: phys_blocks[6], 2: phys_blocks[9]}

    for i in range(3):
        l_obj = l_blocks[i]
        t_obj = t_rows[i + 1]
        p_obj = p_targets[i]

        arr1 = Arrow(
            l_obj.get_right(),
            t_obj.get_left(),
            buff=0.08,
            color=ACCENT,
            stroke_width=2,
            max_tip_length_to_length_ratio=0.2,
        )
        arr2 = Arrow(
            t_obj.get_right(),
            p_obj.get_left(),
            buff=0.08,
            color=ACCENT,
            stroke_width=2,
            max_tip_length_to_length_ratio=0.2,
        )
        arrows.add(arr1, arr2)

    scene.play(LaggedStart(*(FadeIn(a) for a in arrows), lag_ratio=0.15), run_time=1.2)
    scene.wait(0.5)

    # Key insight callout (at DOWN * 2.80, leaving 0.18 gap below panels and safe above player bar)
    insight_text = text(
        "Physical blocks are scattered across memory without requiring contiguous layout",
        font_size=LABEL_SIZE - 3,
        color=SUCCESS,
        weight="BOLD",
    )
    insight_box = surrounding_panel(
        insight_text,
        buff=0.18,
        fill_color=SURFACE,
        fill_opacity=0.85,
        stroke_color=SUCCESS,
        stroke_width=2,
    ).move_to(DOWN * 2.80)
    insight_text.move_to(insight_box)
    insight_group = VGroup(insight_box, insight_text)

    scene.play(FadeIn(insight_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 0.5)


# -----------------------------------------------------------------------------
# Act 3: On-Demand Dynamic Allocation
# -----------------------------------------------------------------------------


def run_act3(scene: Scene) -> None:
    """Act 3: Dynamic token generation and on-demand block allocation."""
    scene_title = title("On-Demand Dynamic Allocation")
    subtitle = text(
        "Blocks are claimed from the free pool only when the current block fills",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.4)

    # Active Sequence State at Top (height 2.15, centered at UP * 1.20)
    top_panel = panel(
        width=11.2,
        height=2.15,
        fill_color=SURFACE,
        fill_opacity=0.3,
        stroke_color=BORDER,
    ).move_to(UP * 1.20)

    top_hdr = text(
        "Active Request Generating Tokens (Block Size B = 4)",
        font_size=LABEL_SIZE - 3,
        color=TEXT,
        weight="BOLD",
    ).next_to(top_panel, UP, buff=0.12)
    scene.play(FadeIn(top_panel), FadeIn(top_hdr))

    # Show Block 2 (Physical Block P9) with 4 token slots:
    block2_title = text(
        "Current Logical Block 2 -> Physical Block P9",
        font_size=LABEL_SIZE - 3,
        color=COLOR_REQ1,
        weight="BOLD",
    ).move_to(top_panel.get_top() + DOWN * 0.38)
    scene.play(FadeIn(block2_title))

    slot_w, slot_h = 1.6, 0.85
    b2_slots = VGroup()
    slot_centers = []
    base_x = -2.7

    for s in range(4):
        x = base_x + s * (slot_w + 0.25)
        slot_centers.append(x)
        if s < 2:
            box = RoundedRectangle(
                width=slot_w,
                height=slot_h,
                corner_radius=0.08,
                fill_color=COLOR_REQ1,
                fill_opacity=0.6,
                stroke_color=COLOR_REQ1,
                stroke_width=2,
            ).move_to([x, 0.75, 0])
            lbl = text(
                f"Token t{8+s}", font_size=LABEL_SIZE - 4, color=TEXT, weight="BOLD"
            ).move_to(box)
            b2_slots.add(VGroup(box, lbl))
        else:
            w_box = dashed_box(slot_w, slot_h, color=BORDER, num_dashes=10)
            w_box.move_to([x, 0.75, 0])
            empty_lbl = text(
                "Slot free", font_size=LABEL_SIZE - 6, color=MUTED
            ).move_to(w_box)
            b2_slots.add(VGroup(w_box, empty_lbl))

    scene.play(LaggedStart(*(FadeIn(s) for s in b2_slots), lag_ratio=0.1), run_time=1.0)
    scene.wait(0.5)

    # Bottom Area: Free Block Pool & Block Table Status
    # Free Block Pool Container on Left (height 1.85, center DOWN * 1.30)
    pool_panel = panel(
        width=5.4,
        height=1.85,
        fill_color=SURFACE,
        fill_opacity=0.3,
        stroke_color=BORDER,
    ).move_to(LEFT * 3.0 + DOWN * 1.30)
    pool_hdr = text(
        "Free Block Pool", font_size=LABEL_SIZE - 3, color=MUTED, weight="BOLD"
    ).next_to(pool_panel, UP, buff=0.12)

    # Free blocks available: P5, P7, P10
    free_p5 = RoundedRectangle(
        width=1.35,
        height=0.75,
        corner_radius=0.08,
        fill_color=COLOR_FREE,
        fill_opacity=0.25,
        stroke_color=ACCENT,
        stroke_width=2,
    ).move_to(pool_panel.get_center() + LEFT * 1.5)
    p5_txt = text(
        "P5 (free)", font_size=LABEL_SIZE - 6, color=ACCENT, weight="BOLD"
    ).move_to(free_p5)
    block_p5 = VGroup(free_p5, p5_txt)

    free_p7 = RoundedRectangle(
        width=1.35,
        height=0.75,
        corner_radius=0.08,
        fill_color=COLOR_FREE,
        fill_opacity=0.2,
        stroke_color=BORDER,
        stroke_width=1.5,
    ).move_to(pool_panel.get_center())
    p7_txt = text("P7 (free)", font_size=LABEL_SIZE - 6, color=MUTED).move_to(free_p7)
    block_p7 = VGroup(free_p7, p7_txt)

    free_p10 = RoundedRectangle(
        width=1.35,
        height=0.75,
        corner_radius=0.08,
        fill_color=COLOR_FREE,
        fill_opacity=0.2,
        stroke_color=BORDER,
        stroke_width=1.5,
    ).move_to(pool_panel.get_center() + RIGHT * 1.5)
    p10_txt = text("P10 (free)", font_size=LABEL_SIZE - 6, color=MUTED).move_to(
        free_p10
    )
    block_p10 = VGroup(free_p10, p10_txt)

    scene.play(
        FadeIn(pool_panel),
        FadeIn(pool_hdr),
        FadeIn(block_p5),
        FadeIn(block_p7),
        FadeIn(block_p10),
    )

    # Dynamic generation narration box on right (height 1.85, width 5.6)
    status_panel = panel(
        width=5.6,
        height=1.85,
        fill_color=SURFACE,
        fill_opacity=0.3,
        stroke_color=BORDER,
    ).move_to(RIGHT * 3.0 + DOWN * 1.30)
    status_hdr = text(
        "Scheduler Status", font_size=LABEL_SIZE - 3, color=ACCENT, weight="BOLD"
    ).next_to(status_panel, UP, buff=0.12)

    step1_msg = text(
        "Step 1: Emit Token t10\nFills slot 2 of Block P9",
        font_size=13,
        color=TEXT,
    ).move_to(status_panel)

    scene.play(FadeIn(status_panel), FadeIn(status_hdr), FadeIn(step1_msg))

    # Animate filling slot 2 with t10
    t10_box = RoundedRectangle(
        width=slot_w,
        height=slot_h,
        corner_radius=0.08,
        fill_color=COLOR_REQ1,
        fill_opacity=0.6,
        stroke_color=COLOR_REQ1,
        stroke_width=2,
    ).move_to([slot_centers[2], 0.75, 0])
    t10_lbl = text(
        "Token t10", font_size=LABEL_SIZE - 4, color=TEXT, weight="BOLD"
    ).move_to(t10_box)
    t10_group = VGroup(t10_box, t10_lbl)

    scene.play(Transform(b2_slots[2], t10_group), run_time=0.7)
    scene.wait(0.4)

    # Step 2: Emit Token t11 -> fills slot 3 (Block 2 is now completely FULL)
    step2_msg = text(
        "Step 2: Emit Token t11\nBlock P9 is now 100% full (4/4)",
        font_size=13,
        color=TEXT,
    ).move_to(status_panel)

    t11_box = RoundedRectangle(
        width=slot_w,
        height=slot_h,
        corner_radius=0.08,
        fill_color=COLOR_REQ1,
        fill_opacity=0.6,
        stroke_color=COLOR_REQ1,
        stroke_width=2,
    ).move_to([slot_centers[3], 0.75, 0])
    t11_lbl = text(
        "Token t11", font_size=LABEL_SIZE - 4, color=TEXT, weight="BOLD"
    ).move_to(t11_box)
    t11_group = VGroup(t11_box, t11_lbl)

    scene.play(
        Transform(step1_msg, step2_msg),
        Transform(b2_slots[3], t11_group),
        run_time=0.8,
    )
    scene.wait(0.4)

    # Step 3: Emit Token t12 -> Triggers on-demand block allocation
    # Shorter text with 13pt font easily fits with wide margin inside status_panel
    step3_msg = text(
        "Step 3: Emit Token t12\nBlock P9 full -> Allocates P5 from pool",
        font_size=13,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(status_panel)

    scene.play(Transform(step1_msg, step3_msg))
    scene.play(Circumscribe(block_p5, color=SUCCESS), run_time=0.8)

    # Highlight P5 turning into an active block
    new_active_p5 = RoundedRectangle(
        width=1.35,
        height=0.75,
        corner_radius=0.08,
        fill_color=COLOR_REQ1,
        fill_opacity=0.7,
        stroke_color=COLOR_REQ1,
        stroke_width=2,
    ).move_to(free_p5)
    new_p5_txt = text(
        "P5 (L3)", font_size=LABEL_SIZE - 6, color=TEXT, weight="BOLD"
    ).move_to(new_active_p5)

    scene.play(Transform(block_p5, VGroup(new_active_p5, new_p5_txt)), run_time=0.8)
    scene.wait(0.5)

    # Stat callout at bottom (DOWN * 2.75 with height ~0.6 leaves safe margin above video player scrubber)
    bottom_text = text(
        "Zero memory reservation waste. Only the active tail block has unused slots (< 4% waste).",
        font_size=13,
        color=SUCCESS,
        weight="BOLD",
    )
    bottom_box = surrounding_panel(
        bottom_text,
        buff=0.16,
        fill_color=SURFACE,
        fill_opacity=0.9,
        stroke_color=SUCCESS,
        stroke_width=2,
    ).move_to(DOWN * 2.75)
    bottom_text.move_to(bottom_box)
    bottom_group = VGroup(bottom_box, bottom_text)

    scene.play(FadeIn(bottom_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 0.5)


# -----------------------------------------------------------------------------
# Act 4: System Impact & Key Takeaways
# -----------------------------------------------------------------------------


def run_act4(scene: Scene) -> None:
    """Act 4: High-level comparison and throughput impact."""
    scene_title = title("PagedAttention: System Impact")
    subtitle = text(
        "Eliminating the memory wall to dramatically increase serving throughput",
        font_size=LABEL_SIZE - 2,
        color=MUTED,
    ).next_to(scene_title, DOWN, buff=0.15)
    scene.play(FadeIn(scene_title, shift=DOWN * 0.2), FadeIn(subtitle))
    scene.wait(0.4)

    # Left Panel: Contiguous Allocation (The Problem)
    left_panel = panel(
        width=5.7,
        height=3.3,
        fill_color=SURFACE,
        fill_opacity=0.35,
        stroke_color=ERROR,
        stroke_width=1.5,
    ).move_to(LEFT * 3.1 + DOWN * 0.40)
    left_hdr = text(
        "Traditional Contiguous KV",
        font_size=LABEL_SIZE - 2,
        color=ERROR,
        weight="BOLD",
    ).move_to(left_panel.get_top() + DOWN * 0.35)

    left_items = (
        VGroup(
            text(
                "• Static allocation for max sequence length", font_size=13, color=TEXT
            ),
            text("• 60% – 80% VRAM wasted by idle slots", font_size=13, color=MUTED),
            text("• Severe external fragmentation failure", font_size=13, color=MUTED),
            text("• Low batch size & throttled throughput", font_size=13, color=MUTED),
        )
        .arrange(DOWN, aligned_edge=LEFT, buff=0.20)
        .move_to(left_panel.get_center() + DOWN * 0.25)
    )
    left_group = VGroup(left_panel, left_hdr, left_items)

    # Right Panel: PagedAttention (The Solution)
    right_panel = panel(
        width=5.7,
        height=3.3,
        fill_color=SURFACE,
        fill_opacity=0.35,
        stroke_color=SUCCESS,
        stroke_width=1.5,
    ).move_to(RIGHT * 3.1 + DOWN * 0.40)
    right_hdr = text(
        "PagedAttention (Virtual Memory)",
        font_size=LABEL_SIZE - 2,
        color=SUCCESS,
        weight="BOLD",
    ).move_to(right_panel.get_top() + DOWN * 0.35)

    right_items = (
        VGroup(
            text("• Dynamic page allocation on demand", font_size=13, color=TEXT),
            text(
                "• Internal fragmentation reduced to < 4%", font_size=13, color=SUCCESS
            ),
            text("• Zero external memory fragmentation", font_size=13, color=SUCCESS),
            text(
                "• 2x – 4x higher serving throughput (vLLM)",
                font_size=13,
                color=ACCENT,
                weight="BOLD",
            ),
        )
        .arrange(DOWN, aligned_edge=LEFT, buff=0.20)
        .move_to(right_panel.get_center() + DOWN * 0.25)
    )
    right_group = VGroup(right_panel, right_hdr, right_items)

    scene.play(
        FadeIn(left_group, shift=RIGHT * 0.2),
        FadeIn(right_group, shift=LEFT * 0.2),
        run_time=1.2,
    )
    scene.wait(0.6)

    # Bottom Takeaway Banner (at DOWN * 2.75, completely clear of video player bar)
    takeaway_text = text(
        "Key Takeaway: Virtual memory paging unlocks true continuous batching at scale",
        font_size=LABEL_SIZE - 3,
        color=ACCENT,
        weight="BOLD",
    )
    takeaway_box = surrounding_panel(
        takeaway_text,
        buff=0.18,
        fill_color=SURFACE,
        fill_opacity=0.9,
        stroke_color=ACCENT,
        stroke_width=2,
    ).move_to(DOWN * 2.75)
    takeaway_text.move_to(takeaway_box)
    takeaway_group = VGroup(takeaway_box, takeaway_text)

    scene.play(FadeIn(takeaway_group, shift=UP * 0.2))
    scene.wait(READ_PAUSE + 0.5)


# -----------------------------------------------------------------------------
# Scene Classes
# -----------------------------------------------------------------------------


class ContiguousFragmentationScene(Scene):
    """Act 1: The Contiguous KV Cache Crisis (~16s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act1(self)


class PagedAttentionArchitectureScene(Scene):
    """Act 2: PagedAttention Architecture (~18s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act2(self)


class DynamicAllocationScene(Scene):
    """Act 3: On-Demand Dynamic Allocation (~18s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act3(self)


class PagedAttentionImpactScene(Scene):
    """Act 4: System Impact & Key Takeaways (~14s)."""

    def construct(self) -> None:
        apply_theme(self)
        run_act4(self)


class PagedAttention(Scene):
    """Master Consolidated Scene linking all acts (~66s)."""

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
        self.wait(1.0)
