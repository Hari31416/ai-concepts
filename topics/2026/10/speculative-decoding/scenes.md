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

- Duration: ~65 seconds
- Scene Class: SpeculativeDecoding
- Output Asset: `video/SpeculativeDecoding.mp4`, `images/SpeculativeDecoding.png`
- Purpose: Seamlessly transitions through all four stages in a single unified presentation video for the topic.
