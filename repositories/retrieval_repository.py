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
            
            if retrieval_filter.metadata_filters:

           
                for key, value in retrieval_filter.metadata_filters.items():

                    filters.append(
                        Document.doc_metadata[key].astext == value
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
                page_numbers=chunk.page_numbers,
                chunk_text=chunk.chunk_text,
                similarity_score=float(similarity_score),
            )
            for chunk, document, similarity_score in results
        ]