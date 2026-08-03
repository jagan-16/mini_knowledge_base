from fastapi import HTTPException
from sqlalchemy.orm import Session

from pydantic_validation import (
    Citation,
    QuestionRequest,
    QuestionResponse,
)

from internal_models.retrieval_filter import RetrievalFilter

from services.conversation_service import ConversationService
from services.extraction.embedding_service import EmbeddingService
from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.reranking_service import RerankingService
from services.retrieval_service import RetrievalService


class QueryService:

    def __init__(
        self,
        db: Session,
        
    ):

        self.db = db

        self.embedding_service = EmbeddingService()

        self.retrieval_service = RetrievalService(db)

        self.reranking_service = RerankingService()

        self.prompt_service = PromptService()

        self.llm_service = LLMService()

        self.conversation_service = ConversationService(db)

    def ask(
        self,
        request: QuestionRequest,
    ) -> QuestionResponse:

        try:

            conversation_context = (
                self.conversation_service.prepare_conversation(
                    request.conversation_id
                )
            )

            query_embedding = (
                self.embedding_service.generate_embedding(
                    request.question
                )
            )

            retrieval_filter = RetrievalFilter(

                top_k=request.top_k,

                document_id=request.document_id,

                document_type=request.document_type,

                department=request.department,

            )

            retrieved_chunks = (
                self.retrieval_service.retrieve(
                    query_embedding=query_embedding,
                    retrieval_filter=retrieval_filter,
                )
            )

            if not retrieved_chunks:

                raise HTTPException(
                    status_code=404,
                    detail="No relevant information found."
                )

            reranked_chunks = (
                self.reranking_service.rerank(
                    question=request.question,
                    chunks=retrieved_chunks,
                )
            )

            prompt = (
                self.prompt_service.build_prompt(
                    question=request.question,
                    chunks=reranked_chunks,
                )
            )

            answer = (
                self.llm_service.generate(
                    prompt=prompt,
                    history=conversation_context.history,
                )
            )

            self.conversation_service.save_exchange(

                conversation_id=
                conversation_context.conversation.id,

                question=request.question,

                answer=answer,
            )

            self.db.commit()

            return QuestionResponse(

                conversation_id=
                conversation_context.conversation.id,

                answer=answer,

                citations=[

                    Citation(

                        document_id=chunk.document_id,

                        title=chunk.document_title,

                        page_number=chunk.page_number,

                        document_url=chunk.file_path,

                    )

                    for chunk in reranked_chunks

                ]

            )

        except Exception:

            self.db.rollback()

            raise