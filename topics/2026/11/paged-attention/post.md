# PagedAttention

## Bullet Points

- Autoregressive generation stores key and value vectors for all previous tokens in GPU memory. This KV cache grows dynamically with every generated token.
- Standard serving engines historically reserved contiguous GPU memory chunks upfront sized for the maximum possible sequence length (such as 2,048 or 4,096 tokens).
- Because actual output lengths vary widely, static pre-allocation wastes 60% to 80% of KV cache memory on idle reserved slots that requests never use.
- Over time, requests completing at different times fragment physical GPU memory. Even when plenty of total memory is free, new requests fail to allocate because no contiguous chunk is large enough.
- PagedAttention applies virtual memory paging to LLM inference.
- KV caches are partitioned into small, fixed-size blocks (typically 16 or 32 tokens per block).
- Physical blocks can reside anywhere in GPU memory and do not need to be contiguous.
- A block table maps logical token positions to physical blocks, resolving addresses on the fly during the attention forward pass.
- New blocks are allocated strictly on demand as sequences grow token by token.
- Internal fragmentation is confined strictly to the last unfilled block of a sequence, reducing total memory waste to under 4%.
- Eliminating memory waste allows batch sizes to scale 2x to 4x higher on the same hardware, drastically improving production serving throughput.

## LinkedIn Post

Large language model inference is bottlenecked by GPU memory.

During generation, models store key and value vectors for every context token in GPU RAM. For a 13B model with 4,096 context length, a single request can consume over 3 GB of KV cache memory alone.

Historically, serving systems allocated this memory the same way traditional programs did before virtual memory: in contiguous memory blocks. Because the engine cannot predict how long an answer will be, it reserves enough contiguous space for the maximum possible sequence length upfront.

That creates two major memory leaks:

1. Internal waste. A user prompt might only generate 50 tokens, but the engine reserved space for 2,048 tokens. The unused 97% sits idle and cannot be shared. Across a batch, 60% to 80% of KV memory is wasted on unallocated headroom.
2. External fragmentation. When requests finish and free their memory, they leave scattered holes in the address space. New incoming requests that need large contiguous blocks fail to allocate, even when the total free GPU memory is more than enough.

PagedAttention borrows the classic solution from 1960s operating systems: virtual memory paging.

Instead of contiguous arrays, the KV cache is divided into fixed-size physical blocks (usually 16 or 32 tokens). These blocks can sit anywhere in GPU VRAM, non-contiguously.

Each sequence maintains a block table that maps logical token positions to physical memory blocks. During multi-head attention, the CUDA kernel reads the block table and fetches keys and values across non-contiguous memory locations without overhead.

When a sequence generates a new token:
- If the current block has room, the token is written into the next slot.
- If the block is full, the engine grabs a single free page from a shared pool and updates the table.

Because memory is allocated only when a token is actually produced, waste drops to under 4% (limited only to the tail of the final block).

With zero external fragmentation and near-zero over-allocation, systems like vLLM can pack far more concurrent requests onto the same GPUs, achieving 2x to 4x higher serving throughput without modifying the underlying model weights.

## Twitter Post

Why did vLLM change LLM serving? PagedAttention.

Standard inference reserves contiguous memory for max sequence lengths upfront, wasting 60% to 80% of GPU RAM on unused headroom.

PagedAttention chops the KV cache into small pages (16 tokens) mapped via block tables. New pages allocate strictly on demand.

Result: waste drops below 4%, and throughput jumps 2x to 4x on identical GPUs.
