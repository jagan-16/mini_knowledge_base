from dataclasses import asdict
from uuid import UUID
import logging
from sqlalchemy.orm import Session
from database_model import Chunk
from internal_models.chunk_metadata import ChunkMetadata
from internal_models.chunk_model import ChunkData


logger = logging.getLogger(__name__)

class ChunkRepository:

    def __init__(self, db: Session):

        self.db = db

    def save_chunks(
        self,
        document_id: UUID,
        metadata: ChunkMetadata ,
        chunks: list[ChunkData],
        embeddings: list[list[float]]
    ) -> None:

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must match."
            )
     
        db_chunks = []

        for chunk, embedding in zip(chunks, embeddings):

            db_chunk = Chunk(
                document_id=document_id,
                chunk_metadata={**asdict(metadata)},
                chunk_hash=chunk.chunk_hash,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                embedding=embedding,
                page_number=chunk.page_number,
                token_count=chunk.token_count
            )

            db_chunks.append(db_chunk)

        self.db.add_all(db_chunks)

        self.db.commit()
    

         