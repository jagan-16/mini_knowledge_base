from sqlalchemy.orm import Session

from database_model import Chunk
from services.extraction.embedding_service import EmbeddingService
from services.retrieval_service import RetrievalService


class QueryService:

    def __init__(self, db: Session):
        self.embedding_service = EmbeddingService()
        self.retrieval_service = RetrievalService(db)

    def query(
        self,
        question: str,
        top_k: int
    ) -> list[Chunk]:

        query_embedding = self.embedding_service.generate_embedding(
            question
        )

        retrieved_chunks = self.retrieval_service.retrieve_chunks(
            query_embedding=query_embedding,
            top_k=top_k
        )

        return retrieved_chunks