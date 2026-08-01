from sentence_transformers import SentenceTransformer

from internal_models.chunk_model import ChunkData


class EmbeddingService:

    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5"
    ):

        self.model = SentenceTransformer(
            model_name
        )
        
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