from contextlib import contextmanager

import psycopg
from psycopg import errors
from psycopg.rows import dict_row

from config import DATABASE_CONNECT_TIMEOUT, DATABASE_URL


class DatabaseError(RuntimeError):
    pass


class ConversationNotFoundError(LookupError):
    def __init__(self, conversation_id):
        super().__init__(f"Conversation {conversation_id} not found.")
        self.conversation_id = conversation_id


@contextmanager
def connect():
    try:
        with psycopg.connect(
            DATABASE_URL,
            connect_timeout=DATABASE_CONNECT_TIMEOUT,
            row_factory=dict_row,
        ) as connection:
            yield connection
    except errors.UndefinedTable as exc:
        raise DatabaseError(
            "The database schema is not initialized. Run 'alembic upgrade head'."
        ) from exc
    except errors.InvalidCatalogName as exc:
        raise DatabaseError(
            "The database does not exist. Create it before running migrations."
        ) from exc
    except psycopg.Error as exc:
        raise DatabaseError(f"Could not access the database: {exc}") from exc


def get_history(conversation_id):
    with connect() as connection:
        conversation = connection.execute(
            "SELECT id FROM conversations WHERE id = %s",
            (conversation_id,),
        ).fetchone()
        if conversation is None:
            return None

        rows = connection.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = %s
            ORDER BY id
            """,
            (conversation_id,),
        ).fetchall()

    return [{"role": row["role"], "content": row["content"]} for row in rows]


def save_exchange(conversation_id, user_message, assistant_message):
    with connect() as connection:
        if conversation_id is None:
            conversation_id = connection.execute(
                "INSERT INTO conversations DEFAULT VALUES RETURNING id"
            ).fetchone()["id"]
        else:
            updated = connection.execute(
                """
                UPDATE conversations
                SET updated_at = now()
                WHERE id = %s
                RETURNING id
                """,
                (conversation_id,),
            ).fetchone()
            if updated is None:
                raise ConversationNotFoundError(conversation_id)

        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (%s, %s, %s)
                """,
                [
                    (conversation_id, "user", user_message),
                    (conversation_id, "assistant", assistant_message),
                ],
            )

    return conversation_id
