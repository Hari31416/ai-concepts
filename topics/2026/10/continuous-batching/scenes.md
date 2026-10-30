# Continuous Batching Animation Plan

This document details the visual storyboard, narrative arc, mathematical components, and technical implementation for animating Continuous Batching (iteration-level scheduling) with Manim Community Edition.

## Overview

- **Topic:** Continuous Batching (In-Flight Batching / Iteration-Level Scheduling) in LLM Inference
- **Hook:** Why does traditional batching waste over 40% of GPU compute on empty padding, and how does iteration-level scheduling reclaim that lost throughput?
- **Target Audience:** ML engineers, system designers, and students familiar with autoregressive decoding and GPU batching basics
- **Structure:** 4 modular scene classes for focused explanations, plus 1 consolidated master scene (`ContinuousBatching`) linking the full narrative arc
- **Asset Layout:** Videos saved in `video/`, still frames and diagrams saved in `images/`

---

## Narrative Arc

The animation opens with the limitation of static batching: autoregressive outputs have unpredictable lengths, forcing short requests to linger as idle "bubbles" while late arrivals queue outside. We then reveal the mechanism of iteration-level scheduling, where the serving engine re-evaluates the batch at every single token step, immediately evicting completed sequences and slotting in queued requests. Next, a direct timeline comparison demonstrates the stark difference in makespan and slot density. Finally, a clear performance dashboard summarizes the resulting surge in throughput and drop in latency.

---

## Scene 1: The Static Batching Bottleneck

- **Duration:** ~18 seconds
- **Scene Class:** `StaticBatchingWasteScene`
- **Output Asset:** `video/StaticBatchingWasteScene.mp4`, `images/StaticBatchingWasteScene.png`
- **Purpose:** Illustrate why request-level batching creates severe GPU underutilization ("bubble" waste) and head-of-line blocking.

### Visual Elements
- Title: "The Static Batching Bottleneck"
- Batch container with 3 sequence slots running across decoding steps $t = 1 \dots 6$:
  - Request 1 ($R_1$, `ENTITY_A` #7DD3FC): finishes at $t = 2$ (`<eos>`)
  - Request 2 ($R_2$, `ENTITY_B` #C4B5FD): finishes at $t = 4$ (`<eos>`)
  - Request 3 ($R_3$, `ENTITY_C` #FDBA74): finishes at $t = 6$ (`<eos>`)
- Idle bubble zones: Dashed, dimmed `ERROR` red-tinted slots representing wasted GPU compute where dummy padding tokens are evaluated.
- Blocked queue panel on the right: Request 4 ($R_4$) waiting helplessly until the entire batch concludes.
- Stat callout badge: "33% Compute Wasted in Idle Bubbles".

### Narration / Logic Notes
- In static batching, all requests are locked until the slowest sequence finishes.
- Once $R_1$ emits `<eos>` at step 2, its slot cannot be reused.
- New requests cannot enter, causing long queue delays and wasted GPU cycles.

---

## Scene 2: The Continuous Batching Mechanism

- **Duration:** ~22 seconds
- **Scene Class:** `ContinuousBatchingMechanismScene`
- **Output Asset:** `video/ContinuousBatchingMechanismScene.mp4`, `images/ContinuousBatchingMechanismScene.png`
- **Purpose:** Demystify how iteration-level scheduling works by animating sequence eviction and immediate queue admission at the token boundary.

### Visual Elements
- Title: "Iteration-Level Scheduling: Step-by-Step"
- Active Batch Grid (3 slots) with dynamic token generation step counter:
  - Iteration $t = 2$: $R_1$ emits `<eos>` (highlighted in `SUCCESS` emerald green).
  - Iteration $t = 3$ Transition:
    - $R_1$ is smoothly faded and evicted to the completed zone.
    - $R_4$ slides out of the waiting queue directly into Slot 1.
    - The batch immediately resumes decoding without missing a single beat.
  - Iteration $t = 4$: $R_2$ emits `<eos>`, evicts, and $R_5$ enters Slot 2.
- Mechanism badge: "Dynamic Slot Recycling at Every Token Step".

### Narration / Logic Notes
- Scheduling happens at token granularity, not request granularity.
- The GPU batch remains 100% dense with valid tokens on every single forward pass.
- Eliminates padding bubbles completely during active load.

---

## Scene 3: Execution Timeline Comparison

- **Duration:** ~20 seconds
- **Scene Class:** `TimelineComparisonScene`
- **Output Asset:** `video/TimelineComparisonScene.mp4`, `images/TimelineComparisonScene.png`
- **Purpose:** Provide a side-by-side macro timeline of the exact same 5-request workload under both strategies.

### Visual Elements
- Title: "Execution Timelines: Static vs. Continuous"
- Top Track: **Static Batching**
  - Batch 1 ($R_1, R_2, R_3$) spanning $t = 1 \dots 6$, with shaded bubble areas.
  - Batch 2 ($R_4, R_5$) delayed until $t = 7 \dots 9$.
  - Total makespan: 9 iterations.
- Bottom Track: **Continuous Batching**
  - Fluid, tightly packed layout where $R_4$ starts at $t = 3$ and $R_5$ starts at $t = 5$.
  - Total makespan: 7 iterations.
- Visual delta arrow showing a 22% reduction in makespan and earlier completion times for every single query.

---

## Scene 4: Throughput & Latency Gains

- **Duration:** ~16 seconds
- **Scene Class:** `ThroughputLatencyGainsScene`
- **Output Asset:** `video/ThroughputLatencyGainsScene.mp4`, `images/ThroughputLatencyGainsScene.png`
- **Purpose:** Summarize the operational impact on GPU utilization, throughput, and queue latency.

### Visual Elements
- Title: "Serving Performance Impact"
- Three comparison cards:
  1. **GPU Slot Utilization:** 67% $\to$ 95%+ (Padded waste eliminated)
  2. **Queue Waiting Time:** 6 steps $\to$ 0 steps (No head-of-line blocking)
  3. **Effective Throughput:** Up to 2.5x higher tokens/sec
- Takeaway banner at bottom:
  "Continuous batching turns idle bubble cycles into useful token throughput."

---

## Scene 5: Consolidated Master Video

- **Duration:** ~75 seconds
- **Scene Class:** `ContinuousBatching`
- **Output Asset:** `video/ContinuousBatching.mp4`, `images/ContinuousBatching.png`
- **Purpose:** Unifies all four scenes into a single presentation video with smooth transitions.

---

## Color Palette & Theme Tokens

- Background: `#0B1020` (`BACKGROUND` from `shared.theme`)
- Surface Panel: `#151E32` (`SURFACE`)
- Borders: `#64748B` (`BORDER`)
- Primary Text: `#F1F5F9` (`TEXT`)
- Muted Labels: `#A8B3C7` (`MUTED`)
- Accent / Active: `#FBBF24` (`ACCENT`)
- Completed / Success: `#6EE7B7` (`SUCCESS`)
- Idle Bubble / Error: `#FDA4AF` (`ERROR`)
- Request 1: `#7DD3FC` (`ENTITY_A` Sky Blue)
- Request 2: `#C4B5FD` (`ENTITY_B` Purple)
- Request 3: `#FDBA74` (`ENTITY_C` Amber)
- Request 4: `#38BDF8` (Cyan)
- Request 5: `#A78BFA` (Indigo)
