from uuid import UUID

from sqlalchemy.orm import Session , joinedload


from database_model import Conversation

    


class ConversationRepository:

    def __init__(
        self,
        db: Session,
        
    ):
        self.db = db

    def create(
        self,
    ) -> Conversation:

        conversation = Conversation()

        self.db.add(
            conversation
        )

        self.db.flush()

        return conversation

    def get_by_id(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:

        return (
            self.db.query(
                Conversation
            )
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )
        
        
    def get_by_id_with_messages(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:

        return (

            self.db.query(
                Conversation
            )

            .options(
                joinedload(
                    Conversation.messages
                )
            )

            .filter(
                Conversation.id == conversation_id
            )

            .first()

        )

    def list_conversations(
        self,
    ) -> list[Conversation]:

        return (

            self.db.query(
                Conversation
            )

            .order_by(
                Conversation.created_at.desc()
            )

            .all()

        )