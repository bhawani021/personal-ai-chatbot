import tempfile
import unittest

from pathlib import Path

from app.database import Database
from app.repositories.conversation_repository import (
    ConversationRepository,
)

class TestConversationRepository(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.database = Database()
        self.database.db_path = (
                Path(self.temp_dir.name) / "test_chatbot.db"
        )

        self.database.initialize()

        self.repository = ConversationRepository(
            self.database
        )

    def test_create_conversation(self):
        conversation = self.repository.create_conversation(
            title="Python Learning"
        )

        self.assertIsNotNone(conversation)
        self.assertEqual(
            conversation["title"],
            "Python Learning",
        )

    def test_add_and_get_messages(self):
        conversation = self.repository.create_conversation(
            title="Test Chat"
        )

        conversation_id = conversation["id"]

        self.repository.add_message(
            conversation_id,
            "user",
            "What is Python?",
        )

        self.repository.add_message(
            conversation_id,
            "assistant",
            "Python is a programming language.",
        )

        messages = self.repository.get_messages(
            conversation_id
        )

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_list_conversations(self):
        self.repository.create_conversation("Chat 1")
        self.repository.create_conversation("Chat 2")

        conversations = self.repository.list_conversations()

        self.assertEqual(len(conversations), 2)

    def test_update_title(self):
        conversation = self.repository.create_conversation(
            "Old title"
        )

        result = self.repository.update_title(
            conversation["id"],
            "New title",
        )

        self.assertTrue(result)

        updated = self.repository.get_conversation(
            conversation["id"]
        )

        self.assertEqual(updated["title"], "New title")

    def test_delete_conversation(self):
        conversation = self.repository.create_conversation(
            "Delete me"
        )

        conversation_id = conversation["id"]

        self.repository.add_message(
            conversation_id,
            "user",
            "Hello",
        )

        result = self.repository.delete_conversation(
            conversation_id
        )

        self.assertTrue(result)
        self.assertIsNone(
            self.repository.get_conversation(conversation_id)
        )

        # Verify cascade deletion.
        self.assertEqual(
            self.repository.get_messages(conversation_id),
            [],
        )

    def test_invalid_role_is_rejected(self):
        conversation = self.repository.create_conversation()

        with self.assertRaises(ValueError):
            self.repository.add_message(
                conversation["id"],
                "system",
                "Invalid role",
            )

if __name__ == "__main__":
    unittest.main()
