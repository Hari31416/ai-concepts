# Product Quantization

## Bullet Points

- A 128-dimensional `float32` embedding takes 512 bytes. A billion of them take 512 GB, which does not fit in one machine's RAM, and an exact search has to read all of it.
- Product quantization (PQ) compresses each vector to a few bytes, usually 8 to 64, and still gives approximate distances without decompressing.
- Split each vector into M pieces, for example 8 pieces of 16 dimensions.
- Run k-means separately in each piece's subspace to learn K centroids, usually 256.
- Replace each piece with the ID of its nearest centroid. The vector becomes M one-byte IDs, so 512 bytes shrink to 8, a 64x reduction.
- The codebooks multiply. You store 8 × 256 = 2,048 centroids (about 128 KiB) but can describe 256^8, roughly 1.8 × 10^19, different vectors. One k-means would need that many centroids.
- Search keeps the query exact. Compute its distance to every centroid once, which gives an M × K table. A stored vector's distance is then M table lookups added together.
- That is 8 lookups per vector instead of 128 multiplications.
- Vectors with the same code get the same score, so PQ is lossy. Real systems use it to shortlist, then rerank the top results with the original vectors.
- PQ makes each vector smaller but does not cut how many you compare. IVF or HNSW handle that part.

## LinkedIn Post

A billion embeddings is 512 GB of RAM. Product quantization gets it to 8 GB and you can still search it.

A 128-dimensional float32 vector is 512 bytes. At a billion vectors, memory is gone before you run a single query, and an exact search reads everything.

PQ works in two moves, split and snap.

Split each vector into pieces, say 8 pieces of 16 numbers. For each piece position, run k-means to learn 256 centroids. Then replace every piece with the ID of its nearest centroid.

A 512-byte vector is now 8 one-byte IDs. That is 64x smaller.

What surprised me is how little codebook this needs. You store 8 × 256 = 2,048 centroids, about 128 KiB. Because every piece picks independently, those centroids describe 256^8 vectors, roughly 1.8 × 10^19. A single k-means would need that many centroids to match it.

Search is just as cheap. The query stays exact. For each piece, compute its distance to all 256 centroids once and keep the results in a table. A stored vector's distance is 8 table lookups added together. No decompression, and no 128 multiplications per vector.

It is lossy. Vectors in the same cell share a code and score the same, so real systems shortlist with PQ and rerank the top hits with the original vectors.

PQ also only shrinks vectors. It does not reduce how many you compare. IVF and HNSW decide which vectors to look at, and PQ makes each one cheap to look at.

Reference: Jégou, Douze and Schmid, "Product Quantization for Nearest Neighbor Search", IEEE TPAMI 2011.

## Twitter Post

How does a vector DB fit a billion 128-dim embeddings (512 GB) into 8 GB?

Product quantization. Split each vector into 8 pieces, snap each piece to its nearest of 256 centroids, store only the IDs. 512 bytes becomes 8.

Search builds one lookup table per query, then adds 8 numbers per vector. It is approximate, so rerank the shortlist.
