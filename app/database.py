import sqlite3
from pathlib import Path
from contextlib import contextmanager

from app.config import DATABASE_PATH

class Database:

    def __init__(self):
        self.db_path = Path(DATABASE_PATH)
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    @contextmanager
    def get_connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        try:
            connection.execute('PRAGMA foreign_keys = ON')
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):

        schema = """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            system_prompt TEXT,
            create_at TEXT NOT NULL,
            update_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK (ROLE IN ('user', 'assistant')),
            context TEXT NOT NULL,
            create_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
            REFERENCES conversations(id)
            ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
            idx_message_conversation
        ON messages(conversation_id);
        """

        with self.get_connection() as connection:
            connection.executescript(schema)

        print(f"Database initialized: {self.db_path}")
