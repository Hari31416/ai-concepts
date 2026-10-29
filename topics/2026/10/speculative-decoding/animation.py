"""Manim scenes illustrating the mechanics and mathematics of Speculative Decoding."""

from __future__ import annotations

from manim import (
    BOLD,
    DOWN,
    IN,
    LEFT,
    ORIGIN,
    OUT,
    RIGHT,
    UP,
    AnimationGroup,
    Arrow,
    Brace,
    Circumscribe,
    Create,
    Cross,
    DashedVMobject,
    FadeIn,
    FadeOut,
    GrowArrow,
    Indicate,
    LaggedStart,
    Line,
    MathTex,
    MoveToTarget,
    Rectangle,
    ReplacementTransform,
    RoundedRectangle,
    Scene,
    Square,
    Text,
    Transform,
    VGroup,
    VMobject,
    Write,
    linear,
)

from shared.theme import (
    ACCENT,
    BACKGROUND,
    BODY_SIZE,
    BORDER,
    ENTITY_A,
    ENTITY_B,
    ENTITY_C,
    ERROR,
    FONT,
    GAP,
    LABEL_SIZE,
    MARGIN,
    MATH_SIZE,
    MUTED,
    SUCCESS,
    SURFACE,
    TEXT,
    TITLE_SIZE,
    apply_theme,
    math,
    panel,
    surrounding_panel,
    text,
    title,
)


def make_token_box(
    word: str,
    color: str = TEXT,
    border_color: str = BORDER,
    is_draft: bool = False,
    width: float = 1.25,
    height: float = 0.52,
    font_size: int = 17,
) -> VGroup:
    """Create a stylized token badge with clean theme styling."""
    if is_draft:
        base_rect = RoundedRectangle(
            corner_radius=0.08,
            width=width,
            height=height,
            color=border_color,
            stroke_width=1.8,
            fill_color=border_color,
            fill_opacity=0.10,
        )
        box = DashedVMobject(base_rect, num_dashes=12)
        bg = RoundedRectangle(
            corner_radius=0.08,
            width=width,
            height=height,
            fill_color=border_color,
            fill_opacity=0.08,
            stroke_opacity=0,
        )
        border = VGroup(bg, box)
    else:
        border = RoundedRectangle(
            corner_radius=0.08,
            width=width,
            height=height,
            color=border_color,
            stroke_width=1.8,
            fill_color=border_color,
            fill_opacity=0.20,
        )

    lbl = Text(word, font=FONT, font_size=font_size, color=color, weight=BOLD)
    lbl.move_to(border.get_center())
    return VGroup(border, lbl)


