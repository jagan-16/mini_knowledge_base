from sentence_transformers import SentenceTransformer
from services.model_loader import embedding_model

from internal_models.chunk_model import ChunkData

import logging 


class EmbeddingService:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    


    def __init__(self):
        self.model = embedding_model

    def generate_embedding(self, text: str) -> list[float]:
        self.logger.info(
                    "Chunk created | index=%s pages=%s tokens=%s",
                    
                          
                        
                    
                )
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
        for chunk in chunks:
            self.logger.info(
            "Chunk created | index=%s pages=%s tokens=%s",
            
                    chunk.chunk_index,
                    chunk.page_numbers,
                    chunk.token_count,
                
            
        )

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings.tolist()