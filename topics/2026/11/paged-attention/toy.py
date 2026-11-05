"""Minimal reference simulation of PagedAttention vs Contiguous KV Cache Allocation.

Demonstrates:
1. Contiguous allocation with max-sequence pre-reservation and fragmentation waste.
2. Paged allocation using fixed-size physical blocks and block tables.
3. On-demand block allocation during autoregressive decoding.
4. Copy-on-Write (CoW) memory sharing for parallel candidate branches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class AllocationStats:
    total_slots_reserved: int
    valid_tokens_stored: int
    wasted_slots: int
    waste_percentage: float
    active_requests: int
    max_concurrent_capacity: int


class ContiguousKVManager:
    """Simulates traditional contiguous KV cache allocation.

    Each request reserves a contiguous chunk of size max_seq_len upfront.
    """

    def __init__(self, total_gpu_slots: int, max_seq_len: int = 16) -> None:
        self.total_gpu_slots = total_gpu_slots
        self.max_seq_len = max_seq_len
        # Maps request_id to (start_slot, current_tokens, reserved_slots)
        self.allocations: Dict[str, tuple[int, int, int]] = {}
        # Bitmask or set of allocated physical slot indices
        self.occupied_slots: Set[int] = set()

    def allocate(self, request_id: str, initial_tokens: int) -> bool:
        """Attempt to find a contiguous slot range of size max_seq_len."""
        needed = self.max_seq_len
        # Find contiguous free range
        start = self._find_contiguous_free(needed)
        if start is None:
            return False
        for slot in range(start, start + needed):
            self.occupied_slots.add(slot)
        self.allocations[request_id] = (start, initial_tokens, needed)
        return True

    def append_token(self, request_id: str) -> bool:
        """Append one generated token to the sequence."""
        if request_id not in self.allocations:
            return False
        start, curr, reserved = self.allocations[request_id]
        if curr >= reserved:
            return False
        self.allocations[request_id] = (start, curr + 1, reserved)
        return True

    def free(self, request_id: str) -> None:
        if request_id not in self.allocations:
            return
        start, _, reserved = self.allocations.pop(request_id)
        for slot in range(start, start + reserved):
            self.occupied_slots.discard(slot)

    def _find_contiguous_free(self, count: int) -> Optional[int]:
        consecutive = 0
        start_idx = 0
        for i in range(self.total_gpu_slots):
            if i in self.occupied_slots:
                consecutive = 0
                start_idx = i + 1
            else:
                consecutive += 1
                if consecutive == count:
                    return start_idx
        return None

    def stats(self) -> AllocationStats:
        total_reserved = sum(res for _, _, res in self.allocations.values())
        valid_tokens = sum(curr for _, curr, _ in self.allocations.values())
        wasted = total_reserved - valid_tokens
        waste_pct = (wasted / total_reserved * 100.0) if total_reserved > 0 else 0.0
        max_capacity = self.total_gpu_slots // self.max_seq_len
        return AllocationStats(
            total_slots_reserved=total_reserved,
            valid_tokens_stored=valid_tokens,
            wasted_slots=wasted,
            waste_percentage=waste_pct,
            active_requests=len(self.allocations),
            max_concurrent_capacity=max_capacity,
        )


@dataclass
class PhysicalBlock:
    block_id: int
    block_size: int
    tokens: List[str] = field(default_factory=list)
    ref_count: int = 0

    @property
    def is_full(self) -> bool:
        return len(self.tokens) >= self.block_size

    @property
    def free_slots(self) -> int:
        return self.block_size - len(self.tokens)


class PagedAttentionManager:
    """Simulates PagedAttention block table and physical block pool."""

    def __init__(self, num_blocks: int, block_size: int = 4) -> None:
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.total_gpu_slots = num_blocks * block_size
        self.physical_blocks = [
            PhysicalBlock(block_id=i, block_size=block_size) for i in range(num_blocks)
        ]
        self.free_blocks: List[int] = list(range(num_blocks))
        # Maps request_id to list of physical block ids
        self.block_tables: Dict[str, List[int]] = {}

    def allocate_request(self, request_id: str, tokens: List[str]) -> bool:
        """Allocate physical blocks on demand for initial tokens."""
        needed_blocks = (len(tokens) + self.block_size - 1) // self.block_size
        if len(self.free_blocks) < needed_blocks:
            return False

        table: List[int] = []
        token_idx = 0
        for _ in range(needed_blocks):
            p_id = self.free_blocks.pop(0)
            block = self.physical_blocks[p_id]
            block.ref_count = 1
            chunk = tokens[token_idx : token_idx + self.block_size]
            block.tokens = list(chunk)
            token_idx += len(chunk)
            table.append(p_id)

        self.block_tables[request_id] = table
        return True

    def append_token(self, request_id: str, token: str) -> bool:
        """Append a token, allocating a new physical block only when the current block is full."""
        if request_id not in self.block_tables:
            return False

        table = self.block_tables[request_id]
        if not table:
            if not self.free_blocks:
                return False
            p_id = self.free_blocks.pop(0)
            self.physical_blocks[p_id].ref_count = 1
            table.append(p_id)

        last_block_id = table[-1]
        last_block = self.physical_blocks[last_block_id]

        if last_block.is_full:
            # Last block is full; allocate a brand new unshared block from the free pool
            if not self.free_blocks:
                return False
            new_p_id = self.free_blocks.pop(0)
            new_block = self.physical_blocks[new_p_id]
            new_block.ref_count = 1
            new_block.tokens = [token]
            table.append(new_p_id)
            return True

        # Last block has room. If it is shared with another sequence, copy-on-write!
        if last_block.ref_count > 1:
            if not self.free_blocks:
                return False
            new_p_id = self.free_blocks.pop(0)
            new_block = self.physical_blocks[new_p_id]
            new_block.tokens = list(last_block.tokens) + [token]
            new_block.ref_count = 1
            last_block.ref_count -= 1
            table[-1] = new_p_id
            return True

        last_block.tokens.append(token)
        return True

    def fork_sequence(self, parent_id: str, child_id: str) -> bool:
        """Fork a request for parallel sampling using Copy-on-Write sharing."""
        if parent_id not in self.block_tables:
            return False
        parent_table = self.block_tables[parent_id]
        # Child shares all current physical blocks; increment ref counts
        child_table = list(parent_table)
        for p_id in child_table:
            self.physical_blocks[p_id].ref_count += 1
        self.block_tables[child_id] = child_table
        return True

    def free_request(self, request_id: str) -> None:
        if request_id not in self.block_tables:
            return
        table = self.block_tables.pop(request_id)
        for p_id in table:
            block = self.physical_blocks[p_id]
            block.ref_count -= 1
            if block.ref_count == 0:
                block.tokens = []
                self.free_blocks.append(p_id)

    def stats(self) -> AllocationStats:
        allocated_blocks = [b for b in self.physical_blocks if b.ref_count > 0]
        total_reserved = len(allocated_blocks) * self.block_size
        valid_tokens = sum(len(b.tokens) for b in allocated_blocks)
        wasted = total_reserved - valid_tokens
        waste_pct = (wasted / total_reserved * 100.0) if total_reserved > 0 else 0.0
        return AllocationStats(
            total_slots_reserved=total_reserved,
            valid_tokens_stored=valid_tokens,
            wasted_slots=wasted,
            waste_percentage=waste_pct,
            active_requests=len(self.block_tables),
            max_concurrent_capacity=self.total_gpu_slots // self.block_size,
        )
