# PagedAttention

## Background & Motivation

In autoregressive Large Language Model (LLM) serving, generation latency is dominated by memory bandwidth, while system throughput is bounded by GPU memory capacity.

For every generated token, the model needs the key and value vectors of all prior tokens in the sequence. To avoid recomputing these vectors at each step, engines cache them in GPU high-bandwidth memory (HBM). This structure is the Key-Value (KV) cache.

As sequence lengths and concurrent request counts grow, the KV cache quickly consumes most available GPU memory, often 60% to 80% of total VRAM, dwarfing the model weights themselves.

---

## 1. The Contiguous Allocation Problem

Traditional serving systems allocate KV cache memory contiguously in physical GPU memory. Because standard deep learning operations expect contiguous virtual memory tensors, each request pre-allocates a fixed buffer sized for the maximum possible sequence length (for example, 2048 or 4096 tokens).

This design introduces three distinct sources of memory waste:

1. **Reserved Slots (Over-allocation):** A request may generate only 50 tokens, but memory was reserved for 2048 tokens. The remaining slots sit empty for the entire duration of the request.
2. **Internal Fragmentation:** Memory is allocated in large chunks ahead of time based on loose upper bounds. Even if requests specify a maximum token budget, actual stop tokens (`<eos>`) trigger early, leaving the remainder wasted.
3. **External Fragmentation:** Over time, requests of varying lengths start and finish, leaving scattered, non-contiguous holes in physical GPU memory. Even if total free memory is large, the allocator cannot fit a new long request requiring contiguous space.

In practice, only 20% to 40% of allocated KV cache memory holds valid token states in contiguous allocation systems.

---

## 2. The PagedAttention Core Concept

Inspired by virtual memory paging in operating systems, PagedAttention (Kwon et al., SOSP 2023) eliminates the contiguous memory requirement.

Instead of storing a sequence's KV cache in a single contiguous tensor, PagedAttention divides the KV cache of each sequence into fixed-size **KV blocks**.

### Key Components

- **Logical Blocks:** The sequence views its KV cache as a continuous sequence of logical blocks ($L_0, L_1, L_2, \dots$), each containing $B$ tokens (typically $B = 16$ or $B = 32$).
- **Physical Blocks:** GPU memory is pre-divided into a global pool of fixed-size physical blocks ($P_0, P_1, P_2, \dots$).
- **Block Table:** A lookup table maintained by the serving engine. For each running request, the table records the mapping from logical block index to physical block index, along with how many token slots in the latest block are filled.

```
Logical Blocks (Request 1):
  [ Block 0: tokens 0-3 ] -> Block Table -> Physical Block 7
  [ Block 1: tokens 4-7 ] -> Block Table -> Physical Block 2
  [ Block 2: tokens 8-9 ] -> Block Table -> Physical Block 11
```

Physical blocks do not need to be contiguous in GPU memory. They are allocated dynamically from the free pool as the sequence generates tokens.

---

## 3. Attention Computation with Paged Blocks

During decoding for token $t$, the query vector $q_t$ computes attention against all previous keys $K$, followed by weighted aggregation over values $V$.

In standard attention:
$$A = \text{Softmax}\left(\frac{q_t K^T}{\sqrt{d}}\right) V$$

In PagedAttention, the kernel reads keys and values block by block:
1. The kernel receives the query $q_t$ and the request's block table.
2. Warp threads load key vectors directly from scattered physical blocks ($P_7, P_2, P_{11}$) into on-chip registers.
3. Partial attention dot products are accumulated across blocks.
4. Softmax reduction and value accumulation proceed without ever materializing a contiguous $K$ or $V$ tensor in HBM.

---

## 4. Memory Efficiency & Fragmentation Elimination

PagedAttention removes almost all memory waste:

- **External Fragmentation: 0%.** All physical blocks have identical fixed size $B$. Any free block can satisfy any request.
- **Internal Fragmentation: $< 4\%$.** Only the very last block of an active sequence can have unused slots. With block size $B = 16$, the expected wasted slots per sequence is $B / 2 = 8$ tokens. For a sequence of 200 tokens, this is $8 / 200 = 4\%$.
- **Zero Pre-reservation:** Blocks are allocated strictly on demand as new tokens are emitted.

---

## 5. Copy-on-Write and Prefix Sharing

PagedAttention enables memory sharing across requests:

- When generating multiple outputs from the same prompt (parallel sampling, beam search), the prompt's physical blocks are shared across all child requests via their block tables.
- The block manager tracks a reference count for each physical block.
- When child requests generate diverging tokens, if a block is shared and a new token is appended, the manager allocates a new block and copies the contents (Copy-on-Write).
