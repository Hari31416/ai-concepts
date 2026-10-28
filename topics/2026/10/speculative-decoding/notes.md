# Speculative Decoding

Speculative decoding accelerates large language model generation by producing multiple tokens per target forward pass without degrading output quality.

## The Problem: The Memory Wall

Generating text token-by-token with large language models is memory-bandwidth bound rather than compute bound.

When generating with a batch size of 1, emitting a single token from a 70B parameter model in 16-bit precision requires reading roughly 140 GB of model weights from high-bandwidth memory (HBM) into processor caches and registers. High-end accelerators transfer data at a few terabytes per second, so reading 140 GB takes 30 to 40 milliseconds. During this time, thousands of GPU compute cores sit mostly idle, waiting for weight transfers.

Processing a batch of several candidate tokens simultaneously takes virtually the same time as processing a single token:

$$T_{\text{target}}(K \text{ tokens in parallel}) \approx T_{\text{target}}(1 \text{ token})$$

Autoregressive decoding generates tokens sequentially, incurring the full memory read cost for every token. If candidate tokens can be guessed in advance, the target model can verify all of them concurrently in a single forward pass.

## Core Mechanism

Speculative decoding pairs two models:

- **Target Model ($M_p$):** The primary, high-capacity model (e.g. 70B parameters) whose output quality is desired.
- **Draft Model ($M_q$):** A much smaller, faster model from the same family (e.g. 1B to 7B parameters) or an auxiliary prediction head.

Generation proceeds in alternating cycles:

1. **Draft Phase:** The draft model rapidly generates a short speculative burst of $K$ candidate tokens sequentially. Because the draft model is small, reading its weights takes a fraction of the time.
2. **Verification Phase:** The target model receives the original prompt plus all $K$ candidate tokens simultaneously in one parallel forward pass. Self-attention allows the target model to evaluate candidate positions concurrently.
3. **Sequential Verification:** The candidate tokens are checked from left to right against the target model's probabilities:
   - Tokens that match the target model's criteria are accepted.
   - Upon the first rejected token, that token is replaced with a correction emitted by the target model, and any subsequent draft tokens are discarded.
   - If all $K$ tokens are accepted, the target model's forward pass emits an additional bonus token at position $K+1$.

## Why It Is Lossless

Speculative decoding does not approximate or degrade the target model.

- **Greedy Decoding:** When generating with temperature 0, a candidate token is accepted if and only if it matches the target model's argmax token. If a candidate differs, the target model replaces it with its own top choice. The resulting text is identical to standard greedy generation from the target model.
- **Sampling:** When sampling with temperature, a modified rejection sampling rule ensures that accepted tokens combined with resampled rejected tokens reproduce the exact probability distribution of the target model.

## Wall-Clock Speedup

Because each draft step is fast and the target verification step evaluates all candidates in parallel, every verification cycle yields between 1 and $K+1$ valid tokens in roughly the time of one target forward pass.

With an acceptance rate $\alpha$ between 70% and 85%, speculative decoding routinely achieves $2\times$ to $3\times$ latency speedups in practice.

## Primary References

- Leviathan, Y., Kalman, M., & Matias, Y. (2023). Fast Inference from Transformers via Speculative Decoding. ICML 2023. https://arxiv.org/abs/2211.17192
- Chen, C., Borgeaud, S., Irving, G., Lespiau, J. B., Sifre, L., & Jumper, J. (2023). Accelerating Large Language Model Decoding with Speculative Sampling. arXiv:2302.01318. https://arxiv.org/abs/2302.01318
