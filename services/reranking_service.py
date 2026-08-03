from services.model_loader import reranker_model
from internal_models.retrieved_chunk import RetrievedChunk


class RerankingService:

    def __init__(self):

        self.model = reranker_model

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        top_k: int = 3,
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

        return [

            chunk

            for chunk, _ in ranked[:top_k]
        ]