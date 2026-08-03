import os
from groq import Groq
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder

embedding_model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5"
)

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-base"
)

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

