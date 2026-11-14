import unittest

from app.services.token_context_tracker import TokenContextTracker


class TestTokenContextTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = TokenContextTracker(
            context_window_tokens=4096,
            max_output_tokens=512,
            safety_margin=128,
            warning_percent=80,
        )

    def test_available_input_budget(self):
        self.assertEqual(
            self.tracker.max_input_tokens,
            3456,
        )

    def test_estimate_tokens(self):
        messages = [
            {
                "role": "user",
                "content": "Hello world",
            }
        ]

        result = self.tracker.estimate_tokens(messages)

        self.assertEqual(result, 8)

    def test_normal_context_usage(self):
        messages = [
            {
                "role": "user",
                "content": "Hello",
            }
        ]

        result = self.tracker.analyze(messages)

        self.assertEqual(result["status"], "normal")
        self.assertGreater(result["remaining_tokens"], 0)

    def test_warning_context_usage(self):
        messages = [
            {
                "role": "user",
                "content": "a" * 10000,
            }
        ]

        result = self.tracker.analyze(messages)

        self.assertEqual(result["status"], "warning")

    def test_context_limit_exceeded(self):
        messages = [
            {
                "role": "user",
                "content": "a" * 15000,
            }
        ]

        result = self.tracker.analyze(messages)

        self.assertEqual(result["status"], "exceeded")
        self.assertEqual(result["remaining_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
