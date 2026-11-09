from app.config import SYSTEM_PROMPT
from app.repositories.conversation_repository import ConversationRepository
from app.services.llm_service import LLMService

class PersistentChatbot:
    """
    Coordinates conversation persistence and LLM interactions.

    ConversationRepository handles database operations.
    LLMService handles communication with Ollama.
    """

    def __init__(
            self,
            repository: ConversationRepository,
            llm_service: LLMService | None = None
    ):
        self.repository = repository
        self.llm_service = llm_service or LLMService()
        self.current_conversation_id: str | None = None

    def create_new_conversation(self, title="New conversation") -> dict:

        conversation = self.repository.create_conversation(
            title=title,
            system_prompt=SYSTEM_PROMPT,
        )

        self.current_conversation_id = conversation["id"]
        return conversation

    def switch_conversation(self, conversation_id: str) -> dict:
        conversation = self.repository.get_conversation(conversation_id)

        if conversation is None:
            raise ValueError(
                f"Conversation not found: {conversation_id}"
            )

        self.current_conversation_id = conversation_id

        return conversation

    def get_current_conversation(self) -> dict | None:
        if not self.current_conversation_id:
            return None

        return self.repository.get_conversation(
            self.current_conversation_id
        )

    def chat(self, user_message: str) -> str:
        if not user_message or not user_message.strip():
            raise ValueError("Message cannot be empty")

        conversation = self.get_current_conversation()

        if conversation is None:
            raise RuntimeError(
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

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        messages.extend(
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in stored_messages
        )

        # 3. Add the current user message to the request
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # 4. Get the LLM response
        # IF Ollama fails, neither message is persisted
        assistant_response = self.llm_service.generate(messages)

        #5. Persist both messages after successful generation
        self.repository.add_message(
            self.current_conversation_id,
            "user",
            user_message
        )

        self.repository.add_message(
            self.current_conversation_id,
            "assistant",
            assistant_response
        )

        # 6. Automatically name a new conversation using it;s first message
        if not stored_messages:
            title = user_message.strip().replace("\n", " ")[:50]
            self.repository.update_title(
                self.current_conversation_id,
                title or "New conversation"
            )

        return assistant_response

    def get_history(self) -> list[dict]:
        if not self.current_conversation_id:
            return []

        return self.repository.get_messages(self.current_conversation_id)

    def list_conversations(self) -> list[dict]:
        return self.repository.list_conversations()
