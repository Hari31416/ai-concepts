# Speculative Decoding Animation Plan

This document details the visual storyboard, narrative arc, mathematical components, and technical implementation for animating speculative decoding with Manim Community Edition.

## Overview

- Topic: Speculative Decoding for Large Language Models
- Hook: Why do large models spend most of their time waiting for memory, and how can a tiny model scout ahead so the giant model generates multiple tokens in a single step?
- Target Audience: Machine learning engineers, researchers, and students familiar with autoregressive generation and basic probability
- Structure: 4 modular scene classes for focused explanations, plus 1 consolidated master scene (`SpeculativeDecoding`) linking the full narrative arc
- Asset Layout: Videos saved in `video/`, still frames and diagrams saved in `images/`

## Narrative Arc

The animation begins with the hardware reality of autoregressive decoding: loading tens of gigabytes of weights for just one token is memory-bandwidth bound. We then introduce the two-actor collaboration: a tiny draft model rapidly proposes tokens, and the giant target model verifies all of them concurrently in a single forward pass. Next, we illustrate the mathematical guarantee: draft errors are repaired by the target model, preserving the exact target output distribution. Finally, a timeline comparison makes the concrete wall-clock speedup unmistakable.

## Scene 1: The Memory Bottleneck

- Duration: ~15 seconds
- Scene Class: MemoryBottleneckScene
- Output Asset: `video/MemoryBottleneckScene.mp4`, `images/MemoryBottleneckScene.png`
- Purpose: Illustrate why autoregressive decoding is slow and why parallel verification costs almost the same as single-token generation.

### Visual Elements

- Title: "The Memory Bandwidth Bottleneck"
- Hardware representation: GPU chip with HBM (High Bandwidth Memory) on the left and Tensor Cores on the right
- Animated memory bus transfer: Large weight packet ("Load 140 GB") traveling across the bus
- Token output badge: "Token 1 Emitted"
- Takeaway banner: "Key Insight: Verifying K tokens in parallel takes nearly the SAME time!"

## Scene 2: The Speculative Loop and Parallel Verification

- Duration: ~25 seconds
- Scene Class: SpeculativeLoopScene
- Output Asset: `video/SpeculativeLoopScene.mp4`, `images/SpeculativeLoopScene.png`
- Purpose: Demystify how the parallel verification pass works by explicitly showing the batch of prefix queries evaluated simultaneously.

### Visual Elements

