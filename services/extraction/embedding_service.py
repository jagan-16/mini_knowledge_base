from sentence_transformers import SentenceTransformer
from services.model_loader import embedding_model

from internal_models.chunk_model import ChunkData


class EmbeddingService:



    def __init__(self):
        self.model = embedding_model

    def generate_embedding(self, text: str) -> list[float]:

        return self.model.encode(
            text,
            normalize_embeddings=True ,
            convert_to_numpy=True
        ).tolist()


    def generate_embeddings(
        self,
        chunks: list[ChunkData]
    ) -> list[list[float]]:

        texts = [
            chunk.chunk_text
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings.tolist()