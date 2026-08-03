from uuid import UUID

from sqlalchemy.orm import Session

from database_model import Message


class MessageRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def save(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> Message:

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(message)

        self.db.flush()

        return message

    def save_many(
        self,
        conversation_id: UUID,
        messages: list[tuple[str, str]],
    ) -> None:

        db_messages = [

            Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )

            for role, content in messages
        ]

        self.db.add_all(
            db_messages
        )

        self.db.flush()

    def get_recent_history(
        self,
        conversation_id: UUID,
        exchanges : int = 3,
    ) -> list[Message]:

        limit = exchanges * 2
        
        messages = (

            self.db.query(
                Message
            )

            .filter(
                Message.conversation_id == conversation_id
            )

            .order_by(
                Message.created_at.desc()
            )

            .limit(limit)

            .all()

        )
        
        return messages[::-1]
    
    def get_all_messages(
    self,
    conversation_id: UUID,
) -> list[Message]:

        return (
            self.db.query(Message)
            .filter(
                Message.conversation_id == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )