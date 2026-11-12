import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from app.exceptions import LLMServiceError
from app.services.llm_service import LLMService


class TestLLMService(unittest.TestCase):

    @patch("app.services.llm_service.Client")
    def test_successful_generation(self, mock_client_class):
        mock_client = Mock()

        mock_client.chat.return_value = SimpleNamespace(
            message=SimpleNamespace(
                content="Python is a programming language."
            )
        )

        mock_client_class.return_value = mock_client

        service = LLMService()

        result = service.generate([
            {"role": "user", "content": "What is Python?"}
        ])

        self.assertEqual(
            result,
            "Python is a programming language.",
        )

        mock_client.chat.assert_called_once()

    @patch("app.services.llm_service.Client")
    def test_llm_failure(self, mock_client_class):
        mock_client = Mock()

        mock_client.chat.side_effect = ConnectionError(
            "Ollama unavailable"
        )

        mock_client_class.return_value = mock_client

        service = LLMService()

        with self.assertRaises(LLMServiceError):
            service.generate([
                {"role": "user", "content": "Hello"}
            ])

    @patch("app.services.llm_service.Client")
    def test_empty_response(self, mock_client_class):
        mock_client = Mock()

        mock_client.chat.return_value = SimpleNamespace(
            message=SimpleNamespace(content=" ")
        )

        mock_client_class.return_value = mock_client

        service = LLMService()

        with self.assertRaises(LLMServiceError):
            service.generate([
                {"role": "user", "content": "Hello"}
            ])


if __name__ == "__main__":
    unittest.main()