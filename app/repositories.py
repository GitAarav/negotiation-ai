from typing import Any

from app.database import Database
from app.models import StoredInteraction


class UserPreferenceRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def set_preferred_language(self, user_id: str, language_code: str) -> None:
        with self.database.connect() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences (user_id, preferred_language)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET preferred_language = excluded.preferred_language
                """,
                (user_id, language_code),
            )

    def get_preferred_language(self, user_id: str) -> str | None:
        with self.database.connect() as conn:
            row = conn.execute(
                "SELECT preferred_language FROM user_preferences WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return None if row is None else str(row["preferred_language"])


class InteractionRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, payload: dict[str, Any]) -> StoredInteraction:
        with self.database.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO interactions (
                    user_id,
                    channel,
                    source_language,
                    target_language,
                    original_text,
                    english_text,
                    negotiation_response_en,
                    localized_response_text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["user_id"],
                    payload["channel"],
                    payload["source_language"],
                    payload["target_language"],
                    payload["original_text"],
                    payload["english_text"],
                    payload["negotiation_response_en"],
                    payload["localized_response_text"],
                ),
            )
            row = conn.execute(
                "SELECT * FROM interactions WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return StoredInteraction.model_validate(dict(row))
