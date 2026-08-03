from sqlalchemy.orm import Session

from database_model import Chunk, Document
from internal_models.retrieval_filter import RetrievalFilter
from internal_models.retrieved_chunk import RetrievedChunk


class RetrievalRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def retrieve(
        self,
        query_embedding: list[float],
        retrieval_filter: RetrievalFilter,
    ) -> list[RetrievedChunk]:

        distance = Chunk.embedding.cosine_distance(
            query_embedding
        )

        query = (
            self.db.query(
                Chunk,
                Document,
                distance.label("similarity_score"),
            )
            .join(Chunk.document)
        )

        # Highest priority: Search a single document
        if retrieval_filter.document_id is not None:

            query = query.filter(
                Chunk.document_id == retrieval_filter.document_id
            )

        # Otherwise apply metadata filters
        else:

            if retrieval_filter.document_type is not None:

                query = query.filter(
                    Chunk.chunk_metadata["document_type"].astext
                    == retrieval_filter.document_type
                )

            if retrieval_filter.department is not None:

                query = query.filter(
                    Chunk.chunk_metadata["department"].astext
                    == retrieval_filter.department
                )

        results = (
            query
            .order_by(distance)
            .limit(retrieval_filter.top_k)
            .all()
        )

        return [

            RetrievedChunk(

                document_id=document.id,

                document_title = document.title,
               
                file_path = document.file_path,

                page_number=chunk.page_number,

                chunk_text=chunk.chunk_text,

                similarity_score=float(distance),

            )

            for chunk, document, distance in results
        ]