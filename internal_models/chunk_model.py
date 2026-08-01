from dataclasses import dataclass


@dataclass
class ChunkData:
    chunk_index: int
    page_number: int
    chunk_text: str
    chunk_hash: str
    token_count: int 
   