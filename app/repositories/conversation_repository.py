from datetime import datetime, timezone
from uuid import uuid4

from app.database import Database


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ConversationRepository:

    def __init__(self, database: Database):
        self.database = database

    # --------------------------------------------------
    # Conversation operations
    # --------------------------------------------------
    def create_conversation(
            self,
            title: str = "New Connection",
            system_prompt: str | None = None,
    ) -> dict:
        conversion_id = str(uuid4())
        timestamp = current_timestamp()

        query = """
            INSERT INTO conversations (
                id,
                title,
                system_prompt,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """

        with self.database.get_connection() as connection:
            connection.execute(
                query,
                (
                    conversion_id,
                    title,
                    system_prompt,
                    timestamp,
                    timestamp
                ),
            )

        return self.get_conversation(conversion_id)

    def get_conversation(
            self,
            conversation_id: str,
    ) -> dict | None:

        query = """
            SELECT * FROM conversations
            WHERE ID = ?
        """

        with self.database.get_connection() as connection:
            row = connection.execute(
                query,
                (conversation_id,),
            ).fetchone()

        return dict(row) if row else None

    def list_conversations(self) -> list[dict]:

        query = """
            SELECT *
            FROM conversations
            ORDER BY updated_at DESC
        """

        with self.database.get_connection() as connection:
            rows = connection.execute(query).fetchall()

        return [dict(row) for row in rows]

    def update_title(
            self,
            conversation_id: str,
            title: str,
    ) -> bool:
        query = """
            UPDATE conversations
            SET title = ?,
              updated_at = ?
            WHERE id = ?
        """

        with self.database.get_connection() as connection:
            cursor = connection.execute(
                query,
                (
                    title,
                    current_timestamp(),
                    conversation_id,
                ),
            )

        return cursor.rowcount > 0

    def delete_conversation(
            self,
            conversation_id: str,
    ) -> bool:

        query = """
            DELETE FROM conversations WHERE id = ?
        """

        with self.database.get_connection() as connection:
            cursor = connection.execute(
                query,
                (
                    conversation_id,
                ),
            )

        return cursor.rowcount > 0

    # --------------------------------------------------
    # Message operations
    # --------------------------------------------------

    @staticmethod
    def _validate_message(role: str, content: str) -> None:
        if role not in ["user", "assistant"]:
            raise ValueError(
                "Role must be either 'user' or 'assistant'"
            )

        if not content or not content.strip():
            raise ValueError(
                "Message content cannot be empty"
            )

    def add_message(
            self,
            conversation_id: str,
            role: str,
            content: str,
    ) -> dict:
        return self.add_messages(
            conversation_id,
            [(role, content)],
        )[0]

    def add_messages(
            self,
            conversation_id: str,
            messages: list[tuple[str, str]],
    ) -> list[dict]:
        if not messages:
            return []

        for role, content in messages:
            self._validate_message(role, content)

        timestamp = current_timestamp()

        insert_message_query = """
            INSERT INTO messages (
                conversation_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """

        with self.database.get_connection() as connection:
            conversation = connection.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()

            if conversation is None:
                raise ValueError(
                    f"Conversation not found: {conversation_id}"
                )

            inserted_messages = []
            for role, content in messages:
                cursor = connection.execute(
                    insert_message_query,
                    (
                        conversation_id,
                        role,
                        content,
                        timestamp,
                    ),
                )
                inserted_messages.append({
                    "id": cursor.lastrowid,
                    "conversation_id": conversation_id,
                    "role": role,
                    "content": content,
                    "created_at": timestamp,
                })

            connection.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE id = ?
                """,
                (timestamp, conversation_id),
            )

        return inserted_messages

    def get_messages(
            self,
            conversation_id: str,
    ):
        query = """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """

        with self.database.get_connection() as connection:
            rows = connection.execute(
                query,
                (
                    conversation_id,
                ),
            ).fetchall()

        return [dict(row) for row in rows]
