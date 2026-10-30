# Continuous Batching (Iteration-Level Scheduling)

## Background & Motivation

In autoregressive Large Language Model (LLM) inference, text generation proceeds one token at a time. Each generated token requires reading all model weights from high-bandwidth GPU memory (HBM) into on-chip cache (SRAM/registers) to compute a single forward pass. Because memory bandwidth limits single-request decoding, batching multiple requests together amortizes weight transfer across parallel sequences, dramatically improving GPU compute efficiency.

However, naive batching at the request level introduces severe inefficiencies due to the dynamic nature of generation.

---

## 1. The Flaw of Static (Request-Level) Batching

In static batching, the serving engine groups $B$ requests into a batch and runs iterations until **all** sequences in the batch finish generating (either reaching `<eos>` or maximum sequence length).

### The Inherent Inefficiencies

1. **The "Bubble" Problem (Compute Underutilization):**
   - Natural language queries have unpredictable output lengths.
   - If Request 1 finishes in 20 tokens, Request 2 in 40 tokens, and Request 3 in 200 tokens, Requests 1 and 2 must continue to occupy batch slots until Request 3 finishes.
   - The engine pads the completed sequences with dummy tokens. The GPU continues to load weights and execute tensor cores for these empty slots, wasting 50% or more of compute cycles.

2. **Head-of-Line Blocking & Queue Latency:**
   - New incoming requests cannot enter the batch while it is executing.
   - They must wait in a queue until the entire current static batch completes.
   - This spikes Time to First Token (TTFT) and overall end-to-end latency.

---

## 2. The Solution: Iteration-Level (Continuous) Batching

First introduced by Orca (OSDI '22) and popularized by vLLM, TensorRT-LLM, and TGI, **continuous batching** (also called *in-flight batching* or *iteration-level scheduling*) redefines the scheduling granularity from the **request** level to the **iteration (token)** level.

### Key Operational Rules

1. **Immediate Eviction:** As soon as any sequence emits `<eos>` (or hits its limit) on iteration $t$, it is evicted from the running batch immediately. Its allocated memory and compute slot are freed.
2. **Immediate Admission:** At iteration $t+1$, the scheduler checks the waiting queue. If memory allows, waiting requests are immediately admitted into the newly vacated slots.
3. **Dynamic Batch Composition:** The batch composition changes dynamically at every single token step. The batch remains densely packed with valid active tokens.

---

## 3. Concrete Numerical Example

Consider 5 requests with varying generation lengths:
- $R_1$: 2 tokens
- $R_2$: 4 tokens
- $R_3$: 6 tokens
- $R_4$: 3 tokens
- $R_5$: 3 tokens

Suppose hardware batch size limit $B = 3$.

### Static Batching Execution
- **Batch 1 ($R_1, R_2, R_3$):**
  - Runs for 6 iterations (dictated by $R_3$).
  - $R_1$ finishes at $t=2$; slots for $t \in [3, 6]$ are idle padding (4 wasted slots).
  - $R_2$ finishes at $t=4$; slots for $t \in [5, 6]$ are idle padding (2 wasted slots).
  - Total tokens computed in Batch 1: 18 slots, of which 6 are wasted padding ($33.3\%$ waste).
  - $R_4$ and $R_5$ are blocked in the queue until $t=6$.
- **Batch 2 ($R_4, R_5$):**
  - Runs for 3 iterations ($t=7, 8, 9$).
  - One unused slot throughout ($t \in [7, 9]$, 3 wasted slots).
- **Total makespan:** 9 iterations. Total slot capacity = $9 \times 3 = 27$. Total real tokens = 18. Wasted = 9 slots ($33.3\%$).

### Continuous Batching Execution
- $t=1$: Batch = $[R_1, R_2, R_3]$.
- $t=2$: Batch = $[R_1, R_2, R_3]$. $R_1$ emits `<eos>` and completes.
- $t=3$: $R_1$ evicted, $R_4$ admitted! Batch = $[R_4, R_2, R_3]$.
- $t=4$: Batch = $[R_4, R_2, R_3]$. $R_2$ emits `<eos>` and completes.
- $t=5$: $R_2$ evicted, $R_5$ admitted! Batch = $[R_4, R_5, R_3]$. $R_4$ emits `<eos>` and completes.
- $t=6$: $R_4$ evicted. Batch = $[R_5, R_3]$. $R_3$ emits `<eos>` and completes.
- $t=7$: $R_3$ evicted. Batch = $[R_5]$. $R_5$ emits `<eos>` and completes!
- **Total makespan:** 7 iterations (vs. 9 iterations). Zero padding bubbles during heavy load. $R_4$ finishes at $t=5$ instead of $t=9$!

---

## 4. Key Performance Gains

| Metric                          | Static Batching                      | Continuous Batching                  |
| :------------------------------ | :----------------------------------- | :----------------------------------- |
| **Scheduling Granularity**      | Request-level                        | Iteration (Token)-level              |
| **Token Padding Waste**         | Severe (30% - 60% idle bubbles)      | Zero during decoding                 |
| **Queue Waiting Time**          | High (must wait for slowest request) | Minimal (immediate slot backfilling) |
| **Throughput (Tokens/s)**       | Baseline                             | 2x - 4x improvement                  |
| **GPU Tensor Core Utilization** | Sporadic & decaying per batch        | Sustained high density               |

---

## References

1. Yu, G., et al. (2022). *Orca: A Distributed Serving System for Transformer-Based Generative Models*. OSDI '22.
2. Kwon, W., et al. (2023). *Efficient Memory Management for Large Language Model Serving with PagedAttention*. SOSP '23.
