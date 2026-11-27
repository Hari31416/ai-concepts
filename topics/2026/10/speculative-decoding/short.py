"""Speculative Decoding as a vertical YouTube Short (9:16, ~48 s, captions + SFX).

Run from the repository root:

    make preview FILE=topics/2026/10/speculative-decoding/short.py \
        SCENE=SpeculativeDecodingShort FORMAT=shorts

Story: 140 GB weight load for 1 token -> draft model guesses 4 tokens ->
target model verifies all 4 in 1 parallel pass -> 2x-3x faster, lossless.
The 70B (~140 GB FP16) example is illustrative; the 70-85% acceptance rate
and 2x-3x speedup come from Leviathan et al. (2023) and Chen et al. (2023).
"""

from manim import (
    BOLD,
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Cross,
    DashedVMobject,
    FadeIn,
    FadeOut,
    Indicate,
    LaggedStart,
    Line,
    Rectangle,
    ReplacementTransform,
    RoundedRectangle,
    Scene,
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
    ERROR,
    MUTED,
    SHORTS_CAPTION_SIZE,
    SHORTS_CAPTION_Y,
    SHORTS_LABEL_SIZE,
    SHORTS_TITLE_SIZE,
    SUCCESS,
    SURFACE,
    TEXT,
    apply_theme,
    panel,
    text,
)

X0 = 0.0
TITLE_Y = 6.9


def caption_track(scene: Scene) -> CaptionTrack:
    return CaptionTrack(
        scene,
        position=(X0, SHORTS_CAPTION_Y),
        font_size=SHORTS_CAPTION_SIZE,
        max_chars=30,
    )


def make_token_box(
    word: str,
    *,
    color: str = TEXT,
    border_color: str = BORDER,
    is_draft: bool = False,
    width: float = 1.12,
    height: float = 0.56,
    font_size: float = 22,
) -> VGroup:
    """Create a token badge, dashed when it is an unverified draft guess."""
    if is_draft:
        base = RoundedRectangle(
            corner_radius=0.1,
            width=width,
            height=height,
            color=border_color,
            stroke_width=2.0,
        )
        dashed = DashedVMobject(base, num_dashes=12)
        bg = RoundedRectangle(
            corner_radius=0.1,
            width=width,
            height=height,
            fill_color=border_color,
            fill_opacity=0.12,
            stroke_opacity=0,
        )
        border = VGroup(bg, dashed)
    else:
        border = RoundedRectangle(
            corner_radius=0.1,
            width=width,
            height=height,
            color=border_color,
            stroke_width=2.0,
            fill_color=border_color,
            fill_opacity=0.20,
        )
    lbl = text(word, font_size=font_size, color=color, weight=BOLD)
    lbl.move_to(border.get_center())
    return VGroup(border, lbl)


# -----------------------------------------------------------------------------
# Part 1: the memory-bandwidth bottleneck
# -----------------------------------------------------------------------------


