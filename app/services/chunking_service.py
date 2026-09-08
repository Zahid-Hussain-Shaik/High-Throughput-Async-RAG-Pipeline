from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkDraft:
    chunk_index: int
    content: str
    metadata: dict


class ChunkingService:
    def __init__(self, chunk_size: int, overlap: int) -> None:
        self.chunk_size, self.overlap = chunk_size, overlap

    async def chunk(self, content: str, metadata: dict) -> list[ChunkDraft]:
        text = content.strip()
        if not text:
            return []
        chunks: list[ChunkDraft] = []
        start, index = 0, 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = max(text.rfind(" ", start, end), text.rfind("\n", start, end))
                if boundary > start + self.chunk_size // 2:
                    end = boundary
            piece = text[start:end].strip()
            if piece:
                chunks.append(ChunkDraft(index, piece, metadata.copy()))
                index += 1
            if end >= len(text):
                break
            start = max(end - self.overlap, start + 1)
        return chunks
