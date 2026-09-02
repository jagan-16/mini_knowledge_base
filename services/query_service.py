
from fastapi import HTTPException
from metadata_filter_mapper import MetadataFilterMapper
from sqlalchemy.orm import Session
from pathlib import Path

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

        self.metadata_filter_mapper = MetadataFilterMapper()
        
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

            # --------------------------------
            # 1. Generate query embedding
            # --------------------------------
            query_embedding = (
                self.embedding_service.generate_embedding(
                    request.question
                )
            )
            

            # --------------------------------
            # 2. Build retrieval filter
            # --------------------------------
            metadata_filters = None

            if request.metadata_filters is not None:
                metadata_filters = self.metadata_filter_mapper.to_internal(
                    request.metadata_filters
                )

            retrieval_filter = RetrievalFilter(
                top_k=request.top_k,
                document_id=request.document_id,
                metadata_filters=metadata_filters,
            )
            
            
            # --------------------------------
            # 3. Vector retrieval
            # --------------------------------
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
                
            # --------------------------------
            # 4. Cross Encoder reranking
            # --------------------------------

            reranked_chunks = (
                self.reranking_service.rerank(
                    question=request.question,
                    chunks=retrieved_chunks,
                )
            )


            # --------------------------------
            # 5. Build LLM prompt
            # --------------------------------
            prompt = (
                self.prompt_service.build_prompt(
                    question=request.question,
                    chunks=reranked_chunks,
                )
            )
            
            # --------------------------------
            # 6. Generate answer
            # --------------------------------
            answer = (
                self.llm_service.complete(
                    prompt=prompt,
                    history=conversation_context.history,
                )
            )
            
            
            
            # --------------------------------
            # 7. Build unique citations
            # --------------------------------

            seen = set()
            citations = []

            for chunk in reranked_chunks:

                    page_numbers = sorted(
                        set(chunk.page_numbers)
                    )

                    key = (
                        chunk.document_id,
                        tuple(page_numbers),
                    )

                    if key in seen:
                        continue

                    seen.add(key)

                    first_page = (
                        page_numbers[0]
                        if page_numbers
                        else 1
                    )

                    citations.append(
                        Citation(
                            document_id=chunk.document_id,
                            title=chunk.document_title,
                            page_numbers=page_numbers,
                            document_url=(
                                f"http://localhost:8000/uploads/"
                                f"{Path(chunk.file_path).name}"
                                f"#page={first_page}"
                            ),
                        )
                    )
                                                
            # --------------------------------
            # 8. Convert Pydantic citations
            #    to JSON-compatible data
            # --------------------------------
            citation_data = [
                            citation.model_dump(mode="json")
                            for citation in citations
                        ]
            
            
            # --------------------------------
            # 9. Persist conversation
            # --------------------------------

            self.conversation_service.save_exchange(

                conversation_id=
                conversation_context.conversation.id,

                question=request.question,

                answer=answer,
                
                citations=citation_data,
            )
            
            # --------------------------------
            # 10. Commit everything
            # --------------------------------

            self.db.commit()
            
           
            # --------------------------------
            # 11. Return API response
            # --------------------------------

            return QuestionResponse(

                conversation_id=
                conversation_context.conversation.id,

                answer=answer,

                citations=citations
            )

        except Exception:

            self.db.rollback()

            raise