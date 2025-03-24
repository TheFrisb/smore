from typing import List, Union

from langchain_core.messages import HumanMessage, AIMessage

from accounts.models import User
from ai_assistant.models import Message


class ConversationHistoryFetcher:
    def fetch(self, user: User) -> List[Union[HumanMessage, AIMessage]]:
        recent_messages = Message.objects.filter(
            user=user
        ).order_by("-created_at")[:10]
        direction_map = {
            Message.Direction.OUTBOUND: HumanMessage,
            Message.Direction.INBOUND: AIMessage,
        }
        return [
            direction_map[msg.direction](content=f"[{msg.created_at}] {msg.message}")
            for msg in reversed(recent_messages)
        ]
