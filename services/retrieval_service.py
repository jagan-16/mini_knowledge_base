from sqlalchemy.orm import Session

from database_model import Chunk
from repositories.retrieval_repository import RetrievalRepository


class RetrievalService:

    def __init__(self, db: Session):
        self.retrieval_repository = RetrievalRepository(db)

    def retrieve_chunks(
        self,
        query_embedding: list[float],
        top_k: int
    ) -> list[Chunk]:

        return self.retrieval_repository.retrieve(
            query_embedding=query_embedding,
            top_k=top_k
        )