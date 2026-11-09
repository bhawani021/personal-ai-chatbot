import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.repositories.conversation_repository import ConversationRepository
from app.services.persistent_chatbot import PersistentChatbot


class FakeLLMService:
    """Simulates Ollama responses for testing."""

    def generate(self, messages):
        return f"Mock response to: {messages[-1]['content']}"


class TestPersistentChatbot(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        database = Database()
        database.db_path = Path(self.temp_dir.name) / "test.db"
        database.initialize()

        self.repository = ConversationRepository(database)

        self.chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=FakeLLMService(),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_conversation(self):
        conversation = self.chatbot.create_new_conversation()

        self.assertIsNotNone(conversation["id"])
        self.assertEqual(
            self.chatbot.current_conversation_id,
            conversation["id"],
        )

    def test_chat_persists_messages(self):
        self.chatbot.create_new_conversation()

        response = self.chatbot.chat("What is Python?")

        self.assertEqual(
            response,
            "Mock response to: What is Python?",
        )

        history = self.chatbot.get_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_conversation_survives_chatbot_restart(self):
        conversation = self.chatbot.create_new_conversation()
        conversation_id = conversation["id"]

        self.chatbot.chat("What is Python?")

        # Simulate restarting the chatbot.
        restarted_chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=FakeLLMService(),
        )

        restarted_chatbot.switch_conversation(conversation_id)

        history = restarted_chatbot.get_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(
            history[0]["content"],
            "What is Python?",
        )

    def test_previous_messages_are_sent_to_llm(self):
        class InspectingLLM:
            def __init__(self):
                self.received_messages = None

            def generate(self, messages):
                self.received_messages = messages
                return "Test response"

        llm = InspectingLLM()

        chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=llm,
        )

        chatbot.create_new_conversation()
        chatbot.chat("My name is Alex.")
        chatbot.chat("What is my name?")

        self.assertEqual(
            llm.received_messages[-3]["content"],
            "My name is Alex.",
        )
        self.assertEqual(
            llm.received_messages[-2]["content"],
            "Test response",
        )
        self.assertEqual(
            llm.received_messages[-1]["content"],
            "What is my name?",
        )

    def test_switch_conversation(self):
        first = self.chatbot.create_new_conversation()
        self.chatbot.chat("First conversation")

        second = self.chatbot.create_new_conversation()
        self.chatbot.chat("Second conversation")

        self.chatbot.switch_conversation(first["id"])

        history = self.chatbot.get_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(
            history[0]["content"],
            "First conversation",
        )

    def test_empty_message_rejected(self):
        self.chatbot.create_new_conversation()

        with self.assertRaises(ValueError):
            self.chatbot.chat("   ")


if __name__ == "__main__":
    unittest.main()