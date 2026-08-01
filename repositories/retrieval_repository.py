from sqlalchemy.orm import Session

from database_model import Chunk


class RetrievalRepository:

    def __init__(self, db: Session):
        self.db = db

    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int = 5
    ):

        return (
            self.db.query(
                Chunk,
                Chunk.embedding.cosine_distance(query_embedding).label("distance")
            )
            .order_by(
                Chunk.embedding.cosine_distance(query_embedding)
            )
            .limit(top_k)
            .all()
        )