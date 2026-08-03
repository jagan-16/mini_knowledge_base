FROM python:3.12-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-base')"


EXPOSE 8501

EXPOSE 8000


CMD ["uvicorn" , "main:app" , "--host" , "0.0.0.0" , "--port" , "8000"]