# Speculative Decoding

## Bullet Points

- Generating text from large models one token at a time is limited by memory bandwidth, not compute.
- For a 70B model in FP16, each generated token requires loading roughly 140 GB of weights from GPU memory.
- At typical memory bandwidths like 3.35 TB/s, loading weights takes around 35 to 40 milliseconds per token while tensor cores stay idle.
- Verifying a batch of multiple tokens in parallel takes almost the same time as running a single token.
- Speculative decoding pairs a small draft model with a large target model.
- The small model quickly guesses a sequence of candidate tokens. The large model checks all candidates in a single parallel forward pass.
- Matches are accepted, and the first mismatch is corrected using the target model's output.
- The process is mathematically lossless. Greedy decoding reproduces the exact argmax output, and speculative sampling reproduces the target probability distribution.
- In production, this delivers a 2x to 3x wall-clock speedup without retraining or fine-tuning the target model.

## LinkedIn Post

Large language model inference is memory bandwidth bound.

When you run a 70B parameter model in FP16 with a batch size of 1, emitting a single token requires reading roughly 140 GB of weights from GPU memory into the compute cores. On an accelerator with 3.35 TB/s memory bandwidth, that transfer takes about 35 to 40 milliseconds. The tensor cores finish their math in a couple of milliseconds and spend the rest of the time waiting for weights.

Because the memory transfer dominates, evaluating four tokens in parallel takes nearly the same time as evaluating one token.

Speculative decoding takes advantage of this property:

- A small draft model, such as a 1B or 7B parameter model, generates a sequence of candidate tokens. Since the model is small, it runs quickly.
- The large target model processes all candidate prefixes together in a single forward pass.
- The candidate tokens are checked from left to right. Matching tokens are kept. The first mismatched token is corrected by the target model, and any remaining draft tokens are dropped.

If the draft model guesses four tokens and three match, the target model accepts those three and provides the fourth. You get four verified tokens for the latency cost of one forward pass.

This technique is mathematically lossless. With greedy decoding, the output matches standard generation from the target model token for token. In practice, with acceptance rates between 70% and 85%, speculative decoding provides a 2x to 3x wall-clock speedup without modifying the weights or fine-tuning the base model.

## Twitter Post

LLM decoding is memory bandwidth bound. For a 70B model, generating 1 token loads 140 GB of weights.

Speculative decoding uses a fast 1B model to guess tokens, and the 70B model verifies them in one parallel pass.

You get a 2x to 3x speedup with zero quality loss.
