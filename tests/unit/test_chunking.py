import pytest
from app.services.chunking_service import ChunkingService

@pytest.mark.asyncio
async def test_empty_input():
    assert await ChunkingService(10, 2).chunk("  ", {}) == []

@pytest.mark.asyncio
async def test_short_document():
    chunks = await ChunkingService(10, 2).chunk("short", {"a": 1})
    assert len(chunks) == 1 and chunks[0].content == "short" and chunks[0].metadata == {"a": 1}

@pytest.mark.asyncio
async def test_overlap_and_order():
    chunks = await ChunkingService(10, 2).chunk("abcdefghij klmnopqrst uvwxyz", {})
    assert len(chunks) >= 3
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert chunks[0].content[-2:] in chunks[1].content
