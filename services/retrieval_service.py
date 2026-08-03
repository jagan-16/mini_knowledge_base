from sqlalchemy.orm import Session
from internal_models.retrieval_filter import RetrievalFilter
from internal_models.retrieved_chunk import RetrievedChunk
from repositories.retrieval_repository import RetrievalRepository


class RetrievalService:

    def __init__(
        self,
        db: Session,
    ):
        self.retrieval_repository = RetrievalRepository(
            db
        )
    def retrieve(
        self,
        query_embedding: list[float],
        retrieval_filter: RetrievalFilter,
    ) -> list[RetrievedChunk]:

        return self.retrieval_repository.retrieve(
            query_embedding=query_embedding,
            retrieval_filter=retrieval_filter,
        )