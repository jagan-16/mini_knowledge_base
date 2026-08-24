from uuid import UUID
from fastapi import HTTPException
from pydantic_validation import ConversationResponse, ConversationSummaryResponse , MessageResponse
from sqlalchemy.orm import Session

from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository

from internal_models.conversation_context import (
    ConversationContext,
)


class ConversationService:

    def __init__(
        self,
        db: Session,
    ):

        self.conversation_repository = (
            ConversationRepository(db)
        )

        self.message_repository = (
            MessageRepository(db)
        )

    def prepare_conversation(
        self,
        conversation_id: UUID | None,
    ) -> ConversationContext:

        # Create a new conversation
        if conversation_id is None:

            conversation = (
                self.conversation_repository.create()
            )

            history = []

        # Continue an existing conversation
        else:

            conversation = (
                self.conversation_repository.get_by_id(
                    conversation_id
                )
            )

            if conversation is None:

                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )

            history = (
                self.message_repository.get_recent_history(
                    conversation_id=conversation.id,
                    exchanges=3,
                )
            )

        return ConversationContext(
            conversation=conversation,
            history=history,
        )

    def save_exchange(
        self,
        conversation_id: UUID,
        question: str,
        answer: str,
        citations: list | None = None,
    ) -> None:

        self.message_repository.save_many(

            conversation_id=conversation_id,

            messages=[
                ("user", question , []),
                ("assistant", answer ,  citations or []),
            ],
        )
        
    
    def list_conversations(
        self,
    ) -> list[ConversationSummaryResponse]:

        conversations = (
            self.conversation_repository.list_conversations()
        )

        return [

            ConversationSummaryResponse(

                conversation_id=conversation.id,

                created_at=conversation.created_at,
                
                updated_at=conversation.updated_at,

            )

            for conversation in conversations

        ]
        
    def get_conversation(
        self,
        conversation_id: UUID,
    ) -> ConversationResponse:

        conversation = (

            self.conversation_repository
            .get_by_id_with_messages(
                conversation_id
            )

        )

        if conversation is None:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )

        return ConversationResponse(

            conversation_id=conversation.id,

            messages=[

    MessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        citations = message.citations,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )

    for message in conversation.messages

]

        )