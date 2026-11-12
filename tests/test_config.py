import unittest

from app.config import validate_config


class TestConfiguration(unittest.TestCase):

    def test_valid_configuration(self):
        self.assertTrue(validate_config())


if __name__ == "__main__":
    unittest.main()