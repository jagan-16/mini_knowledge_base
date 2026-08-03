from dataclasses import dataclass
from database_model import Conversation, Message


@dataclass
class ConversationContext:

    conversation: Conversation

    history: list[Message]