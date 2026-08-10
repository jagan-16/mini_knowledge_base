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

        # --------------------------------
        # 1. Determine retrieval scope
        # --------------------------------

        filters = []

        if retrieval_filter.document_id is not None:

            # Single-document search
            filters.append(
                Chunk.document_id == retrieval_filter.document_id
            )

        else:

            # Metadata / global search
            if retrieval_filter.document_type is not None:

                filters.append(
                    Chunk.chunk_metadata["document_type"].astext
                    == retrieval_filter.document_type
                )

            if retrieval_filter.department is not None:

                filters.append(
                    Chunk.chunk_metadata["department"].astext
                    == retrieval_filter.department
                )

        # --------------------------------
        # 2. Build query
        # --------------------------------

        query = (
            self.db.query(
                Chunk,
                Document,
                distance.label("similarity_score"),
            )
            .join(Chunk.document)
            .filter(*filters)
            .order_by(distance)
            .limit(retrieval_filter.top_k)
        )

        # --------------------------------
        # 3. Execute
        # --------------------------------

        results = query.all()

        # --------------------------------
        # 4. Convert DB rows to domain model
        # --------------------------------

        return [
            RetrievedChunk(
                document_id=document.id,
                document_title=document.title,
                file_path=document.file_path,
                page_number=chunk.page_number,
                chunk_text=chunk.chunk_text,
                similarity_score=float(similarity_score),
            )
            for chunk, document, similarity_score in results
        ]