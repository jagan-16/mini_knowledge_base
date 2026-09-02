from sqlalchemy.orm import Session

from database_model import Chunk, Document

from internal_models.retrieval_filter import RetrievalFilter
from internal_models.retrieved_chunk import RetrievedChunk

from repositories.metadata_filter_query_builder import (
    MetadataFilterQueryBuilder,
)


class RetrievalRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

        self.metadata_filter_query_builder = (
            MetadataFilterQueryBuilder()
        )

    def retrieve(
        self,
        query_embedding: list[float],
        retrieval_filter: RetrievalFilter,
    ) -> list[RetrievedChunk]:

        distance = Chunk.embedding.cosine_distance(
            query_embedding
        )

        filters = []

        # --------------------------------
        # 1. Document scope
        # --------------------------------

        if retrieval_filter.document_id is not None:

            filters.append(
                Chunk.document_id
                == retrieval_filter.document_id
            )

        # --------------------------------
        # 2. Metadata scope
        # --------------------------------

        elif retrieval_filter.metadata_filters:

            metadata_expression = (
                self.metadata_filter_query_builder.build(
                    retrieval_filter.metadata_filters
                )
            )

            if metadata_expression is not None:

                filters.append(
                    metadata_expression
                )

        # --------------------------------
        # 3. Retrieval query
        # --------------------------------

        query = (
            self.db.query(
                Chunk,
                Document,
                distance.label(
                    "similarity_score"
                ),
            )
            .join(Chunk.document)
            .filter(*filters)
            .order_by(distance)
            .limit(
                retrieval_filter.top_k
            )
        )

        # --------------------------------
        # 4. Execute
        # --------------------------------

        results = query.all()

        # --------------------------------
        # 5. Convert database rows
        #    into RetrievedChunk
        # --------------------------------

        return [
            RetrievedChunk(
                document_id=document.id,
                document_title=document.title,
                file_path=document.file_path,
                page_numbers=chunk.page_numbers,
                chunk_text=chunk.chunk_text,
                similarity_score=float(
                    similarity_score
                ),
            )
            for (
                chunk,
                document,
                similarity_score,
            ) in results
        ]