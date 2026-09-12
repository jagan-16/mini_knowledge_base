from services.model_loader import reranker_model
from internal_models.retrieved_chunk import RetrievedChunk
import logging  


class RerankingService:


    
    def __init__(self):

        self.model = reranker_model
        self.logger = logging.getLogger(__name__)

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:

        if not chunks:
            return []

        pairs = [

            (
                question,
                chunk.chunk_text,
            )

            for chunk in chunks
        ]

        scores = self.model.predict(
            pairs
        )

        ranked = sorted(
            zip(
                chunks,
                scores,
            ),
            key=lambda item: item[1],
            reverse=True,
        )

        selected_chunks = [

            chunk

            for chunk, _ in ranked[:top_k]
        ]
        
        self.logger.info(
            "Reranked %d chunks, returning top %d",
            len(chunks),
            len(selected_chunks),
        )

        for rank, (chunk, score) in enumerate(
            ranked[:top_k],
            start=1,
        ):
            self.logger.info(
                "\n"
                "===== RERANKED CHUNK %d =====\n"
                "Chunk ID: %s\n"
                "Document ID: %s\n"
                "Chunk Index: %s\n"
                "Reranker Score: %s\n"
                "Content:\n%s\n"
                "==============================",
                rank,
                getattr(chunk, "id", None),
                getattr(chunk, "document_id", None),
                getattr(chunk, "chunk_index", None),
                score,
                getattr(chunk, "chunk_text", None),
            )

        
       
        return selected_chunks