"""Unit tests verifying PagedAttention simulation mechanics and metrics."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType


def _load_toy_module() -> ModuleType:
    module_path = (
        Path(__file__).parent.parent
        / "topics"
        / "2026"
        / "11"
        / "paged-attention"
        / "toy.py"
    )
    spec = importlib.util.spec_from_file_location("paged_attention_toy", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


toy = _load_toy_module()


def test_contiguous_kv_manager_fragmentation() -> None:
    # 64 slots total, max sequence length 16 (capacity for 4 requests)
    manager = toy.ContiguousKVManager(total_gpu_slots=64, max_seq_len=16)

    # Allocate request 1 with 4 tokens, request 2 with 8 tokens
    assert manager.allocate("req_1", initial_tokens=4)
    assert manager.allocate("req_2", initial_tokens=8)

    stats = manager.stats()
    assert stats.active_requests == 2
    # 2 requests reserved 16 slots each = 32 slots reserved
    assert stats.total_slots_reserved == 32
    # Only 4 + 8 = 12 tokens stored
    assert stats.valid_tokens_stored == 12
    # 20 slots wasted (over 60% waste)
    assert stats.wasted_slots == 20
    assert stats.waste_percentage == 62.5


def test_paged_attention_dynamic_allocation() -> None:
    # 16 physical blocks of size 4 (64 slots total)
    manager = toy.PagedAttentionManager(num_blocks=16, block_size=4)

    # Allocate request 1 with 7 tokens -> needs 2 blocks (8 slots)
    assert manager.allocate_request("req_1", ["t0", "t1", "t2", "t3", "t4", "t5", "t6"])
    stats = manager.stats()
    assert stats.total_slots_reserved == 8
    assert stats.valid_tokens_stored == 7
    assert stats.wasted_slots == 1
    assert stats.waste_percentage == 12.5

    # Append 1 token -> fills block 1 completely (0 wasted slots)
    assert manager.append_token("req_1", "t7")
    stats = manager.stats()
    assert stats.valid_tokens_stored == 8
    assert stats.wasted_slots == 0
    assert stats.waste_percentage == 0.0

    # Append 9th token -> allocates a fresh 3rd block on demand
    assert manager.append_token("req_1", "t8")
    assert len(manager.block_tables["req_1"]) == 3
    stats = manager.stats()
    assert stats.total_slots_reserved == 12
    assert stats.valid_tokens_stored == 9
    assert stats.wasted_slots == 3


def test_paged_attention_copy_on_write() -> None:
    manager = toy.PagedAttentionManager(num_blocks=16, block_size=4)

    # Parent prompt with 4 tokens (1 full block)
    assert manager.allocate_request("parent", ["p0", "p1", "p2", "p3"])
    assert len(manager.block_tables["parent"]) == 1
    parent_block = manager.block_tables["parent"][0]
    assert manager.physical_blocks[parent_block].ref_count == 1

    # Fork sequence for parallel sampling
    assert manager.fork_sequence("parent", "child")
    assert manager.block_tables["child"] == [parent_block]
    assert manager.physical_blocks[parent_block].ref_count == 2

    # Append to child -> since parent_block is full, it allocates a new unshared block for child
    assert manager.append_token("child", "c4")
    assert len(manager.block_tables["child"]) == 2
    child_new_block = manager.block_tables["child"][1]
    assert child_new_block != parent_block
    assert manager.physical_blocks[child_new_block].tokens == ["c4"]
    # Shared prefix block remains shared
    assert manager.physical_blocks[parent_block].ref_count == 2


def test_paged_attention_partial_block_cow() -> None:
    manager = toy.PagedAttentionManager(num_blocks=16, block_size=4)

    # Parent prompt with 2 tokens (partial block)
    assert manager.allocate_request("parent", ["p0", "p1"])
    parent_block = manager.block_tables["parent"][0]
    assert manager.physical_blocks[parent_block].ref_count == 1

    # Fork sequence
    assert manager.fork_sequence("parent", "child")
    assert manager.physical_blocks[parent_block].ref_count == 2

    # Child appends a token into the partial block -> triggers Copy-on-Write
    assert manager.append_token("child", "c2")
    child_block = manager.block_tables["child"][0]
    assert child_block != parent_block
    assert manager.physical_blocks[child_block].tokens == ["p0", "p1", "c2"]
    assert manager.physical_blocks[child_block].ref_count == 1

    # Parent remains unaffected
    assert manager.block_tables["parent"][0] == parent_block
    assert manager.physical_blocks[parent_block].tokens == ["p0", "p1"]
    assert manager.physical_blocks[parent_block].ref_count == 1