- Title: "The Speculative Loop: How Parallel Verification Works"
- Two model cards:
  - Draft Model $M_q$ (lightweight, color `ENTITY_B` #C4B5FD, ~2 ms/token)
  - Target Model $M_p$ (high-capacity, color `ENTITY_A` #7DD3FC, ~25 ms/pass)
- Phase 1 (Drafting): $M_q$ sequentially emits candidate tokens `["brown", "fox", "jumps", "under"]` following prompt `"The quick"`.
- Phase 2 (Parallel Batch Construction): Displays the 4 prefix queries stacked into a single batch of size 4:
  - Query 1: `[The, quick]` $\to$ `"brown"` (94%)
  - Query 2: `[The, quick, brown]` $\to$ `"fox"` (91%)
  - Query 3: `[The, quick, brown, fox]` $\to$ `"jumps"` (86%)
  - Query 4: `[The, quick, brown, fox, jumps]` $\to$ `"over"` (82%)
  - Container callout: 70B parameters loaded once to evaluate all 4 queries in parallel.
- Phase 3 (Verification & Correction):
  - Tokens `"brown"`, `"fox"`, `"jumps"` accepted (`SUCCESS` checkmarks).
  - First mismatch `"under"` rejected (`ERROR` cross) and replaced with `"over"` from the target model's prediction.
- Summary banner: "Outcome: 4 verified tokens emitted from 1 target step!"

## Scene 3: Exact Distribution Preservation

- Duration: ~18 seconds
- Scene Class: RejectionSamplingScene
- Output Asset: `video/RejectionSamplingScene.mp4`, `images/RejectionSamplingScene.png`
- Purpose: Demystify why speculative decoding is mathematically lossless.

### Visual Elements

- Title: "Zero Quality Loss: Exact Target Distribution"
- Probability bar chart comparing target $p(x)$ and draft $q(x)$ across a 4-token vocabulary {A, B, C, D}
- Green bars: Accepted overlap $\min(p(x), q(x))$
- Blue bars: Resampled residual deficit $\max(0, p(x) - q(x))$
- Red bars: Rejected draft surplus $\max(0, q(x) - p(x))$
- Guarantee banner: "Lossless Guarantee: Output distribution matches the target model exactly."

## Scene 4: Wall-Clock Speedup

- Duration: ~15 seconds
- Scene Class: SpeedupComparisonScene
- Output Asset: `video/SpeedupComparisonScene.mp4`, `images/SpeedupComparisonScene.png`
- Purpose: Show wall-clock execution timeline comparison between standard autoregressive decoding and speculative decoding.

### Visual Elements

- Title: "Wall-Clock Speedup: Standard vs Speculative"
- Standard timeline: 4 sequential target forward passes ($4.0 \times T_{\text{target}}$)
- Speculative timeline: 3 tiny draft passes + 1 parallel verification pass ($\sim 1.4 \times T_{\text{target}}$)
- Speedup metric callout: 2.8x speedup card with circular accent pulse

## Scene 5: Consolidated Master Video

- Duration: ~77 seconds (paced by caption reading time)
- Scene Class: SpeculativeDecoding
- Output Asset: `video/SpeculativeDecoding.mp4`, `images/SpeculativeDecoding.png`
- Purpose: Seamlessly transitions through all four stages in a single unified presentation video for the topic.

### Caption beats (16:9, burned in, `video/SpeculativeDecoding.srt`)

Voiceless: the captions are the narration. Each beat is shown first, then the matching
animation plays, then the scene holds until the caption has been readable long enough.
Only the consolidated scene is captioned; the four individual scenes are not yet.
Takeaway banners sit above the caption area (bottom edge at y = -2.25).

| Act | Caption | Accompanies |
| --- | ------- | ----------- |
| 1 | Why is a giant model slow? It waits on memory, not math. | Title writes in |
| 1 | A 70B model's weights sit far from the compute. | HBM, tensor cores and bus appear |
| 1 | To produce one token, all 140 GB must cross the bus. | Weight packet crosses, token emitted |
| 1 | Cores sit idle, so checking K tokens at once is cheap. | Insight banner |
| 2 | Trick: a tiny model guesses, the big one checks. | Title writes in |
| 2 | The draft model cheaply guesses four tokens in a row. | Phase 1: draft tokens appear |
| 2 | The big model then scores every prefix in one pass. | Phase 2: four prefix queries in one batch |
| 2 | Each guess is compared with the big model's own pick. | Phase 3: draft row and target outputs |
| 2 | Matches are kept; the first mismatch is rejected. | Checkmarks and the cross on "under" |
| 2 | The big model's own token fills the gap: nothing lost. | "under" replaced by "over" |
| 2 | Result: four tokens from one big-model pass. | Outcome banner |
| 3 | Does guessing change the answer? Not even slightly. | Title and formula |
| 3 | Green marks where draft and target agree on the odds. | Bars and legend |
| 3 | Resampling the shortfall tops each bar up to exactly p. | Brace on p(A) = 0.60 |
| 3 | So outputs follow the big model's distribution exactly. | Lossless guarantee banner |
| 4 | So how much faster is it on the clock? | Title writes in |
| 4 | Standard decoding pays one big-model pass per token. | Four sequential passes |
| 4 | Speculation: three cheap drafts plus one verify pass. | Three drafts and one verify block |
| 4 | About 1.4 passes instead of 4: roughly 2.8x faster. | Speedup callout (illustrative timings) |
