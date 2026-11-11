import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import main


class TestMain(unittest.TestCase):

    def test_search_without_keyword_shows_usage(self):
        output = StringIO()

        with (
            patch("main.Database"),
            patch("main.ConversationRepository"),
            patch("main.PersistentChatbot") as chatbot_class,
            patch("builtins.input", side_effect=["/search", "/exit"]),
            redirect_stdout(output),
        ):
            chatbot = chatbot_class.return_value
            chatbot.create_new_conversation.return_value = {
                "id": "conversation-id",
                "title": "New conversation",
            }

            main.main()

        self.assertIn("Usage: /search <keyword>", output.getvalue())
        self.assertNotIn("Error:", output.getvalue())
        chatbot.search_conversations.assert_not_called()


if __name__ == "__main__":
    unittest.main()
