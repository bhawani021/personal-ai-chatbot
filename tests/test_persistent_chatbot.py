import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.database import Database
from app.exceptions import (
    ContextLimitExceededError,
    InvalidMessageError,
    LLMServiceError,
    NoActiveConversationError,
)
from app.repositories.conversation_repository import ConversationRepository
from app.services.persistent_chatbot import PersistentChatbot
from app.services.token_context_tracker import TokenContextTracker


class FakeLLMService:
    last_usage = {}

    def generate(self, messages):
        return f"Mock response to: {messages[-1]['content']}"

    def generate_stream(self, messages):
        response = self.generate(messages)

        for word in response.split(" "):
            yield word + " "


class TestPersistentChatbot(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        database = Database()
        database.db_path = Path(self.temp_dir.name) / "test.db"
        database.initialize()

        self.database = database
        self.repository = ConversationRepository(database)

        self.chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=FakeLLMService(),
        )

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

    def test_chat_records_usage_summary(self):
        self.chatbot.create_new_conversation()

        self.chatbot.chat("Track this request")

        summary = self.chatbot.get_usage_summary()
        self.assertEqual(summary["request_count"], 1)
        self.assertGreater(summary["total_estimated_tokens"], 0)

    def test_chat_rejects_context_over_budget_without_persisting(self):
        conversation = self.chatbot.create_new_conversation()
        self.chatbot.context_tracker = TokenContextTracker(
            context_window_tokens=64,
            max_output_tokens=16,
            safety_margin=8,
            warning_percent=80,
        )

        with self.assertRaises(ContextLimitExceededError):
            self.chatbot.chat("A" * 200)

        self.assertEqual(self.repository.get_messages(conversation["id"]), [])
        self.assertEqual(
            self.chatbot.get_usage_summary()["request_count"],
            0,
        )

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
                self.last_usage = {}

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

        self.chatbot.create_new_conversation()
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

        with self.assertRaises(InvalidMessageError):
            self.chatbot.chat("   ")

    def test_resume_latest_conversation(self):
        with patch(
            "app.repositories.conversation_repository.current_timestamp",
            return_value="2026-01-01T00:00:00.000000+00:00",
        ):
            self.chatbot.create_new_conversation("First")
            self.chatbot.chat("First message")

            second = self.chatbot.create_new_conversation("Second")
            self.chatbot.chat("Second message")

            resumed = self.chatbot.resume_latest_conversation()

        self.assertEqual(resumed["id"], second["id"])

    def test_rename_conversation(self):
        conversation = self.chatbot.create_new_conversation()

        result = self.chatbot.rename_conversation(
            conversation["id"],
            "My Python Learning",
        )

        self.assertTrue(result)

        updated = self.repository.get_conversation(conversation["id"])

        self.assertEqual(updated["title"], "My Python Learning")

    def test_delete_conversation(self):
        conversation = self.chatbot.create_new_conversation()

        self.chatbot.chat("Hello")

        result = self.chatbot.delete_conversation(conversation["id"])

        self.assertTrue(result)
        self.assertIsNone(self.repository.get_conversation(conversation["id"]))
        self.assertIsNone(self.chatbot.get_current_conversation())

    def test_search_conversations(self):
        conversation = self.chatbot.create_new_conversation("Python Learning")

        self.chatbot.chat("Explain Python")

        results = self.chatbot.search_conversations("Python")

        self.assertTrue(any(item["id"] == conversation["id"] for item in results))

    def test_chat_without_active_conversation(self):
        with self.assertRaises(NoActiveConversationError):
            self.chatbot.chat("Hello")

    def test_llm_failure_does_not_save_messages(self):
        class FailingLLM:
            def generate(self, messages):
                raise LLMServiceError("LLM unavailable")

        chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=FailingLLM(),
        )

        conversation = chatbot.create_new_conversation()

        with self.assertRaises(LLMServiceError):
            chatbot.chat("Hello")

        messages = self.repository.get_messages(conversation["id"])

        self.assertEqual(messages, [])

    def test_invalid_message(self):
        self.chatbot.create_new_conversation()

        with self.assertRaises(InvalidMessageError):
            self.chatbot.chat("   ")

    def test_exchange_is_persisted_atomically(self):
        conversation = self.chatbot.create_new_conversation()

        # Force the assistant-message insertion to fail.
        with self.database.get_connection() as connection:
            connection.execute("""
                CREATE TRIGGER reject_assistant_message
                BEFORE INSERT ON messages
                WHEN NEW.role = 'assistant'
                BEGIN
                    SELECT RAISE(ABORT, 'Test failure');
                END;
            """)

        with self.assertRaises(sqlite3.IntegrityError):
            self.repository.add_messages(
                conversation["id"],
                [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                ],
            )

        messages = self.repository.get_messages(conversation["id"])

        # The user message must also have rolled back.
        self.assertEqual(messages, [])

    def test_chat_stream_returns_chunks(self):
        self.chatbot.create_new_conversation()

        chunks = list(self.chatbot.chat_stream("What is Python?"))

        response = "".join(chunks)

        self.assertIn("Mock response", response)

        history = self.chatbot.get_history()

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")

    def test_streaming_failure_does_not_persist_exchange(self):
        class FailingStreamLLM:

            def generate_stream(self, messages):
                yield "Partial response"

                raise LLMServiceError("Connection lost")

        chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=FailingStreamLLM(),
        )

        conversation = chatbot.create_new_conversation()

        with self.assertRaises(LLMServiceError):
            list(chatbot.chat_stream("Hello"))

        history = self.repository.get_messages(conversation["id"])

        self.assertEqual(history, [])

    def test_streaming_uses_previous_conversation_history(self):
        class InspectingStreamLLM:

            def __init__(self):
                self.received_messages = None
                self.last_usage = {}

            def generate(self, messages):
                return "First response"

            def generate_stream(self, messages):
                self.received_messages = messages
                yield "Alex"

        llm = InspectingStreamLLM()

        chatbot = PersistentChatbot(
            repository=self.repository,
            llm_service=llm,
        )

        chatbot.create_new_conversation()

        chatbot.chat("My name is Alex.")

        list(chatbot.chat_stream("What is my name?"))

        self.assertEqual(
            llm.received_messages[-3]["content"],
            "My name is Alex.",
        )
        self.assertEqual(
            llm.received_messages[-2]["content"],
            "First response",
        )

        self.assertEqual(
            llm.received_messages[-1]["content"],
            "What is my name?",
        )


if __name__ == "__main__":
    unittest.main()
