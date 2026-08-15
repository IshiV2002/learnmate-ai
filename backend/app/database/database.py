import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Lock

from app.core.config import SQLITE_DATABASE_PATH
from app.database.models import (
    DocumentRecord,
    QuizAttemptRecord,
    QuizRecord,
    RecommendationRecord,
    TutorMessageRecord,
    TutorSessionRecord,
)


class DocumentDatabaseError(Exception):
    """Raised when document, quiz, or recommendation data cannot be read or changed."""


class DocumentDatabase:
    """Store document metadata, quiz attempts, and recommendations in local SQLite."""

    def __init__(self, database_path: Path = SQLITE_DATABASE_PATH) -> None:
        self.database_path = database_path
        self._initialized = False
        self._initialization_lock = Lock()

    def initialize(self) -> None:
        """Create database tables and indexes once when first needed."""
        if self._initialized:
            return

        with self._initialization_lock:
            if self._initialized:
                return

            try:
                self.database_path.parent.mkdir(parents=True, exist_ok=True)

                with closing(sqlite3.connect(self.database_path)) as connection:
                    with connection:
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS documents (
                                document_id TEXT PRIMARY KEY,
                                original_filename TEXT NOT NULL,
                                stored_filename TEXT NOT NULL,
                                page_count INTEGER NOT NULL,
                                pages_with_text INTEGER NOT NULL,
                                chunk_count INTEGER NOT NULL,
                                file_size_bytes INTEGER NOT NULL,
                                created_at TEXT NOT NULL
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS quizzes (
                                quiz_id TEXT PRIMARY KEY,
                                document_id TEXT NOT NULL,
                                title TEXT NOT NULL,
                                topic TEXT NOT NULL,
                                total_questions INTEGER NOT NULL,
                                difficulty TEXT NOT NULL,
                                questions_json TEXT NOT NULL,
                                created_at TEXT NOT NULL,
                                FOREIGN KEY(document_id) REFERENCES documents(document_id)
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_quizzes_document
                            ON quizzes(document_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS quiz_attempts (
                                attempt_id TEXT PRIMARY KEY,
                                student_id TEXT NOT NULL,
                                document_id TEXT NOT NULL,
                                quiz_id TEXT NOT NULL,
                                quiz_title TEXT NOT NULL,
                                total_questions INTEGER NOT NULL,
                                score INTEGER NOT NULL,
                                time_spent_seconds INTEGER NOT NULL,
                                submission_data_json TEXT NOT NULL,
                                created_at TEXT NOT NULL
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student
                            ON quiz_attempts(student_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_quiz_attempts_document
                            ON quiz_attempts(document_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS recommendations (
                                recommendation_id TEXT PRIMARY KEY,
                                attempt_id TEXT NOT NULL,
                                student_id TEXT NOT NULL,
                                document_id TEXT NOT NULL,
                                overall_score_percentage REAL NOT NULL,
                                mastery_level TEXT NOT NULL,
                                summary TEXT NOT NULL,
                                topic_mastery_json TEXT NOT NULL,
                                knowledge_gaps_json TEXT NOT NULL,
                                action_items_json TEXT NOT NULL,
                                tutor_handoff_json TEXT NOT NULL,
                                created_at TEXT NOT NULL,
                                FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(attempt_id)
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_recommendations_student
                            ON recommendations(student_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_recommendations_document
                            ON recommendations(document_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_recommendations_attempt
                            ON recommendations(attempt_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS tutor_sessions (
                                session_id TEXT PRIMARY KEY,
                                student_id TEXT NOT NULL,
                                document_id TEXT NOT NULL,
                                recommendation_id TEXT,
                                topic_focus TEXT NOT NULL,
                                mode TEXT NOT NULL,
                                created_at TEXT NOT NULL,
                                updated_at TEXT NOT NULL
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_tutor_sessions_student
                            ON tutor_sessions(student_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_tutor_sessions_document
                            ON tutor_sessions(document_id)
                            """
                        )
                        connection.execute(
                            """
                            CREATE TABLE IF NOT EXISTS tutor_messages (
                                message_id TEXT PRIMARY KEY,
                                session_id TEXT NOT NULL,
                                role TEXT NOT NULL,
                                content TEXT NOT NULL,
                                citations_json TEXT NOT NULL,
                                created_at TEXT NOT NULL,
                                FOREIGN KEY(session_id) REFERENCES tutor_sessions(session_id)
                            )
                            """
                        )
                        connection.execute(
                            """
                            CREATE INDEX IF NOT EXISTS idx_tutor_messages_session
                            ON tutor_messages(session_id)
                            """
                        )
            except (OSError, sqlite3.Error) as error:
                raise DocumentDatabaseError(
                    "The learning database could not be initialized."
                ) from error

            self._initialized = True

    def _connect(self) -> sqlite3.Connection:
        """Open a connection that returns rows with named columns."""
        self.initialize()
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> DocumentRecord:
        return DocumentRecord(
            document_id=row["document_id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            page_count=row["page_count"],
            pages_with_text=row["pages_with_text"],
            chunk_count=row["chunk_count"],
            file_size_bytes=row["file_size_bytes"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_quiz(row: sqlite3.Row) -> QuizRecord:
        return QuizRecord(
            quiz_id=row["quiz_id"],
            document_id=row["document_id"],
            title=row["title"],
            topic=row["topic"],
            total_questions=row["total_questions"],
            difficulty=row["difficulty"],
            questions_json=row["questions_json"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_quiz_attempt(row: sqlite3.Row) -> QuizAttemptRecord:
        return QuizAttemptRecord(
            attempt_id=row["attempt_id"],
            student_id=row["student_id"],
            document_id=row["document_id"],
            quiz_id=row["quiz_id"],
            quiz_title=row["quiz_title"],
            total_questions=row["total_questions"],
            score=row["score"],
            time_spent_seconds=row["time_spent_seconds"],
            submission_data_json=row["submission_data_json"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_recommendation(row: sqlite3.Row) -> RecommendationRecord:
        return RecommendationRecord(
            recommendation_id=row["recommendation_id"],
            attempt_id=row["attempt_id"],
            student_id=row["student_id"],
            document_id=row["document_id"],
            overall_score_percentage=float(row["overall_score_percentage"]),
            mastery_level=row["mastery_level"],
            summary=row["summary"],
            topic_mastery_json=row["topic_mastery_json"],
            knowledge_gaps_json=row["knowledge_gaps_json"],
            action_items_json=row["action_items_json"],
            tutor_handoff_json=row["tutor_handoff_json"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_tutor_session(row: sqlite3.Row) -> TutorSessionRecord:
        return TutorSessionRecord(
            session_id=row["session_id"],
            student_id=row["student_id"],
            document_id=row["document_id"],
            recommendation_id=row["recommendation_id"],
            topic_focus=row["topic_focus"],
            mode=row["mode"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_tutor_message(row: sqlite3.Row) -> TutorMessageRecord:
        return TutorMessageRecord(
            message_id=row["message_id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            citations_json=row["citations_json"],
            created_at=row["created_at"],
        )

    # -----------------------------------------------------------------
    # Document Operations
    # -----------------------------------------------------------------

    def create_document(self, document: DocumentRecord) -> None:
        """Insert metadata after the PDF has been indexed in ChromaDB."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO documents (
                            document_id,
                            original_filename,
                            stored_filename,
                            page_count,
                            pages_with_text,
                            chunk_count,
                            file_size_bytes,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            document.document_id,
                            document.original_filename,
                            document.stored_filename,
                            document.page_count,
                            document.pages_with_text,
                            document.chunk_count,
                            document.file_size_bytes,
                            document.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be saved."
            ) from error

    def list_documents(self) -> list[DocumentRecord]:
        """Return all documents with the newest uploads first."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM documents
                    ORDER BY created_at DESC, rowid DESC
                    """
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be listed."
            ) from error

        return [self._row_to_record(row) for row in rows]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        """Return one document, or None when its ID is unknown."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM documents WHERE document_id = ?",
                    (document_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_record(row)

    def delete_document(self, document_id: str) -> bool:
        """Delete one metadata row and report whether it existed."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    cursor = connection.execute(
                        "DELETE FROM documents WHERE document_id = ?",
                        (document_id,),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document metadata could not be deleted."
            ) from error

        return cursor.rowcount > 0

    # -----------------------------------------------------------------
    # Quiz Operations
    # -----------------------------------------------------------------

    def save_quiz(self, quiz: QuizRecord) -> None:
        """Persist a synthesized quiz and its question definitions."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO quizzes (
                            quiz_id,
                            document_id,
                            title,
                            topic,
                            total_questions,
                            difficulty,
                            questions_json,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            quiz.quiz_id,
                            quiz.document_id,
                            quiz.title,
                            quiz.topic,
                            quiz.total_questions,
                            quiz.difficulty,
                            quiz.questions_json,
                            quiz.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quiz could not be saved."
            ) from error

    def get_quiz(self, quiz_id: str) -> QuizRecord | None:
        """Retrieve a specific quiz by its unique quiz ID."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM quizzes WHERE quiz_id = ?",
                    (quiz_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quiz could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_quiz(row)

    def list_document_quizzes(self, document_id: str) -> list[QuizRecord]:
        """List all quizzes generated for a specific document."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM quizzes
                    WHERE document_id = ?
                    ORDER BY created_at DESC
                    """,
                    (document_id,),
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The document quizzes could not be listed."
            ) from error

        return [self._row_to_quiz(row) for row in rows]

    def list_all_quizzes(self) -> list[QuizRecord]:
        """List all generated quizzes across all documents, newest first."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM quizzes
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quizzes could not be listed."
            ) from error

        return [self._row_to_quiz(row) for row in rows]

    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete a generated quiz from the database."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    cursor = connection.execute(
                        "DELETE FROM quizzes WHERE quiz_id = ?",
                        (quiz_id,),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quiz could not be deleted."
            ) from error

        return cursor.rowcount > 0

    # -----------------------------------------------------------------
    # Quiz Attempt Operations
    # -----------------------------------------------------------------

    def save_quiz_attempt(self, attempt: QuizAttemptRecord) -> None:
        """Persist a student's quiz attempt and question responses."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO quiz_attempts (
                            attempt_id,
                            student_id,
                            document_id,
                            quiz_id,
                            quiz_title,
                            total_questions,
                            score,
                            time_spent_seconds,
                            submission_data_json,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            attempt.attempt_id,
                            attempt.student_id,
                            attempt.document_id,
                            attempt.quiz_id,
                            attempt.quiz_title,
                            attempt.total_questions,
                            attempt.score,
                            attempt.time_spent_seconds,
                            attempt.submission_data_json,
                            attempt.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quiz attempt could not be saved."
            ) from error

    def get_quiz_attempt(self, attempt_id: str) -> QuizAttemptRecord | None:
        """Retrieve a quiz attempt by its unique attempt ID."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM quiz_attempts WHERE attempt_id = ?",
                    (attempt_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The quiz attempt could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_quiz_attempt(row)

    def list_student_quiz_attempts(
        self, student_id: str
    ) -> list[QuizAttemptRecord]:
        """Retrieve all quiz attempts submitted by a student."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM quiz_attempts
                    WHERE student_id = ?
                    ORDER BY created_at DESC
                    """,
                    (student_id,),
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The student's quiz attempts could not be listed."
            ) from error

        return [self._row_to_quiz_attempt(row) for row in rows]

    # -----------------------------------------------------------------
    # Recommendation Operations
    # -----------------------------------------------------------------

    def save_recommendation(self, recommendation: RecommendationRecord) -> None:
        """Save a generated recommendation record."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO recommendations (
                            recommendation_id,
                            attempt_id,
                            student_id,
                            document_id,
                            overall_score_percentage,
                            mastery_level,
                            summary,
                            topic_mastery_json,
                            knowledge_gaps_json,
                            action_items_json,
                            tutor_handoff_json,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            recommendation.recommendation_id,
                            recommendation.attempt_id,
                            recommendation.student_id,
                            recommendation.document_id,
                            recommendation.overall_score_percentage,
                            recommendation.mastery_level,
                            recommendation.summary,
                            recommendation.topic_mastery_json,
                            recommendation.knowledge_gaps_json,
                            recommendation.action_items_json,
                            recommendation.tutor_handoff_json,
                            recommendation.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The recommendation could not be saved."
            ) from error

    def get_recommendation(
        self, recommendation_id: str
    ) -> RecommendationRecord | None:
        """Retrieve a specific recommendation by its ID."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM recommendations WHERE recommendation_id = ?",
                    (recommendation_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The recommendation could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_recommendation(row)

    def get_recommendation_by_attempt(
        self, attempt_id: str
    ) -> RecommendationRecord | None:
        """Retrieve recommendation linked to a specific quiz attempt."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM recommendations WHERE attempt_id = ?",
                    (attempt_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The attempt recommendation could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_recommendation(row)

    def list_student_recommendations(
        self, student_id: str
    ) -> list[RecommendationRecord]:
        """List all recommendations generated for a student, newest first."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM recommendations
                    WHERE student_id = ?
                    ORDER BY created_at DESC
                    """,
                    (student_id,),
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The student recommendations could not be listed."
            ) from error

        return [self._row_to_recommendation(row) for row in rows]

    # -----------------------------------------------------------------
    # Tutor Session & Message Operations
    # -----------------------------------------------------------------

    def create_tutor_session(self, session: TutorSessionRecord) -> None:
        """Persist a new AI tutor session."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO tutor_sessions (
                            session_id,
                            student_id,
                            document_id,
                            recommendation_id,
                            topic_focus,
                            mode,
                            created_at,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session.session_id,
                            session.student_id,
                            session.document_id,
                            session.recommendation_id,
                            session.topic_focus,
                            session.mode,
                            session.created_at,
                            session.updated_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The tutor session could not be created."
            ) from error

    def get_tutor_session(self, session_id: str) -> TutorSessionRecord | None:
        """Retrieve a tutor session by session ID."""
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM tutor_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The tutor session could not be read."
            ) from error

        if row is None:
            return None

        return self._row_to_tutor_session(row)

    def list_student_tutor_sessions(
        self, student_id: str
    ) -> list[TutorSessionRecord]:
        """List all tutor sessions for a student, newest first."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM tutor_sessions
                    WHERE student_id = ?
                    ORDER BY updated_at DESC, created_at DESC
                    """,
                    (student_id,),
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The student's tutor sessions could not be listed."
            ) from error

        return [self._row_to_tutor_session(row) for row in rows]

    def update_tutor_session_activity(
        self, session_id: str, updated_at: str, mode: str | None = None
    ) -> None:
        """Update last active timestamp and optionally mode for a tutor session."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    if mode:
                        connection.execute(
                            """
                            UPDATE tutor_sessions
                            SET updated_at = ?, mode = ?
                            WHERE session_id = ?
                            """,
                            (updated_at, mode, session_id),
                        )
                    else:
                        connection.execute(
                            """
                            UPDATE tutor_sessions
                            SET updated_at = ?
                            WHERE session_id = ?
                            """,
                            (updated_at, session_id),
                        )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The tutor session activity could not be updated."
            ) from error

    def delete_tutor_session(self, session_id: str) -> bool:
        """Delete a tutor session and its associated chat messages."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        "DELETE FROM tutor_messages WHERE session_id = ?",
                        (session_id,),
                    )
                    cursor = connection.execute(
                        "DELETE FROM tutor_sessions WHERE session_id = ?",
                        (session_id,),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The tutor session could not be deleted."
            ) from error

        return cursor.rowcount > 0

    def save_tutor_message(self, message: TutorMessageRecord) -> None:
        """Persist a message turn within a tutor session."""
        try:
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO tutor_messages (
                            message_id,
                            session_id,
                            role,
                            content,
                            citations_json,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            message.message_id,
                            message.session_id,
                            message.role,
                            message.content,
                            message.citations_json,
                            message.created_at,
                        ),
                    )
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The tutor message could not be saved."
            ) from error

    def get_session_messages(
        self, session_id: str
    ) -> list[TutorMessageRecord]:
        """Retrieve all messages in chronological order for a session."""
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM tutor_messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC, rowid ASC
                    """,
                    (session_id,),
                ).fetchall()
        except (OSError, sqlite3.Error) as error:
            raise DocumentDatabaseError(
                "The session messages could not be listed."
            ) from error

        return [self._row_to_tutor_message(row) for row in rows]

