# PagedAttention Animation Plan

This document details the storyboard, visual structure, mathematical framing, and technical implementation for animating PagedAttention with Manim Community Edition.

## Overview

- **Topic:** PagedAttention: Eliminating Memory Waste in LLM Inference KV Cache
- **Hook:** Why do large language models waste over 60% of GPU memory on unused slots, and how does operating system-style paging bring cache waste below 4%?
- **Target Audience:** Systems engineers, ML researchers, and students familiar with transformer attention and autoregressive generation.
- **Structure:** 4 modular scenes plus 1 consolidated master scene (`PagedAttention`) in `animation.py`.
- **Assets:** Videos saved in `video/`, still frames and review extracts saved in `images/`.

---

## Narrative Arc

The animation opens with the memory crisis in standard KV caching: contiguous virtual memory forces engines to pre-allocate memory for the maximum possible sequence length, wasting 60% to 80% of GPU VRAM in idle reservations and fragmentation. Next, we reveal the core mechanism of PagedAttention: slicing the sequence's cache into small fixed-size logical blocks and routing them through a dynamic Block Table to scattered physical GPU blocks. We then animate token generation in real time, demonstrating on-demand block allocation. Finally, we showcase memory sharing and Copy-on-Write for parallel sampling.

---

## Scene 1: The Contiguous KV Cache Crisis

- **Duration:** ~16 seconds
- **Scene Class:** `ContiguousFragmentationScene`
- **Output Asset:** `video/ContiguousFragmentationScene.mp4`, `images/ContiguousFragmentationScene.png`
- **Purpose:** Visualize how traditional contiguous allocation wastes memory through static reservations, internal fragmentation, and external fragmentation.

### Visual Elements
- Title: "The Contiguous KV Cache Crisis"
- GPU Memory Bar: Divided into contiguous slots for 3 requests:
  - Request 1 (`ENTITY_A` #7DD3FC): 4 tokens used out of 16 reserved.
  - Request 2 (`ENTITY_B` #C4B5FD): 6 tokens used out of 16 reserved.
  - Request 3 (`ENTITY_C` #FDBA74): 10 tokens used out of 16 reserved.
- Wasted space callout: Red-tinted shaded boxes indicating empty reserved slots.
- External fragmentation: Request 4 arrives needing 12 contiguous slots; none of the small free fragments are large enough, causing an out-of-memory error despite having 20+ free slots total.
- Metric badge: "60% - 80% GPU Memory Wasted".

---

## Scene 2: The PagedAttention Architecture

- **Duration:** ~18 seconds
- **Scene Class:** `PagedAttentionArchitectureScene`
- **Output Asset:** `video/PagedAttentionArchitectureScene.mp4`, `images/PagedAttentionArchitectureScene.png`
- **Purpose:** Introduce the virtual memory abstraction: Logical Blocks, the Block Table, and Physical Blocks.

### Visual Elements
- Title: "Virtual Memory for KV Cache"
- Left Panel: **Logical Blocks** (Sequence view)
  - Block 0: tokens $t_0 \dots t_3$
  - Block 1: tokens $t_4 \dots t_7$
  - Block 2: tokens $t_8 \dots t_9$ (partially filled)
- Center Panel: **Block Table**
  - Logical 0 $\to$ Physical 7
  - Logical 1 $\to$ Physical 2
  - Logical 2 $\to$ Physical 11
- Right Panel: **Physical GPU Memory Pool**
  - Scattered 4-token blocks across physical memory ($P_0 \dots P_{15}$).
  - Curved animated routing arrows connecting logical blocks to physical blocks via table rows.
- Architectural takeaway: Physical blocks do not need to be contiguous in VRAM.

---

## Scene 3: On-Demand Dynamic Allocation

- **Duration:** ~18 seconds
- **Scene Class:** `DynamicAllocationScene`
- **Output Asset:** `video/DynamicAllocationScene.mp4`, `images/DynamicAllocationScene.png`
- **Purpose:** Walk through token-by-token generation and show how blocks are claimed only when needed.

### Visual Elements
- Title: "On-Demand Block Allocation"
- Current State: Block 2 has 3 filled slots ($t_8, t_9, t_{10}$) and 1 empty slot.
- Step 1: Token $t_{11}$ generated. Fills the 4th slot of Block 2. Block 2 is now completely full.
- Step 2: Token $t_{12}$ generated. Engine detects that the current block is full.
- Step 3: Engine queries the Free Block Pool ($P_5$ is free), claims $P_5$, writes $t_{12}$ into slot 0, and updates the Block Table with Logical 3 $\to$ Physical 5.
- Stat Callout: "Zero Pre-allocation. Internal Waste < 4%".

---

## Scene 4: System Impact & Key Takeaways

- **Duration:** ~14 seconds
- **Scene Class:** `PagedAttentionImpactScene`
- **Output Asset:** `video/PagedAttentionImpactScene.mp4`, `images/PagedAttentionImpactScene.png`
- **Purpose:** Provide a clear side-by-side comparison between contiguous allocation and PagedAttention, highlighting practical throughput gains and zero memory fragmentation.

### Visual Elements
- Title: "PagedAttention: System Impact"
- Left Panel (Contiguous Allocation):
  - Static reservation for maximum sequence length
  - 60% – 80% VRAM wasted by idle reserved slots
  - Severe external fragmentation allocation failures
  - Artificially throttled batch size
- Right Panel (PagedAttention):
  - Dynamic page allocation on demand
  - Internal fragmentation reduced to < 4% (active tail block only)
  - Zero external memory fragmentation
  - 2x – 4x higher serving throughput in production (vLLM)
- Bottom Banner: "Key Takeaway: Virtual memory paging unlocks true continuous batching at scale"

---

## Master Consolidated Scene: `PagedAttention`

- **Duration:** ~66 seconds
- Combines the 4 phases with clear title cards and smooth transitions.
- Fully runnable standalone.
