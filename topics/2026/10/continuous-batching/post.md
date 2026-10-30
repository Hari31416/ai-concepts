# Continuous Batching

## Bullet Points

- Static (request-level) batching forces all requests in a batch to run until the slowest sequence finishes generating.
- Shorter requests that emit `<eos>` early must be padded with dummy tokens, creating idle GPU "bubbles" that waste 30% to 50%+ of compute cycles.
- While a static batch runs, new incoming requests cannot join and remain blocked in the queue, spiking Time to First Token (TTFT).
- Continuous batching (iteration-level scheduling) evaluates completions after every single token generation step.
- As soon as a request finishes at iteration $t$, it is evicted immediately and its KV-cache slot is freed.
- Queued requests are admitted at iteration $t+1$ directly into vacated slots.
- The GPU batch stays densely saturated with active tokens at every forward pass.
- In production inference engines (vLLM, TensorRT-LLM, TGI), continuous batching delivers a 2x to 4x throughput increase and slashes queue wait times.

## LinkedIn Post

Autoregressive LLM inference is limited by memory bandwidth during decoding. Loading weights from high-bandwidth memory to compute a single token underutilizes GPU tensor cores, which is why serving engines batch requests together.

Static batching groups requests at the request level. If Request 1 finishes in 20 tokens, Request 2 in 40, and Request 3 in 200, Requests 1 and 2 sit idle as dummy padding for hundreds of iterations while the GPU finishes Request 3. At the same time, new user queries sit blocked in the arrival queue.

Continuous batching solves this by moving scheduling from the request level to the iteration level:

- At each token step, the engine inspects generated tokens for `<eos>`.
- Finished sequences are evicted immediately, returning their response to the client and freeing memory.
- Waiting requests from the queue are admitted into the vacant slots on the very next token iteration.
- The GPU runs full batches of real work on every step, eliminating padding bubbles.

Modern inference engines like vLLM, TensorRT-LLM, and TGI rely on continuous batching to turn bursty, unpredictable sequence lengths into steady compute saturation, doubling or tripling production serving throughput.

## Twitter Post

Static batching locks LLM requests together until the slowest one finishes, wasting GPU cycles on empty padding bubbles.

Continuous batching schedules at the token level: evict finished sequences immediately and admit waiting requests into vacant slots at the next step.

Zero idle bubbles, 2x to 4x throughput.