def problem(scene: Scene, caps: CaptionTrack) -> VGroup:
    head = text("Why are LLMs slow?", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    head.move_to([X0, TITLE_Y, 0])
    scene.play(FadeIn(head))

    # HBM weights panel (top) -> memory bus -> Tensor Cores panel (middle)
    hbm_box = panel(width=6.2, height=1.7, fill_color=SURFACE, stroke_color=ENTITY_A)
    hbm_box.move_to([X0, 5.1, 0])
    hbm_title = text(
        "GPU Memory (HBM)", font_size=SHORTS_LABEL_SIZE, color=TEXT, weight="BOLD"
    )
    hbm_sub = text("70B Weights • ~140 GB (FP16)", font_size=24, color=MUTED)
    hbm_txt = VGroup(hbm_title, hbm_sub).arrange(DOWN, buff=0.12).move_to(hbm_box)
    hbm_grp = VGroup(hbm_box, hbm_txt)

    bus_l = Line([X0 - 0.5, 4.25, 0], [X0 - 0.5, 3.05, 0], color=BORDER, stroke_width=2)
    bus_r = Line([X0 + 0.5, 4.25, 0], [X0 + 0.5, 3.05, 0], color=BORDER, stroke_width=2)
    bus_lbl = text("Memory Bus", font_size=22, color=MUTED).next_to(
        bus_r, RIGHT, buff=0.2
    )
    bus_grp = VGroup(bus_l, bus_r, bus_lbl)

    core_box = panel(width=6.2, height=2.1, fill_color=SURFACE, stroke_color=BORDER)
    core_box.move_to([X0, 2.0, 0])
    core_title = text(
        "Tensor Cores", font_size=SHORTS_LABEL_SIZE, color=TEXT, weight="BOLD"
    )
    core_title.next_to(core_box.get_top(), DOWN, buff=0.18)
    cores = VGroup(
        *(
            Rectangle(
                width=0.58,
                height=0.38,
                fill_color=SURFACE,
                fill_opacity=0.85,
                stroke_color=BORDER,
                stroke_width=1.5,
            )
            for _ in range(12)
        )
    ).arrange_in_grid(rows=2, cols=6, buff=0.12)
    cores.next_to(core_title, DOWN, buff=0.18)
    core_grp = VGroup(core_box, core_title, cores)

    caps.show("Why load 140 GB of weights just for one token?")
    scene.play(FadeIn(hbm_grp), FadeIn(bus_grp), FadeIn(core_grp), run_time=0.6)

    packet = RoundedRectangle(
        width=2.3,
        height=0.52,
        corner_radius=0.1,
        fill_color=ACCENT,
        fill_opacity=0.35,
        stroke_color=ACCENT,
        stroke_width=2,
    ).move_to([X0, 4.0, 0])
    packet_lbl = text("140 GB", font_size=24, color=ACCENT, weight="BOLD").move_to(
        packet
    )
    packet_grp = VGroup(packet, packet_lbl)
    play_sfx(scene, "thump")  # the big model's weights
    scene.play(FadeIn(packet_grp, run_time=0.2))
    play_sfx(scene, "stream")  # 140 GB crossing the memory bus
    scene.play(packet_grp.animate.move_to([X0, 3.2, 0]), run_time=0.7)

    out_tok = make_token_box(
        "Token 1",
        color=ENTITY_A,
        border_color=ENTITY_A,
        width=1.8,
        height=0.56,
        font_size=24,
    ).move_to([X0, 0.2, 0])
    play_sfx(scene, "tick")
    scene.play(FadeOut(packet_grp, run_time=0.2), FadeIn(out_tok, shift=DOWN * 0.15))
    caps.hold()

    caps.show("GPU cores sit mostly idle waiting on memory bandwidth.")
    for c in cores:
        c.set_stroke(ERROR).set_fill(ERROR, 0.15)
    idle_badge = VGroup(
        text("~90% idle", font_size=56, color=ERROR, weight="BOLD"),
        text("1 token per 140 GB read", font_size=26, color=MUTED),
    ).arrange(DOWN, buff=0.1)
    idle_badge.move_to([X0, -1.45, 0])
    play_sfx(scene, "deny")
    scene.play(FadeIn(idle_badge, shift=UP * 0.15), run_time=0.6)
    caps.hold()

    caps.show("Checking four tokens at once takes almost the same time.")
    four_toks = VGroup(
        *(
            make_token_box(
                f"T{i + 1}",
                color=SUCCESS,
                border_color=SUCCESS,
                width=1.15,
                height=0.56,
                font_size=24,
            )
            for i in range(4)
        )
    ).arrange(RIGHT, buff=0.16)
    four_toks.move_to([X0, 0.2, 0])
    same_badge = VGroup(
        text("4 tokens, 1 read", font_size=46, color=SUCCESS, weight="BOLD"),
        text("illustrative batch verification", font_size=24, color=MUTED),
    ).arrange(DOWN, buff=0.1)
    same_badge.move_to([X0, -1.45, 0])
    for c in cores:
        c.set_stroke(SUCCESS).set_fill(SUCCESS, 0.2)
    for i in range(4):  # four tokens verified in one read
        play_sfx(scene, f"ping_{i}", delay=0.1 * i)
    scene.play(
        ReplacementTransform(out_tok, four_toks),
        ReplacementTransform(idle_badge, same_badge),
        run_time=0.7,
    )
    caps.hold()
    return head


# -----------------------------------------------------------------------------
# Part 2: draft + parallel verification
# -----------------------------------------------------------------------------


def mechanism(scene: Scene, caps: CaptionTrack, head: VGroup) -> None:
    play_sfx(scene, "whoosh")
    new_head = text("Speculative Decoding", font_size=SHORTS_TITLE_SIZE, weight="BOLD")
    new_head.move_to([X0, TITLE_Y, 0])
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    scene.play(FadeOut(*others), Transform(head, new_head), run_time=0.7)

    # Draft phase
    caps.show("A tiny draft model quickly guesses the next four tokens.")
    draft_hdr = text(
        "Draft Model Mq (1B • fast)",
        font_size=SHORTS_LABEL_SIZE,
        color=ENTITY_B,
        weight="BOLD",
    ).move_to([X0, 5.7, 0])

    prompt_toks = VGroup(
        make_token_box("The", width=0.88, height=0.52, font_size=22),
        make_token_box("quick", width=0.96, height=0.52, font_size=22),
    ).arrange(RIGHT, buff=0.1)

    draft_words = ("brown", "fox", "jumps", "under")
    draft_toks = VGroup(
        *(
            make_token_box(
                w,
                color=ENTITY_B,
                border_color=ENTITY_B,
                is_draft=True,
                width=1.08,
                height=0.52,
                font_size=21,
            )
            for w in draft_words
        )
    ).arrange(RIGHT, buff=0.1)

    seq_row = (
        VGroup(prompt_toks, draft_toks).arrange(RIGHT, buff=0.1).move_to([X0, 4.7, 0])
    )
    scene.play(FadeIn(draft_hdr), FadeIn(prompt_toks), run_time=0.5)
    for i, tok in enumerate(draft_toks):  # light notes: the small model guessing
        play_sfx(scene, f"blip_{i}")
        scene.play(FadeIn(tok, shift=RIGHT * 0.12), run_time=0.25)
    caps.hold()

    # Parallel verification pass inside Target Model Mp
    caps.show("The large target model checks all four in one pass.")
    mp_panel = panel(width=7.0, height=4.7, fill_color=SURFACE, stroke_color=ENTITY_A)
    mp_panel.move_to([X0, 1.0, 0])
    mp_hdr = text(
        "Target Model Mp (70B, 1 pass)",
        font_size=26,
        color=ENTITY_A,
        weight="BOLD",
    ).next_to(mp_panel.get_top(), DOWN, buff=0.22)

    query_specs = [
        ("[The quick]", "brown", True),
        ("[... brown]", "fox", True),
        ("[... fox]", "jumps", True),
        ("[... jumps]", "over", False),
    ]
    rows = VGroup()
    for prefix, pred, _ in query_specs:
        q_box = make_token_box(
            prefix,
            color=MUTED,
            border_color=BORDER,
            width=2.2,
            height=0.54,
            font_size=21,
        )
        arr = Arrow(
            LEFT * 0.3,
            RIGHT * 0.3,
            color=ENTITY_A,
            buff=0.05,
            stroke_width=2.5,
            max_tip_length_to_length_ratio=0.35,
        )
        p_box = make_token_box(
            pred,
            color=TEXT,
            border_color=ENTITY_A,
            width=1.6,
            height=0.54,
            font_size=22,
        )
        rows.add(VGroup(q_box, arr, p_box).arrange(RIGHT, buff=0.2))
    rows.arrange(DOWN, buff=0.26).next_to(mp_hdr, DOWN, buff=0.35)

    play_sfx(scene, "riser")  # build-up, then the big model's weight lands
    play_sfx(scene, "thump", delay=0.85)
    scene.play(FadeIn(mp_panel), FadeIn(mp_hdr), run_time=0.5)
    scene.play(
        LaggedStart(*(FadeIn(r, shift=DOWN * 0.1) for r in rows), lag_ratio=0.08),
        run_time=0.8,
    )
    caps.hold()

    # Accept first 3 guesses
    caps.show("Three guesses match and are accepted right away.")
    checks = VGroup()
    for i in range(3):
        rows[i][2][0].set_stroke(SUCCESS).set_fill(SUCCESS, 0.22)
        draft_toks[i][0][0].set_fill(SUCCESS, 0.22)
        draft_toks[i][0][1].set_color(SUCCESS)
        draft_toks[i][1].set_color(SUCCESS)
        chk = text("✓", font_size=28, color=SUCCESS, weight="BOLD").next_to(
            rows[i], RIGHT, buff=0.18
        )
        checks.add(chk)
    for i in range(3):  # a rising bell per accepted guess
        play_sfx(scene, f"ping_{i}", delay=0.15 * i)
    scene.play(
        FadeIn(checks),
        *(Indicate(draft_toks[i], color=SUCCESS, scale_factor=1.08) for i in range(3)),
        run_time=0.8,
    )
    caps.hold()

    # Reject 4th guess ("under") and replace with target's ("over")
    caps.show("The fourth guess fails, so the target model fixes it.")
    bad_tok = draft_toks[3]
    cross = Cross(bad_tok, stroke_color=ERROR, stroke_width=4.0)
    play_sfx(scene, "deny")
    scene.play(FadeIn(cross), run_time=0.35)

    fixed_tok = make_token_box(
        "over",
        color=SUCCESS,
        border_color=SUCCESS,
        is_draft=False,
        width=1.08,
        height=0.52,
        font_size=21,
    ).move_to(bad_tok)
    rows[3][2][0].set_stroke(SUCCESS).set_fill(SUCCESS, 0.25)
    fix_mark = text("→ fix", font_size=22, color=ACCENT, weight="BOLD").next_to(
        rows[3], RIGHT, buff=0.14
    )
    play_sfx(scene, "ping_3")  # the corrected token resolves the phrase
    scene.play(
        FadeOut(cross),
        ReplacementTransform(bad_tok, fixed_tok),
        FadeIn(fix_mark),
        run_time=0.65,
    )

    out_note = text(
        "Output: The quick brown fox jumps over",
        font_size=24,
        color=SUCCESS,
        weight="BOLD",
    ).move_to([X0, -2.0, 0])
    scene.play(FadeIn(out_note, shift=UP * 0.1), run_time=0.45)
    caps.hold(extra=0.6)


# -----------------------------------------------------------------------------
# Part 3: the payoff
# -----------------------------------------------------------------------------


def payoff(scene: Scene, caps: CaptionTrack, head: VGroup) -> None:
    caps.show("One pass yields four exact tokens with zero quality loss.")
    others = [m for m in scene.mobjects if m is not head and m is not caps.current]
    play_sfx(scene, "whoosh")
    scene.play(FadeOut(*others), run_time=0.7)

    speed_card = VGroup(
        text("2x – 3x", font_size=88, color=SUCCESS, weight="BOLD"),
        text("faster decoding (70-85% acceptance)", font_size=26, color=MUTED),
    ).arrange(DOWN, buff=0.18)
    speed_card.move_to([X0, 4.2, 0])

    loss_card = VGroup(
        text("0%", font_size=82, color=ENTITY_A, weight="BOLD"),
        text("quality loss (exact target match)", font_size=26, color=MUTED),
    ).arrange(DOWN, buff=0.18)
    loss_card.move_to([X0, 1.1, 0])

    play_sfx(scene, "ping_1")
    scene.play(FadeIn(speed_card, shift=UP * 0.2), run_time=0.6)
    scene.wait(0.4)
    play_sfx(scene, "chime")
    scene.play(FadeIn(loss_card, shift=UP * 0.2), run_time=0.6)
    caps.hold()

    caps.show("Same model outputs, up to three times faster.")
    caps.hold(extra=0.8)


class SpeculativeDecodingShort(Scene):
    """Vertical Short, about 48 s. Render with FORMAT=shorts."""

    def construct(self) -> None:
        apply_theme(self)
        caps = caption_track(self)
        head = problem(self, caps)
        mechanism(self, caps, head)
        payoff(self, caps, head)
        caps.finish()
