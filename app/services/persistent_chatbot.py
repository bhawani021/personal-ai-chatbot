import logging

from app.config import SYSTEM_PROMPT
from app.exceptions import (
    ConversationNotFoundError,
    InvalidMessageError,
    NoActiveConversationError,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PersistentChatbot:
    """
    Coordinates conversation persistence and LLM interactions.

    ConversationRepository handles database operations.
    LLMService handles communication with Ollama.
    """

    def __init__(
            self,
            repository: ConversationRepository,
            llm_service=None
    ):
        self.repository = repository
        self.llm_service = llm_service or LLMService()
        self.current_conversation_id = None

    def create_new_conversation(self, title="New conversation") -> dict:

        conversation = self.repository.create_conversation(
            title=title,
            system_prompt=SYSTEM_PROMPT,
        )

        self.current_conversation_id = conversation["id"]

        logger.info(
            "Created conversation: %s",
            conversation["id"]
        )

        return conversation

    def switch_conversation(self, conversation_id: str) -> dict:
        conversation = self.repository.get_conversation(conversation_id)

        if conversation is None:
            raise ConversationNotFoundError(
                f"Conversation not found: {conversation_id}"
            )

        self.current_conversation_id = conversation_id

        logger.info("Switched conversation: %s", conversation_id)

        return conversation

    def get_current_conversation(self) -> dict | None:
        if not self.current_conversation_id:
            return None

        return self.repository.get_conversation(
            self.current_conversation_id
        )

    def chat(self, user_message: str) -> str:
        if not user_message or not user_message.strip():
            raise InvalidMessageError("Message cannot be empty")

        conversation = self.get_current_conversation()

        if conversation is None:
            raise NoActiveConversationError(
                "No active conversation. Create or open a conversation first."
            )

        # 1. Load existing messages from SQLite
        stored_messages = self.repository.get_messages(
            self.current_conversation_id
        )

        # 2. Prepare for LLM context
        system_prompt = (
                conversation["system_prompt"] or SYSTEM_PROMPT
        )

        llm_messages = [
            {"role": "system", "content": system_prompt}
        ]

        llm_messages.extend(
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in stored_messages
        )

        # 3. Add the current user message to the request
        llm_messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # 4. Get the LLM response
        # IF Ollama fails, neither message is persisted
        assistant_response = self.llm_service.generate(
            llm_messages
        )

        # 5. Persist both messages after successful generation
        self.repository.add_messages(
            self.current_conversation_id,
            [
                {
                    "role": "user",
                    "content": user_message.strip()
                },
                {
                    "role": "assistant",
                    "content": assistant_response,
                }
            ],
        )

        # 6. Automatically name a new conversation using it;s first message
        if not stored_messages:
            title = user_message.strip().replace("\n", " ")[:50]
            self.repository.update_title(
                self.current_conversation_id,
                title or "New conversation"
            )

        logger.info(
            "Completed chat exchange for conversation: %s",
            self.current_conversation_id,
        )

        return assistant_response

    def get_history(self) -> list[dict]:
        if not self.current_conversation_id:
            return []

        return self.repository.get_messages(self.current_conversation_id)

    def list_conversations(self) -> list[dict]:
        return self.repository.list_conversations()

    def resume_latest_conversation(self) -> dict:
        """ Resume the most recently updated conversation"""

        conversations = self.repository.list_conversations()

        if conversations:
            return self.switch_conversation(conversations[0]["id"])

        return self.create_new_conversation()

    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """ Rename an existing conversation"""
        if not title or not title.strip():
            raise InvalidMessageError("Conversation title cannot be empty")

        updated = self.repository.update_title(
            conversation_id,
            title.strip(),
        )

        if not updated:
            raise ConversationNotFoundError(
                f"Conversation not found: {conversation_id}"
            )

        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """ Delete a conversation and its associated messages"""

        deleted = self.repository.delete_conversation(conversation_id)

        if not deleted:
            raise ConversationNotFoundError(
                f"Conversation not found: {conversation_id}"
            )

        if self.current_conversation_id == conversation_id:
            self.current_conversation_id = None

        return True

    def search_conversations(self, keyword: str) -> list[dict]:
        """Search conversations by title or message content"""

        return self.repository.search_conversations(keyword)