class MemoryBottleneckScene(Scene):
    """Visualizes why single-token autoregressive decoding is memory-bandwidth bound."""

    def construct(self) -> None:
        apply_theme(self)

        scene_title = title("The Memory Bandwidth Bottleneck")
        self.play(Write(scene_title))
        self.wait(0.4)

        hbm_panel = panel(
            width=3.6, height=3.8, fill_color=SURFACE, stroke_color=BORDER
        )
        hbm_panel.move_to(LEFT * 4.2 + UP * 0.3)
        hbm_label = text(
            "GPU Memory (HBM)", font_size=LABEL_SIZE, color=TEXT, weight="BOLD"
        )
        hbm_label.next_to(hbm_panel.get_top(), DOWN, buff=0.25)
        hbm_spec = text("70B Model Weights\n~140 GB (FP16)", font_size=18, color=MUTED)
        hbm_spec.next_to(hbm_label, DOWN, buff=0.15)

        chips = VGroup()
        for _ in range(6):
            chip = RoundedRectangle(
                width=1.2,
                height=0.55,
                corner_radius=0.08,
                fill_color="#1E293B",
                fill_opacity=0.6,
                stroke_color=BORDER,
                stroke_width=1.5,
            )
            chips.add(chip)
        chips.arrange_in_grid(rows=3, cols=2, buff=0.15)
        chips.next_to(hbm_spec, DOWN, buff=0.2)
        hbm_group = VGroup(hbm_panel, hbm_label, hbm_spec, chips)

        compute_panel = panel(
            width=3.6, height=3.8, fill_color=SURFACE, stroke_color=BORDER
        )
        compute_panel.move_to(RIGHT * 4.2 + UP * 0.3)
        compute_label = text(
            "Tensor Cores", font_size=LABEL_SIZE, color=TEXT, weight="BOLD"
        )
        compute_label.next_to(compute_panel.get_top(), DOWN, buff=0.25)
        compute_spec = text(
            "Compute Capacity\n~2,000 TFLOPS", font_size=18, color=MUTED
        )
        compute_spec.next_to(compute_label, DOWN, buff=0.15)

        core_grid = VGroup()
        for _ in range(16):
            core = Rectangle(
                width=0.45,
                height=0.32,
                fill_color="#0F172A",
                fill_opacity=0.8,
                stroke_color=BORDER,
                stroke_width=1.0,
            )
            core_grid.add(core)
        core_grid.arrange_in_grid(rows=4, cols=4, buff=0.12)
        core_grid.next_to(compute_spec, DOWN, buff=0.2)
        compute_group = VGroup(compute_panel, compute_label, compute_spec, core_grid)

        bus_line_top = Line(
            LEFT * 2.4 + UP * 1.25,
            RIGHT * 2.4 + UP * 1.25,
            color=BORDER,
            stroke_width=2,
        )
        bus_line_bot = Line(
            LEFT * 2.4 + UP * 0.15,
            RIGHT * 2.4 + UP * 0.15,
            color=BORDER,
            stroke_width=2,
        )
        bus_label = text("Memory Bus (3.35 TB/s)", font_size=15, color=MUTED)
        bus_label.next_to(bus_line_top, UP, buff=0.1)
        bus_group = VGroup(bus_line_top, bus_line_bot, bus_label)

        self.play(FadeIn(hbm_group), FadeIn(compute_group), FadeIn(bus_group))
        self.wait(0.4)

        transfer_packet = RoundedRectangle(
            width=2.0,
            height=0.55,
            corner_radius=0.08,
            fill_color=ACCENT,
            fill_opacity=0.4,
            stroke_color=ACCENT,
            stroke_width=2,
        ).move_to(LEFT * 1.35 + UP * 0.70)
        packet_label = text("Load 140 GB", font_size=16, color=ACCENT, weight="BOLD")
        packet_label.move_to(transfer_packet)
        packet = VGroup(transfer_packet, packet_label)

        self.play(FadeIn(packet))
        self.play(packet.animate.move_to(RIGHT * 1.35 + UP * 0.70), run_time=1.3)

        token_emitted = RoundedRectangle(
            width=2.1,
            height=0.55,
            corner_radius=0.08,
            fill_color=SURFACE,
            fill_opacity=0.95,
            stroke_color=ENTITY_A,
            stroke_width=2,
        ).move_to(RIGHT * 4.2 + UP * 0.3)
        token_text = text(
            "Token 1 Emitted", font_size=16, color=ENTITY_A, weight="BOLD"
        ).move_to(token_emitted)
        token_group = VGroup(token_emitted, token_text)

        self.play(FadeOut(packet), FadeIn(token_group))
        self.wait(0.4)

        status_box = panel(
            width=11.2, height=1.05, fill_color=SURFACE, stroke_color=BORDER
        )
        status_box.move_to(DOWN * 2.6)
        insight_1 = text(
            "Autoregressive Bottleneck: Full 140 GB loaded for just 1 token!",
            font_size=17,
            color=TEXT,
        )
        insight_2 = text(
            "Arithmetic Intensity is low: Tensor Cores spend ~90% of time idle.",
            font_size=16,
            color=ERROR,
        )
        insight_group = (
            VGroup(insight_1, insight_2).arrange(DOWN, buff=0.10).move_to(status_box)
        )

        self.play(FadeIn(status_box), Write(insight_group))
        self.wait(1.2)

        realization = text(
            "Key Insight: Verifying K tokens in parallel takes nearly the SAME time!",
            font_size=17,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(status_box)

        self.play(ReplacementTransform(insight_group, realization))
        self.wait(2.0)


class SpeculativeLoopScene(Scene):
    """Animates the Draft and explicit Parallel Batch Verification mechanism."""

    def construct(self) -> None:
        apply_theme(self)

        scene_title = title("The Speculative Loop: How Parallel Verification Works")
        self.play(Write(scene_title))
        self.wait(0.4)

        # Top Model Cards
        draft_box = panel(
            width=4.4, height=1.5, fill_color=SURFACE, stroke_color=ENTITY_B
        ).move_to(LEFT * 3.6 + UP * 2.0)
        draft_title = text(
            "Draft Model Mq (Small)", font_size=18, color=ENTITY_B, weight="BOLD"
        )
        draft_desc = text(
            "1B Params • ~2 ms / token\nSequentially guesses candidates",
            font_size=14,
            color=MUTED,
        )
        draft_content = (
            VGroup(draft_title, draft_desc).arrange(DOWN, buff=0.12).move_to(draft_box)
        )
        draft_card = VGroup(draft_box, draft_content)

        target_box = panel(
            width=4.6, height=1.5, fill_color=SURFACE, stroke_color=ENTITY_A
        ).move_to(RIGHT * 3.6 + UP * 2.0)
        target_title = text(
            "Target Model Mp (Large)", font_size=18, color=ENTITY_A, weight="BOLD"
        )
        target_desc = text(
            "70B Params • ~25 ms / pass\nEvaluates full batches in 1 pass",
            font_size=14,
            color=MUTED,
        )
        target_content = (
            VGroup(target_title, target_desc)
            .arrange(DOWN, buff=0.12)
            .move_to(target_box)
        )
        target_card = VGroup(target_box, target_content)

        self.play(FadeIn(draft_card), FadeIn(target_card))
        self.wait(0.3)

        # -------------------------------------------------------------
        # Step 1: Draft model sequentially emits K=4 candidate tokens
        # -------------------------------------------------------------
        p1_label = text(
            "Phase 1: Draft Model sequentially predicts K = 4 candidate tokens",
            font_size=18,
            color=ENTITY_B,
            weight="BOLD",
        ).move_to(UP * 0.7)
        self.play(Write(p1_label))

        prompt_the = make_token_box("The", color=TEXT, border_color=BORDER)
        prompt_quick = make_token_box("quick", color=TEXT, border_color=BORDER)
        prompt_grp = VGroup(prompt_the, prompt_quick).arrange(RIGHT, buff=0.12)

        g1 = make_token_box(
            "brown", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        g2 = make_token_box("fox", color=ENTITY_B, border_color=ENTITY_B, is_draft=True)
        g3 = make_token_box(
            "jumps", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        g4 = make_token_box(
            "under", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        draft_grp = VGroup(g1, g2, g3, g4).arrange(RIGHT, buff=0.12)

        draft_row = (
            VGroup(prompt_grp, draft_grp).arrange(RIGHT, buff=0.12).move_to(DOWN * 0.1)
        )

        self.play(FadeIn(prompt_grp))
        for tok in [g1, g2, g3, g4]:
            self.play(FadeIn(tok, shift=RIGHT * 0.15), run_time=0.25)
        self.wait(0.6)

        self.play(FadeOut(p1_label), FadeOut(draft_card), FadeOut(target_card))

        # -------------------------------------------------------------
        # Step 2: Show the EXACT parallel batch queries formed for Mp
        # -------------------------------------------------------------
        p2_label = text(
            "Phase 2: Target Model verifies ALL prefix queries simultaneously in 1 batch",
            font_size=18,
            color=ENTITY_A,
            weight="BOLD",
        ).move_to(UP * 2.5)
        self.play(Write(p2_label))

        def make_batch_query(
            q_num: int,
            tokens_in: list[tuple[str, bool]],
            pred_word: str,
            prob: str,
            match: bool,
        ) -> VGroup:
            lbl = text(f"Query {q_num}:", font_size=14, color=ACCENT, weight="BOLD")
            boxes = VGroup()
            for w, is_d in tokens_in:
                c = ENTITY_B if is_d else TEXT
                bc = ENTITY_B if is_d else BORDER
                boxes.add(
                    make_token_box(
                        w,
                        color=c,
                        border_color=bc,
                        is_draft=is_d,
                        width=0.95,
                        height=0.40,
                        font_size=13,
                    )
                )
            boxes.arrange(RIGHT, buff=0.08)

            arr = Arrow(
                start=LEFT * 0.25,
                end=RIGHT * 0.25,
                color=ACCENT,
                buff=0.04,
                stroke_width=2.0,
                max_tip_length_to_length_ratio=0.3,
            )

            res_c = SUCCESS if match else ERROR
            pred_badge = make_token_box(
                f"{pred_word} ({prob})",
                color=TEXT,
                border_color=res_c,
                is_draft=False,
                width=1.55,
                height=0.40,
                font_size=12,
            )

            row = VGroup(lbl, boxes, arr, pred_badge).arrange(RIGHT, buff=0.15)
            return row

        q1 = make_batch_query(
            1, [("The", False), ("quick", False)], "brown", "94%", True
        )
        q2 = make_batch_query(
            2, [("The", False), ("quick", False), ("brown", True)], "fox", "91%", True
        )
        q3 = make_batch_query(
            3,
            [("The", False), ("quick", False), ("brown", True), ("fox", True)],
            "jumps",
            "86%",
            True,
        )
        q4 = make_batch_query(
            4,
            [
                ("The", False),
                ("quick", False),
                ("brown", True),
                ("fox", True),
                ("jumps", True),
            ],
            "over",
            "82%",
            False,
        )

        batch_table = (
            VGroup(q1, q2, q3, q4)
            .arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            .move_to(DOWN * 0.3)
        )

        batch_container = panel(
            width=batch_table.width + 0.6,
            height=batch_table.height + 0.45,
            fill_color=SURFACE,
            stroke_color=ENTITY_A,
        ).move_to(batch_table.get_center())

        batch_tag = text(
            "Target Model Parallel Forward Pass (Batch Size = 4)",
            font_size=14,
            color=ENTITY_A,
            weight="BOLD",
        ).next_to(batch_container, UP, buff=0.1)

        self.play(FadeOut(draft_row), run_time=0.3)
        self.play(Create(batch_container), FadeIn(batch_tag))
        self.play(
            LaggedStart(
                FadeIn(q1, shift=RIGHT * 0.15),
                FadeIn(q2, shift=RIGHT * 0.15),
                FadeIn(q3, shift=RIGHT * 0.15),
                FadeIn(q4, shift=RIGHT * 0.15),
                lag_ratio=0.15,
            ),
            run_time=1.2,
        )
        self.wait(1.0)

        # Callout banner: 70B loaded once to evaluate all 4 queries
        pass_banner = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=ENTITY_A
        ).move_to(DOWN * 2.6)
        pass_text = text(
            "1 Forward Pass (28 ms): 70B weights loaded ONCE to evaluate all 4 queries in parallel!",
            font_size=16,
            color=ENTITY_A,
            weight="BOLD",
        ).move_to(pass_banner)
        self.play(FadeIn(pass_banner), Write(pass_text))
        self.wait(1.8)

        # -------------------------------------------------------------
        # Step 3: Compare Batch Outputs -> Get the Verified Tokens
        # -------------------------------------------------------------
        self.play(
            FadeOut(p2_label),
            FadeOut(batch_container),
            FadeOut(batch_tag),
            FadeOut(batch_table),
            FadeOut(pass_banner),
            FadeOut(pass_text),
            run_time=0.5,
        )

        p3_label = text(
            "Phase 3: Accept Matches • First Mismatch Corrected by Target Model",
            font_size=18,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(UP * 2.2)
        self.play(Write(p3_label))

        # Re-display candidate tokens
        final_the = make_token_box("The", color=TEXT, border_color=BORDER)
        final_quick = make_token_box("quick", color=TEXT, border_color=BORDER)
        fg1 = make_token_box(
            "brown", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg2 = make_token_box(
            "fox", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg3 = make_token_box(
            "jumps", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg4 = make_token_box(
            "under", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )

        final_row = (
            VGroup(final_the, final_quick, fg1, fg2, fg3, fg4)
            .arrange(RIGHT, buff=0.20)
            .move_to(DOWN * 0.4)
        )
        row_lbl = text("Draft Candidate Tokens:", font_size=15, color=MUTED).next_to(
            final_row, DOWN, buff=0.3
        )
        self.play(FadeIn(final_row), FadeIn(row_lbl))

        # Show Target Model outputs above each candidate
        t1 = make_token_box(
            "brown (94%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg1, UP, buff=0.65)
        t2 = make_token_box(
            "fox (91%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg2, UP, buff=0.65)
        t3 = make_token_box(
            "jumps (86%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg3, UP, buff=0.65)
        t4 = make_token_box(
            "over (82%)",
            color=TEXT,
            border_color=ERROR,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg4, UP, buff=0.65)
        t_outputs = VGroup(t1, t2, t3, t4)
        t_label = (
            text(
                "Target Model Outputs from Parallel Pass:",
                font_size=15,
                color=ENTITY_A,
                weight="BOLD",
            )
            .next_to(t_outputs, UP, buff=0.25)
            .align_to(t_outputs, LEFT)
        )

        self.play(FadeIn(t_label), FadeIn(t_outputs))
        self.wait(0.5)

        # Acceptance checkmarks
        def make_check(tok: VGroup) -> Text:
            c = text("✓", font_size=20, color=SUCCESS, weight="BOLD")
            c.next_to(tok, DOWN, buff=0.12)
            return c

        def make_cross(tok: VGroup) -> Text:
            c = text("✗", font_size=20, color=ERROR, weight="BOLD")
            c.next_to(tok, DOWN, buff=0.12)
            return c

        c1 = make_check(fg1)
        c2 = make_check(fg2)
        c3 = make_check(fg3)
        cr4 = make_cross(fg4)

        # Accept brown, fox, jumps
        v1 = make_token_box("brown", color=TEXT, border_color=SUCCESS).move_to(fg1)
        v2 = make_token_box("fox", color=TEXT, border_color=SUCCESS).move_to(fg2)
        v3 = make_token_box("jumps", color=TEXT, border_color=SUCCESS).move_to(fg3)

        self.play(
            FadeIn(c1),
            FadeIn(c2),
            FadeIn(c3),
            ReplacementTransform(fg1, v1),
            ReplacementTransform(fg2, v2),
            ReplacementTransform(fg3, v3),
            run_time=0.8,
        )
        self.wait(0.3)

        # Reject "under" and correct to target's "over"
        self.play(FadeIn(cr4), fg4.animate.set_stroke(color=ERROR))
        self.wait(0.3)

        v4_corrected = make_token_box(
            "over", color=TEXT, border_color=ENTITY_A
        ).move_to(fg4)
        v4_tag = text(
            "Target Prediction Adopted", font_size=12, color=ENTITY_A, weight="BOLD"
        ).next_to(v4_corrected, DOWN, buff=0.2)

        self.play(
            FadeOut(fg4),
            FadeOut(cr4),
            FadeIn(v4_corrected),
            FadeIn(v4_tag),
            FadeOut(row_lbl),
            run_time=0.6,
        )
        self.wait(0.6)

        summary_panel = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=SUCCESS
        ).move_to(DOWN * 2.6)
        summary_msg = text(
            'Outcome: 4 verified tokens ["brown", "fox", "jumps", "over"] emitted from 1 target step!',
            font_size=16,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(summary_panel)
        self.play(FadeIn(summary_panel), Write(summary_msg))
        self.wait(2.2)


class RejectionSamplingScene(Scene):
    """Visualizes why speculative decoding is mathematically lossless."""

    def construct(self) -> None:
        apply_theme(self)

        scene_title = title("Exact Distribution Preservation")
        self.play(Write(scene_title))
        self.wait(0.4)

        formula = math(
            r"P(X = x) = \min(q(x), p(x)) + \max(0, p(x) - q(x)) = p(x)", font_size=26
        )
        formula.next_to(scene_title, DOWN, buff=0.25)
        self.play(FadeIn(formula))
        self.wait(0.4)

        vocab = ["A", "B", "C", "D"]
        p_vals = [0.60, 0.25, 0.10, 0.05]
        q_vals = [0.40, 0.40, 0.10, 0.10]

        base_line = Line(
            LEFT * 4.4 + DOWN * 1.5,
            RIGHT * 2.2 + DOWN * 1.5,
            color=BORDER,
            stroke_width=2,
        )
        self.play(Create(base_line))

        scale_h = 4.0
        col_width = 1.15
        spacing = 1.5
        start_x = -3.2

        bar_groups = VGroup()
        labels_group = VGroup()

        for idx, token_name in enumerate(vocab):
            p = p_vals[idx]
            q = q_vals[idx]
            overlap = min(p, q)
            residual_p = max(0.0, p - q)
            surplus_q = max(0.0, q - p)

            col_center_x = start_x + idx * spacing

            h_overlap = overlap * scale_h
            bar_overlap = Rectangle(
                width=col_width,
                height=h_overlap,
                fill_color=SUCCESS,
                fill_opacity=0.7,
                stroke_color=BORDER,
                stroke_width=1.5,
            ).move_to([col_center_x, -1.5 + h_overlap / 2.0, 0])

            if residual_p > 0:
                h_res = residual_p * scale_h
                bar_res = Rectangle(
                    width=col_width,
                    height=h_res,
                    fill_color=ENTITY_A,
                    fill_opacity=0.75,
                    stroke_color=BORDER,
                    stroke_width=1.5,
                ).move_to([col_center_x, -1.5 + h_overlap + h_res / 2.0, 0])
                bar_col = VGroup(bar_overlap, bar_res)
            elif surplus_q > 0:
                h_surplus = surplus_q * scale_h
                bar_surplus = Rectangle(
                    width=col_width,
                    height=h_surplus,
                    fill_color=ERROR,
                    fill_opacity=0.4,
                    stroke_color=ERROR,
                    stroke_width=1.5,
                ).move_to([col_center_x, -1.5 + h_overlap + h_surplus / 2.0, 0])
                bar_col = VGroup(bar_overlap, bar_surplus)
            else:
                bar_col = VGroup(bar_overlap)

            tok_lbl = text(f'"{token_name}"', font_size=19, color=TEXT, weight="BOLD")
            tok_lbl.move_to([col_center_x, -1.8, 0])
            labels_group.add(tok_lbl)
            bar_groups.add(bar_col)

        self.play(FadeIn(bar_groups), FadeIn(labels_group))
        self.wait(0.6)

        legend_box = panel(
            width=3.6, height=2.3, fill_color=SURFACE, stroke_color=BORDER
        ).move_to(RIGHT * 4.4 + DOWN * 0.2)

        leg_title = text(
            "Probability Breakdown", font_size=17, color=TEXT, weight="BOLD"
        )

        dot1 = Rectangle(
            width=0.32,
            height=0.20,
            fill_color=SUCCESS,
            fill_opacity=0.8,
            stroke_width=0,
        )
        desc1 = text("Accepted: min(p, q)", font_size=14, color=SUCCESS)
        item1 = VGroup(dot1, desc1).arrange(RIGHT, buff=0.12)

        dot2 = Rectangle(
            width=0.32,
            height=0.20,
            fill_color=ENTITY_A,
            fill_opacity=0.8,
            stroke_width=0,
        )
        desc2 = text("Resampled: max(0, p - q)", font_size=14, color=ENTITY_A)
        item2 = VGroup(dot2, desc2).arrange(RIGHT, buff=0.12)

        dot3 = Rectangle(
            width=0.32, height=0.20, fill_color=ERROR, fill_opacity=0.5, stroke_width=0
        )
        desc3 = text("Rejected Draft: max(0, q - p)", font_size=14, color=ERROR)
        item3 = VGroup(dot3, desc3).arrange(RIGHT, buff=0.12)

        legend_items = VGroup(item1, item2, item3).arrange(
            DOWN, aligned_edge=LEFT, buff=0.16
        )
        legend_content = (
            VGroup(leg_title, legend_items)
            .arrange(DOWN, aligned_edge=LEFT, buff=0.20)
            .move_to(legend_box)
        )
        legend_group = VGroup(legend_box, legend_content)

        self.play(FadeIn(legend_group))
        self.wait(1.0)

        bracket_a = Brace(bar_groups[0], LEFT, color=ENTITY_A)
        label_a = text("Sum = p(A) = 0.60", font_size=15, color=ENTITY_A).next_to(
            bracket_a, LEFT, buff=0.1
        )
        self.play(Create(bracket_a), FadeIn(label_a))
        self.wait(1.0)

        guarantee_panel = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=SUCCESS
        )
        guarantee_panel.move_to(DOWN * 2.6)
        guarantee_text = text(
            "Zero approximation: Speculative Sampling is mathematically lossless!",
            font_size=17,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(guarantee_panel)

        self.play(FadeIn(guarantee_panel), Write(guarantee_text))
        self.wait(2.0)


class SpeedupComparisonScene(Scene):
    """Visualizes the wall-clock execution timeline speedup."""

    def construct(self) -> None:
        apply_theme(self)

        scene_title = title("Wall-Clock Speedup: Standard vs Speculative")
        self.play(Write(scene_title))
        self.wait(0.4)

        row1_label = text(
            "Standard Autoregressive (4 Tokens)",
            font_size=18,
            color=MUTED,
            weight="BOLD",
        )
        row1_label.move_to(LEFT * 3.3 + UP * 1.6)
        self.play(FadeIn(row1_label))

        blocks_ar = VGroup()
        for i in range(4):
            b = RoundedRectangle(
                width=1.7,
                height=0.75,
                corner_radius=0.08,
                fill_color=ENTITY_A,
                fill_opacity=0.3,
                stroke_color=ENTITY_A,
                stroke_width=2,
            )
            t = text(f"Pass {i+1}", font_size=16, color=TEXT).move_to(b)
            blocks_ar.add(VGroup(b, t))
        blocks_ar.arrange(RIGHT, buff=0.12)
        blocks_ar.next_to(row1_label, DOWN, buff=0.2).align_to(LEFT * 5.8, LEFT)
        row1_label.align_to(blocks_ar, LEFT)

        ar_brace = Brace(blocks_ar, DOWN, color=MUTED)
        ar_time = text(
            "Total Latency: 4.0 × T_target", font_size=16, color=MUTED
        ).next_to(ar_brace, DOWN, buff=0.08)

        self.play(FadeIn(blocks_ar), Create(ar_brace), FadeIn(ar_time))
        self.wait(0.8)

        row2_label = text(
            "Speculative Decoding (4 Tokens)",
            font_size=18,
            color=SUCCESS,
            weight="BOLD",
        )
        row2_label.move_to(LEFT * 3.5 + DOWN * 0.7)
        self.play(FadeIn(row2_label))

        draft_blocks = VGroup()
        for i in range(3):
            db = RoundedRectangle(
                width=0.38,
                height=0.75,
                corner_radius=0.06,
                fill_color=ENTITY_B,
                fill_opacity=0.5,
                stroke_color=ENTITY_B,
                stroke_width=1.5,
            )
            dt = text(f"q{i+1}", font_size=13, color=TEXT).move_to(db)
            draft_blocks.add(VGroup(db, dt))
        draft_blocks.arrange(RIGHT, buff=0.06)

        verify_box = RoundedRectangle(
            width=1.7,
            height=0.75,
            corner_radius=0.08,
            fill_color=ENTITY_A,
            fill_opacity=0.45,
            stroke_color=ENTITY_A,
            stroke_width=2,
        )
        verify_txt = text(
            "Verify All", font_size=15, color=ENTITY_A, weight="BOLD"
        ).move_to(verify_box)
        verify_block = VGroup(verify_box, verify_txt)

        spec_blocks = VGroup(draft_blocks, verify_block).arrange(RIGHT, buff=0.12)
        spec_blocks.next_to(row2_label, DOWN, buff=0.2).align_to(LEFT * 5.8, LEFT)
        row2_label.align_to(spec_blocks, LEFT)

        spec_brace = Brace(spec_blocks, DOWN, color=SUCCESS)
        spec_time = text(
            "Total Latency: ~1.4 × T_target", font_size=16, color=SUCCESS, weight="BOLD"
        ).next_to(spec_brace, DOWN, buff=0.08)

        self.play(FadeIn(spec_blocks), Create(spec_brace), FadeIn(spec_time))
        self.wait(1.0)

        callout_box = panel(
            width=3.2, height=2.5, fill_color=SURFACE, stroke_color=ACCENT
        )
        callout_box.move_to(RIGHT * 4.6 + DOWN * 0.2)

        metric_num = text("2.8×", font_size=46, color=ACCENT, weight="BOLD")
        metric_lbl = text("Latency Speedup", font_size=18, color=TEXT, weight="BOLD")
        metric_sub = text(
            "Same Token Output\nIdentical Perplexity\nZero Fine-Tuning",
            font_size=14,
            color=MUTED,
        )

        metric_group = (
            VGroup(metric_num, metric_lbl, metric_sub)
            .arrange(DOWN, buff=0.15)
            .move_to(callout_box)
        )
        self.play(FadeIn(callout_box), FadeIn(metric_group))
        self.play(Circumscribe(metric_num, color=ACCENT, run_time=1.2))
        self.wait(2.0)


class SpeculativeDecoding(Scene):
    """Consolidated video walking through all phases of speculative decoding."""

    def construct(self) -> None:
        apply_theme(self)

        # ---------------------------------------------------------
        # Act 1: The Memory Bandwidth Bottleneck
        # ---------------------------------------------------------
        p1_title = title("1. The Memory Bandwidth Bottleneck")
        self.play(Write(p1_title))

        hbm_panel = panel(
            width=3.6, height=3.6, fill_color=SURFACE, stroke_color=BORDER
        ).move_to(LEFT * 4.2 + UP * 0.2)
        hbm_lbl = text(
            "GPU Memory (HBM)", font_size=LABEL_SIZE, color=TEXT, weight="BOLD"
        ).next_to(hbm_panel.get_top(), DOWN, buff=0.25)
        hbm_desc = text(
            "70B Model Weights\n~140 GB (FP16)", font_size=18, color=MUTED
        ).next_to(hbm_lbl, DOWN, buff=0.15)

        chips = VGroup()
        for _ in range(6):
            chips.add(
                RoundedRectangle(
                    width=1.2,
                    height=0.5,
                    corner_radius=0.08,
                    fill_color="#1E293B",
                    fill_opacity=0.6,
                    stroke_color=BORDER,
                    stroke_width=1.5,
                )
            )
        chips.arrange_in_grid(rows=3, cols=2, buff=0.15).next_to(
            hbm_desc, DOWN, buff=0.2
        )
        hbm_group = VGroup(hbm_panel, hbm_lbl, hbm_desc, chips)

        compute_panel = panel(
            width=3.6, height=3.6, fill_color=SURFACE, stroke_color=BORDER
        ).move_to(RIGHT * 4.2 + UP * 0.2)
        compute_lbl = text(
            "Tensor Cores", font_size=LABEL_SIZE, color=TEXT, weight="BOLD"
        ).next_to(compute_panel.get_top(), DOWN, buff=0.25)
        compute_desc = text(
            "Compute Capacity\n~2,000 TFLOPS", font_size=18, color=MUTED
        ).next_to(compute_lbl, DOWN, buff=0.15)

        core_grid = VGroup()
        for _ in range(16):
            core_grid.add(
                Rectangle(
                    width=0.45,
                    height=0.3,
                    fill_color="#0F172A",
                    fill_opacity=0.8,
                    stroke_color=BORDER,
                    stroke_width=1.0,
                )
            )
        core_grid.arrange_in_grid(rows=4, cols=4, buff=0.12).next_to(
            compute_desc, DOWN, buff=0.2
        )
        compute_group = VGroup(compute_panel, compute_lbl, compute_desc, core_grid)

        bus_line_top = Line(
            LEFT * 2.4 + UP * 1.2, RIGHT * 2.4 + UP * 1.2, color=BORDER, stroke_width=2
        )
        bus_line_bot = Line(
            LEFT * 2.4 + UP * 0.1, RIGHT * 2.4 + UP * 0.1, color=BORDER, stroke_width=2
        )
        bus_lbl = text("Memory Bus (3.35 TB/s)", font_size=15, color=MUTED).next_to(
            bus_line_top, UP, buff=0.1
        )
        bus_group = VGroup(bus_line_top, bus_line_bot, bus_lbl)

        self.play(FadeIn(hbm_group), FadeIn(compute_group), FadeIn(bus_group))

        transfer_packet = RoundedRectangle(
            width=2.0,
            height=0.55,
            corner_radius=0.08,
            fill_color=ACCENT,
            fill_opacity=0.4,
            stroke_color=ACCENT,
            stroke_width=2,
        ).move_to(LEFT * 1.35 + UP * 0.65)
        packet_lbl = text(
            "Load 140 GB", font_size=16, color=ACCENT, weight="BOLD"
        ).move_to(transfer_packet)
        packet = VGroup(transfer_packet, packet_lbl)

        self.play(FadeIn(packet))
        self.play(packet.animate.move_to(RIGHT * 1.35 + UP * 0.65), run_time=1.2)

        token_emitted = RoundedRectangle(
            width=2.1,
            height=0.55,
            corner_radius=0.08,
            fill_color=SURFACE,
            fill_opacity=0.95,
            stroke_color=ENTITY_A,
            stroke_width=2,
        ).move_to(RIGHT * 4.2 + UP * 0.2)
        token_txt = text(
            "Token 1 Emitted", font_size=16, color=ENTITY_A, weight="BOLD"
        ).move_to(token_emitted)
        token_group = VGroup(token_emitted, token_txt)

        self.play(FadeOut(packet), FadeIn(token_group))

        p1_banner = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=SUCCESS
        ).move_to(DOWN * 2.6)
        p1_msg = text(
            "Insight: Tensor cores are starved! Parallel verification of K tokens takes almost the same time.",
            font_size=16,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(p1_banner)
        self.play(FadeIn(p1_banner), Write(p1_msg))
        self.wait(1.8)

        p1_all = VGroup(
            p1_title,
            hbm_group,
            compute_group,
            bus_group,
            token_group,
            p1_banner,
            p1_msg,
        )
        self.play(FadeOut(p1_all))

        # ---------------------------------------------------------
        # Act 2: The Speculative Loop with Parallel Query Batching
        # ---------------------------------------------------------
        p2_title = title("2. The Speculative Loop: Parallel Verification")
        self.play(Write(p2_title))

        p2_sub = text(
            "Phase 1: Draft Model sequentially predicts K = 4 candidate tokens",
            font_size=18,
            color=ENTITY_B,
            weight="BOLD",
        ).move_to(UP * 2.2)
        self.play(Write(p2_sub))

        prompt_the = make_token_box("The", color=TEXT, border_color=BORDER)
        prompt_quick = make_token_box("quick", color=TEXT, border_color=BORDER)
        prompt_grp = VGroup(prompt_the, prompt_quick).arrange(RIGHT, buff=0.12)

        g1 = make_token_box(
            "brown", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        g2 = make_token_box("fox", color=ENTITY_B, border_color=ENTITY_B, is_draft=True)
        g3 = make_token_box(
            "jumps", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        g4 = make_token_box(
            "under", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        draft_grp = VGroup(g1, g2, g3, g4).arrange(RIGHT, buff=0.12)

        draft_row = (
            VGroup(prompt_grp, draft_grp).arrange(RIGHT, buff=0.12).move_to(UP * 0.8)
        )

        self.play(FadeIn(prompt_grp))
        for tok in [g1, g2, g3, g4]:
            self.play(FadeIn(tok, shift=RIGHT * 0.15), run_time=0.25)
        self.wait(0.5)

        self.play(FadeOut(p2_sub))
        p2_batch_title = text(
            "Phase 2: Target Model verifies ALL prefix queries simultaneously in 1 batch",
            font_size=18,
            color=ENTITY_A,
            weight="BOLD",
        ).move_to(UP * 2.2)
        self.play(Write(p2_batch_title))

        def make_batch_row_master(
            q_num: int,
            tokens_in: list[tuple[str, bool]],
            pred_word: str,
            prob: str,
            match: bool,
        ) -> VGroup:
            lbl = text(f"Query {q_num}:", font_size=13, color=ACCENT, weight="BOLD")
            boxes = VGroup()
            for w, is_d in tokens_in:
                c = ENTITY_B if is_d else TEXT
                bc = ENTITY_B if is_d else BORDER
                boxes.add(
                    make_token_box(
                        w,
                        color=c,
                        border_color=bc,
                        is_draft=is_d,
                        width=0.92,
                        height=0.38,
                        font_size=12,
                    )
                )
            boxes.arrange(RIGHT, buff=0.08)

            arr = Arrow(
                start=LEFT * 0.22,
                end=RIGHT * 0.22,
                color=ACCENT,
                buff=0.04,
                stroke_width=1.8,
                max_tip_length_to_length_ratio=0.3,
            )

            res_c = SUCCESS if match else ERROR
            pred_badge = make_token_box(
                f"{pred_word} ({prob})",
                color=TEXT,
                border_color=res_c,
                is_draft=False,
                width=1.45,
                height=0.38,
                font_size=11,
            )

            row = VGroup(lbl, boxes, arr, pred_badge).arrange(RIGHT, buff=0.14)
            return row

        q1 = make_batch_row_master(
            1, [("The", False), ("quick", False)], "brown", "94%", True
        )
        q2 = make_batch_row_master(
            2, [("The", False), ("quick", False), ("brown", True)], "fox", "91%", True
        )
        q3 = make_batch_row_master(
            3,
            [("The", False), ("quick", False), ("brown", True), ("fox", True)],
            "jumps",
            "86%",
            True,
        )
        q4 = make_batch_row_master(
            4,
            [
                ("The", False),
                ("quick", False),
                ("brown", True),
                ("fox", True),
                ("jumps", True),
            ],
            "over",
            "82%",
            False,
        )

        batch_table = (
            VGroup(q1, q2, q3, q4)
            .arrange(DOWN, buff=0.16, aligned_edge=LEFT)
            .move_to(DOWN * 0.5)
        )

        batch_container = panel(
            width=batch_table.width + 0.5,
            height=batch_table.height + 0.4,
            fill_color=SURFACE,
            stroke_color=ENTITY_A,
        ).move_to(batch_table.get_center())

        batch_tag = text(
            "Target Model Single Parallel Batch (Batch Size = 4)",
            font_size=13,
            color=ENTITY_A,
            weight="BOLD",
        ).next_to(batch_container, UP, buff=0.08)

        self.play(FadeOut(draft_row), run_time=0.3)
        self.play(Create(batch_container), FadeIn(batch_tag))
        self.play(
            LaggedStart(
                FadeIn(q1, shift=RIGHT * 0.15),
                FadeIn(q2, shift=RIGHT * 0.15),
                FadeIn(q3, shift=RIGHT * 0.15),
                FadeIn(q4, shift=RIGHT * 0.15),
                lag_ratio=0.12,
            ),
            run_time=1.0,
        )
        self.wait(1.0)

        # Transition to Phase 3: Verification
        self.play(
            FadeOut(p2_batch_title),
            FadeOut(batch_container),
            FadeOut(batch_tag),
            FadeOut(batch_table),
            run_time=0.5,
        )

        p2_verif_title = text(
            "Phase 3: Accept Matches • First Mismatch Corrected by Target Model",
            font_size=18,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(UP * 2.2)
        self.play(Write(p2_verif_title))

        final_the = make_token_box("The", color=TEXT, border_color=BORDER)
        final_quick = make_token_box("quick", color=TEXT, border_color=BORDER)
        fg1 = make_token_box(
            "brown", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg2 = make_token_box(
            "fox", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg3 = make_token_box(
            "jumps", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )
        fg4 = make_token_box(
            "under", color=ENTITY_B, border_color=ENTITY_B, is_draft=True
        )

        final_row = (
            VGroup(final_the, final_quick, fg1, fg2, fg3, fg4)
            .arrange(RIGHT, buff=0.20)
            .move_to(DOWN * 0.4)
        )
        self.play(FadeIn(final_row))

        t1 = make_token_box(
            "brown (94%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg1, UP, buff=0.65)
        t2 = make_token_box(
            "fox (91%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg2, UP, buff=0.65)
        t3 = make_token_box(
            "jumps (86%)",
            color=TEXT,
            border_color=SUCCESS,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg3, UP, buff=0.65)
        t4 = make_token_box(
            "over (82%)",
            color=TEXT,
            border_color=ERROR,
            width=1.35,
            height=0.42,
            font_size=12,
        ).next_to(fg4, UP, buff=0.65)
        t_outputs = VGroup(t1, t2, t3, t4)
        t_label = (
            text(
                "Target Model Outputs from Parallel Pass:",
                font_size=15,
                color=ENTITY_A,
                weight="BOLD",
            )
            .next_to(t_outputs, UP, buff=0.25)
            .align_to(t_outputs, LEFT)
        )
        self.play(FadeIn(t_label), FadeIn(t_outputs))

        def make_chk(tok: VGroup) -> Text:
            c = text("✓", font_size=20, color=SUCCESS, weight="BOLD")
            c.next_to(tok, DOWN, buff=0.12)
            return c

        def make_crs(tok: VGroup) -> Text:
            c = text("✗", font_size=20, color=ERROR, weight="BOLD")
            c.next_to(tok, DOWN, buff=0.12)
            return c

        c1 = make_chk(fg1)
        c2 = make_chk(fg2)
        c3 = make_chk(fg3)
        cr4 = make_crs(fg4)

        v1 = make_token_box("brown", color=TEXT, border_color=SUCCESS).move_to(fg1)
        v2 = make_token_box("fox", color=TEXT, border_color=SUCCESS).move_to(fg2)
        v3 = make_token_box("jumps", color=TEXT, border_color=SUCCESS).move_to(fg3)

        self.play(
            FadeIn(c1),
            FadeIn(c2),
            FadeIn(c3),
            ReplacementTransform(fg1, v1),
            ReplacementTransform(fg2, v2),
            ReplacementTransform(fg3, v3),
            run_time=0.8,
        )

        self.play(FadeIn(cr4), fg4.animate.set_stroke(color=ERROR))

        v4_corrected = make_token_box(
            "over", color=TEXT, border_color=ENTITY_A
        ).move_to(fg4)
        v4_tag = text(
            "Target Prediction Adopted", font_size=12, color=ENTITY_A, weight="BOLD"
        ).next_to(v4_corrected, DOWN, buff=0.2)
        self.play(
            FadeOut(fg4),
            FadeOut(cr4),
            FadeIn(v4_corrected),
            FadeIn(v4_tag),
            run_time=0.6,
        )

        p2_banner = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=SUCCESS
        ).move_to(DOWN * 2.6)
        p2_msg = text(
            'Outcome: 4 verified tokens ["brown", "fox", "jumps", "over"] emitted from 1 target step!',
            font_size=16,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(p2_banner)
        self.play(FadeIn(p2_banner), Write(p2_msg))
        self.wait(1.8)

        p2_all = VGroup(
            p2_title,
            p2_verif_title,
            final_the,
            final_quick,
            v1,
            v2,
            v3,
            v4_corrected,
            v4_tag,
            t_label,
            t_outputs,
            c1,
            c2,
            c3,
            p2_banner,
            p2_msg,
        )
        self.play(FadeOut(p2_all))

        # ---------------------------------------------------------
        # Act 3: Exact Distribution Preservation
        # ---------------------------------------------------------
        p3_title = title("3. Zero Quality Loss: Exact Target Distribution")
        self.play(Write(p3_title))

        formula = math(
            r"P(X = x) = \min(q(x), p(x)) + \max(0, p(x) - q(x)) = p(x)", font_size=25
        ).next_to(p3_title, DOWN, buff=0.25)
        self.play(FadeIn(formula))

        vocab = ["A", "B", "C", "D"]
        p_vals = [0.60, 0.25, 0.10, 0.05]
        q_vals = [0.40, 0.40, 0.10, 0.10]

        base_line = Line(
            LEFT * 4.4 + DOWN * 1.5,
            RIGHT * 2.2 + DOWN * 1.5,
            color=BORDER,
            stroke_width=2,
        )
        self.play(Create(base_line))

        scale_h = 3.8
        col_width = 1.15
        spacing = 1.5
        start_x = -3.2

        bar_groups = VGroup()
        labels_group = VGroup()

        for idx, token_name in enumerate(vocab):
            p = p_vals[idx]
            q = q_vals[idx]
            overlap = min(p, q)
            residual_p = max(0.0, p - q)
            surplus_q = max(0.0, q - p)
            col_center_x = start_x + idx * spacing

            h_overlap = overlap * scale_h
            bar_overlap = Rectangle(
                width=col_width,
                height=h_overlap,
                fill_color=SUCCESS,
                fill_opacity=0.7,
                stroke_color=BORDER,
                stroke_width=1.5,
            ).move_to([col_center_x, -1.5 + h_overlap / 2.0, 0])

            if residual_p > 0:
                h_res = residual_p * scale_h
                bar_res = Rectangle(
                    width=col_width,
                    height=h_res,
                    fill_color=ENTITY_A,
                    fill_opacity=0.75,
                    stroke_color=BORDER,
                    stroke_width=1.5,
                ).move_to([col_center_x, -1.5 + h_overlap + h_res / 2.0, 0])
                bar_col = VGroup(bar_overlap, bar_res)
            elif surplus_q > 0:
                h_surplus = surplus_q * scale_h
                bar_surplus = Rectangle(
                    width=col_width,
                    height=h_surplus,
                    fill_color=ERROR,
                    fill_opacity=0.4,
                    stroke_color=ERROR,
                    stroke_width=1.5,
                ).move_to([col_center_x, -1.5 + h_overlap + h_surplus / 2.0, 0])
                bar_col = VGroup(bar_overlap, bar_surplus)
            else:
                bar_col = VGroup(bar_overlap)

            tok_lbl = text(
                f'"{token_name}"', font_size=19, color=TEXT, weight="BOLD"
            ).move_to([col_center_x, -1.8, 0])
            labels_group.add(tok_lbl)
            bar_groups.add(bar_col)

        self.play(FadeIn(bar_groups), FadeIn(labels_group))

        legend_box = panel(
            width=3.6, height=2.3, fill_color=SURFACE, stroke_color=BORDER
        ).move_to(RIGHT * 4.4 + DOWN * 0.2)
        leg_title = text(
            "Probability Breakdown", font_size=17, color=TEXT, weight="BOLD"
        )

        d1 = Rectangle(
            width=0.32,
            height=0.20,
            fill_color=SUCCESS,
            fill_opacity=0.8,
            stroke_width=0,
        )
        t1 = text("Accepted: min(p, q)", font_size=14, color=SUCCESS)
        i1 = VGroup(d1, t1).arrange(RIGHT, buff=0.12)

        d2 = Rectangle(
            width=0.32,
            height=0.20,
            fill_color=ENTITY_A,
            fill_opacity=0.8,
            stroke_width=0,
        )
        t2 = text("Resampled: max(0, p - q)", font_size=14, color=ENTITY_A)
        i2 = VGroup(d2, t2).arrange(RIGHT, buff=0.12)

        d3 = Rectangle(
            width=0.32, height=0.20, fill_color=ERROR, fill_opacity=0.5, stroke_width=0
        )
        t3 = text("Rejected: max(0, q - p)", font_size=14, color=ERROR)
        i3 = VGroup(d3, t3).arrange(RIGHT, buff=0.12)

        legend_items = VGroup(i1, i2, i3).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        legend_content = (
            VGroup(leg_title, legend_items)
            .arrange(DOWN, aligned_edge=LEFT, buff=0.20)
            .move_to(legend_box)
        )
        legend_grp = VGroup(legend_box, legend_content)
        self.play(FadeIn(legend_grp))

        bracket_a = Brace(bar_groups[0], LEFT, color=ENTITY_A)
        label_a = text("Sum = p(A) = 0.60", font_size=15, color=ENTITY_A).next_to(
            bracket_a, LEFT, buff=0.1
        )
        self.play(Create(bracket_a), FadeIn(label_a))

        p3_banner = panel(
            width=11.2, height=0.85, fill_color=SURFACE, stroke_color=SUCCESS
        ).move_to(DOWN * 2.6)
        p3_msg = text(
            "Lossless Guarantee: Output distribution matches the target model exactly.",
            font_size=17,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(p3_banner)
        self.play(FadeIn(p3_banner), Write(p3_msg))
        self.wait(1.8)

        p3_all = VGroup(
            p3_title,
            formula,
            base_line,
            bar_groups,
            labels_group,
            legend_grp,
            bracket_a,
            label_a,
            p3_banner,
            p3_msg,
        )
        self.play(FadeOut(p3_all))

        # ---------------------------------------------------------
        # Act 4: Wall-Clock Speedup Timeline
        # ---------------------------------------------------------
        p4_title = title("4. Wall-Clock Speedup: Standard vs Speculative")
        self.play(Write(p4_title))

        row1_lbl = text(
            "Standard Autoregressive (4 Tokens)",
            font_size=18,
            color=MUTED,
            weight="BOLD",
        ).move_to(LEFT * 3.3 + UP * 1.6)
        blocks_ar = VGroup()
        for i in range(4):
            b = RoundedRectangle(
                width=1.7,
                height=0.75,
                corner_radius=0.08,
                fill_color=ENTITY_A,
                fill_opacity=0.3,
                stroke_color=ENTITY_A,
                stroke_width=2,
            )
            t = text(f"Pass {i+1}", font_size=16, color=TEXT).move_to(b)
            blocks_ar.add(VGroup(b, t))
        blocks_ar.arrange(RIGHT, buff=0.12).next_to(row1_lbl, DOWN, buff=0.2).align_to(
            LEFT * 5.8, LEFT
        )
        row1_lbl.align_to(blocks_ar, LEFT)

        ar_brace = Brace(blocks_ar, DOWN, color=MUTED)
        ar_time = text(
            "Total Latency: 4.0 × T_target", font_size=16, color=MUTED
        ).next_to(ar_brace, DOWN, buff=0.08)
        self.play(
            FadeIn(row1_lbl), FadeIn(blocks_ar), Create(ar_brace), FadeIn(ar_time)
        )

        row2_lbl = text(
            "Speculative Decoding (4 Tokens)",
            font_size=18,
            color=SUCCESS,
            weight="BOLD",
        ).move_to(LEFT * 3.5 + DOWN * 0.7)
        draft_blocks = VGroup()
        for i in range(3):
            db = RoundedRectangle(
                width=0.38,
                height=0.75,
                corner_radius=0.06,
                fill_color=ENTITY_B,
                fill_opacity=0.5,
                stroke_color=ENTITY_B,
                stroke_width=1.5,
            )
            dt = text(f"q{i+1}", font_size=13, color=TEXT).move_to(db)
            draft_blocks.add(VGroup(db, dt))
        draft_blocks.arrange(RIGHT, buff=0.06)

        verify_box = RoundedRectangle(
            width=1.7,
            height=0.75,
            corner_radius=0.08,
            fill_color=ENTITY_A,
            fill_opacity=0.45,
            stroke_color=ENTITY_A,
            stroke_width=2,
        )
        verify_txt = text(
            "Verify All", font_size=15, color=ENTITY_A, weight="BOLD"
        ).move_to(verify_box)
        verify_block = VGroup(verify_box, verify_txt)

        spec_blocks = VGroup(draft_blocks, verify_block).arrange(RIGHT, buff=0.12)
        spec_blocks.next_to(row2_lbl, DOWN, buff=0.2).align_to(LEFT * 5.8, LEFT)
        row2_lbl.align_to(spec_blocks, LEFT)

        spec_brace = Brace(spec_blocks, DOWN, color=SUCCESS)
        spec_time = text(
            "Total Latency: ~1.4 × T_target", font_size=16, color=SUCCESS, weight="BOLD"
        ).next_to(spec_brace, DOWN, buff=0.08)
        self.play(
            FadeIn(row2_lbl), FadeIn(spec_blocks), Create(spec_brace), FadeIn(spec_time)
        )

        callout_box = panel(
            width=3.2, height=2.5, fill_color=SURFACE, stroke_color=ACCENT
        ).move_to(RIGHT * 4.6 + DOWN * 0.2)
        metric_num = text("2.8×", font_size=46, color=ACCENT, weight="BOLD")
        metric_lbl = text("Latency Speedup", font_size=18, color=TEXT, weight="BOLD")
        metric_sub = text(
            "Same Token Output\nIdentical Perplexity\nZero Fine-Tuning",
            font_size=14,
            color=MUTED,
        )
        metric_group = (
            VGroup(metric_num, metric_lbl, metric_sub)
            .arrange(DOWN, buff=0.15)
            .move_to(callout_box)
        )

        self.play(FadeIn(callout_box), FadeIn(metric_group))
        self.play(Circumscribe(metric_num, color=ACCENT, run_time=1.2))
        self.wait(2.5)
