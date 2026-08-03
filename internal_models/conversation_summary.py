from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ConversationSummary:

    conversation_id: UUID

    created_at: datetime

   