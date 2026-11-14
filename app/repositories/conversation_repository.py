from datetime import UTC, datetime
from uuid import uuid4

from app.database import Database


def current_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


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
                (conversion_id, title, system_prompt, timestamp, timestamp),
            )

        conversation = self.get_conversation(conversion_id)
        if conversation is None:
            raise RuntimeError(
                f"Created conversation could not be retrieved: {conversion_id}"
            )
        return conversation

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
            ORDER BY updated_at DESC, rowid DESC
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

        return bool(cursor.rowcount > 0)

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
                (conversation_id,),
            )

        return bool(cursor.rowcount > 0)

    # --------------------------------------------------
    # Message operations
    # --------------------------------------------------

    @staticmethod
    def _validate_message(role: str, content: str) -> None:
        if role not in ["user", "assistant"]:
            raise ValueError("Role must be either 'user' or 'assistant'")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> dict:
        return self.add_messages(
            conversation_id,
            [{"role": role, "content": content}],
        )[0]

    def add_messages(self, conversation_id: str, messages: list[dict]) -> list[dict]:
        """Persist multiple messages in a single transaction"""

        if not messages:
            return []

        for message in messages:
            if message.get("role") not in ("user", "assistant"):
                raise ValueError("Invalid message role.")

            content = message.get("content")

            if not isinstance(content, str) or not content.strip():
                raise ValueError("Message content cannot be empty")

        timestamp = current_timestamp()

        with self.database.get_connection() as connection:
            conversation = connection.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (conversation_id,),
            ).fetchone()

            if conversation is None:
                raise ValueError(f"Conversation not found: {conversation_id}")

            inserted_messages = []

            for message in messages:
                cursor = connection.execute(
                    """
                    INSERT INTO messages(
                        conversation_id, role, content, created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (conversation_id, message["role"], message["content"], timestamp),
                )

                inserted_messages.append(
                    {
                        "id": cursor.lastrowid,
                        "conversation_id": conversation_id,
                        "role": message["role"],
                        "content": message["content"],
                        "created_at": timestamp,
                    }
                )

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
    ) -> list[dict]:
        query = """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """

        with self.database.get_connection() as connection:
            rows = connection.execute(
                query,
                (conversation_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def search_conversations(self, keyword: str) -> list[dict]:
        """Search conversations by title or message content."""

        if not keyword or not keyword.strip():
            return []

        query = """
            SELECT DISTINCT c.*
            FROM conversations c
            LEFT JOIN messages m
                ON c.id = m.conversation_id
            WHERE c.title LIKE ?
                OR m.content LIKE ?
            ORDER BY c.updated_at DESC
        """

        search_term = f"%{keyword.strip()}%"

        with self.database.get_connection() as connection:
            rows = connection.execute(
                query,
                (search_term, search_term),
            ).fetchall()

        return [dict(row) for row in rows]

    def record_usage(
        self,
        conversation_id: str,
        context_data: dict,
        llm_metrics: dict,
    ) -> None:
        created_at = datetime.now(UTC).isoformat()

        with self.database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO llm_usage (
                    conversation_id,
                    estimated_prompt_tokens,
                    actual_prompt_tokens,
                    generated_tokens,
                    context_window_tokens,
                    max_input_tokens,
                    usage_percent,
                    prompt_eval_duration_ns,
                    eval_duration_ns,
                    total_duration_ns,
                    load_duration_ns,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    context_data["estimated_prompt_tokens"],
                    llm_metrics.get("actual_prompt_tokens"),
                    llm_metrics.get("generated_tokens"),
                    context_data["context_window_tokens"],
                    context_data["max_input_tokens"],
                    context_data["usage_percent"],
                    llm_metrics.get("prompt_eval_duration_ns"),
                    llm_metrics.get("eval_duration_ns"),
                    llm_metrics.get("total_duration_ns"),
                    llm_metrics.get("load_duration_ns"),
                    created_at,
                ),
            )

    def get_usage_summary(self, conversation_id: str) -> dict:
        with self.database.get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS request_count,
                    SUM(estimated_prompt_tokens) AS total_estimated_tokens,
                    SUM(actual_prompt_tokens) AS total_actual_prompt_tokens,
                    SUM(generated_tokens) AS total_generated_tokens,
                    MAX(usage_percent) AS peak_usage_percent,
                    AVG(usage_percent) AS average_usage_percent
                FROM llm_usage
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()

        return dict(row) if row else {}
