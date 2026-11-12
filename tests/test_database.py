import tempfile
import unittest
from pathlib import Path

from app.database import Database


class TestDatabase(unittest.TestCase):

    def test_database_initialization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Database(Path(temp_dir) / "test.db")

            database.initialize()

            with database.get_connection() as connection:
                tables = connection.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """).fetchall()

            table_names = {row["name"] for row in tables}

            self.assertIn("conversations", table_names)
            self.assertIn("messages", table_names)

    def test_foreign_key_cascade(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Database(Path(temp_dir) / "test.db")
            database.initialize()

            with database.get_connection() as connection:
                connection.execute("""
                    INSERT INTO conversations
                    VALUES ('test-id', 'Test', NULL, 'now', 'now')
                    """)

                connection.execute("""
                    INSERT INTO messages
                    (conversation_id, role, content, created_at)
                    VALUES ('test-id', 'user', 'Hello', 'now')
                    """)

                connection.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    ("test-id",),
                )

                count = connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM messages
                    WHERE conversation_id = ?
                    """,
                    ("test-id",),
                ).fetchone()["count"]

            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
