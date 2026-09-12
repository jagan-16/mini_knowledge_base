from sqlalchemy.orm import Session
from internal_models.retrieval_filter import RetrievalFilter
from internal_models.retrieved_chunk import RetrievedChunk
from repositories.retrieval_repository import RetrievalRepository
import logging


class RetrievalService:

    def __init__(
        self,
        db: Session,
    ):
        self.retrieval_repository = RetrievalRepository(
            db
        )
        self.logger = logging.getLogger(__name__)
    def retrieve(
        self,
        query_embedding: list[float],
        retrieval_filter: RetrievalFilter,
    ) -> list[RetrievedChunk]:

        retrieved_chunks = self.retrieval_repository.retrieve(
            query_embedding=query_embedding,
            retrieval_filter=retrieval_filter,
        )
        
        self.logger.info(
            "Retrieved %d chunks",
            len(retrieved_chunks),
        )

        for rank, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):
            self.logger.info(
                "\n"
                "===== RETRIEVED CHUNK %d =====\n"
                "Chunk ID: %s\n"
                "Document ID: %s\n"
                "Score: %s\n"
                "Content:\n%s\n"
                "==============================",
                rank,
                getattr(chunk, "id", None),
                getattr(chunk, "document_id", None),
                getattr(chunk, "score", None),
                getattr(chunk, "chunk_text", None),
            )

        
        
        return retrieved_chunks 