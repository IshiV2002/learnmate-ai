import json
import sqlite3
import tempfile
import unittest
from dataclasses import replace
from contextlib import closing
from pathlib import Path

from app.database.database import DocumentDatabase, DocumentDatabaseError
from app.database.models import (
    DocumentRecord,
    QuizAttemptRecord,
    RecommendationRecord,
    UserRecord,
)


def make_record(document_id: str, created_at: str) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        original_filename=f"{document_id}.pdf",
        stored_filename=f"{document_id}.stored.pdf",
        page_count=2,
        pages_with_text=2,
        chunk_count=3,
        file_size_bytes=100,
        created_at=created_at,
    )


def make_user(user_id: str, email: str) -> UserRecord:
    return UserRecord(
        user_id=user_id,
        full_name="Test Student",
        email=email,
        password_hash="$argon2id$test-hash",
        created_at="2026-01-01T00:00:00+00:00",
    )


def make_quiz_attempt(
    attempt_id: str, student_id: str, document_id: str, created_at: str
) -> QuizAttemptRecord:
    return QuizAttemptRecord(
        attempt_id=attempt_id,
        student_id=student_id,
        document_id=document_id,
        quiz_id="quiz_101",
        quiz_title="Operating Systems: Memory Management",
        total_questions=5,
        score=3,
        time_spent_seconds=120,
        submission_data_json=json.dumps([{"question_id": "q1", "is_correct": True}]),
        created_at=created_at,
    )


def make_recommendation(
    recommendation_id: str, attempt_id: str, student_id: str, document_id: str, created_at: str
) -> RecommendationRecord:
    return RecommendationRecord(
        recommendation_id=recommendation_id,
        attempt_id=attempt_id,
        student_id=student_id,
        document_id=document_id,
        overall_score_percentage=60.0,
        mastery_level="Developing / Review Needed",
        summary="Review virtual memory concepts.",
        topic_mastery_json=json.dumps([{"topic": "Paging", "accuracy_percentage": 50.0}]),
        knowledge_gaps_json=json.dumps([{"topic": "Paging", "severity": "MODERATE"}]),
        action_items_json=json.dumps([{"topic": "Paging", "title": "Read Paging section"}]),
        tutor_handoff_json=json.dumps({"target_topics": ["Paging"]}),
        created_at=created_at,
    )


class DocumentDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initialization_creates_database_and_documents_table(self) -> None:
        self.database.initialize()

        self.assertTrue(self.database_path.is_file())
        self.assertEqual(self.database.list_documents(), [])

    def test_user_creation_lookup_and_unique_email(self) -> None:
        user = make_user("user-1", "student@example.com")
        self.database.create_user(user)

        self.assertEqual(self.database.get_user_by_id("user-1"), user)
        self.assertEqual(
            self.database.get_user_by_email("STUDENT@example.com"),
            user,
        )

        with self.assertRaises(DocumentDatabaseError):
            self.database.create_user(
                make_user("user-2", "student@example.com")
            )

    def test_document_queries_can_be_restricted_to_owner(self) -> None:
        first = make_user("user-1", "first@example.com")
        second = make_user("user-2", "second@example.com")
        self.database.create_user(first)
        self.database.create_user(second)
        first_document = replace(
            make_record("first", "2026-01-01T00:00:00+00:00"),
            user_id=first.user_id,
        )
        second_document = replace(
            make_record("second", "2026-02-01T00:00:00+00:00"),
            user_id=second.user_id,
        )
        self.database.create_document(first_document)
        self.database.create_document(second_document)

        self.assertEqual(self.database.list_documents(first.user_id), [first_document])
        self.assertIsNone(self.database.get_document("second", first.user_id))
        self.assertFalse(self.database.delete_document("second", first.user_id))

    def test_existing_database_is_migrated_without_assigning_legacy_documents(self) -> None:
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE documents (
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
                    INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "legacy",
                        "legacy.pdf",
                        "legacy.stored.pdf",
                        1,
                        1,
                        1,
                        100,
                        "2026-01-01T00:00:00+00:00",
                    ),
                )

        migrated_database = DocumentDatabase(self.database_path)
        migrated_database.initialize()

        self.assertIsNotNone(migrated_database.get_document("legacy"))
        self.assertEqual(migrated_database.list_documents("new-user"), [])

    def test_document_creation_and_primary_key_uniqueness(self) -> None:
        record = make_record("document-1", "2026-01-01T00:00:00+00:00")
        self.database.create_document(record)

        self.assertEqual(self.database.get_document("document-1"), record)

        with self.assertRaises(DocumentDatabaseError):
            self.database.create_document(record)

    def test_metadata_persists_after_database_reinitialization(self) -> None:
        record = make_record("persistent", "2026-01-01T00:00:00+00:00")
        self.database.create_document(record)

        reopened_database = DocumentDatabase(self.database_path)

        self.assertEqual(reopened_database.get_document("persistent"), record)

    def test_list_documents_orders_newest_first(self) -> None:
        older = make_record("older", "2026-01-01T00:00:00+00:00")
        newer = make_record("newer", "2026-02-01T00:00:00+00:00")
        self.database.create_document(older)
        self.database.create_document(newer)

        self.assertEqual(self.database.list_documents(), [newer, older])

    def test_delete_document_removes_metadata(self) -> None:
        self.database.create_document(
            make_record("document-1", "2026-01-01T00:00:00+00:00")
        )

        self.assertTrue(self.database.delete_document("document-1"))
        self.assertIsNone(self.database.get_document("document-1"))
        self.assertFalse(self.database.delete_document("document-1"))

    def test_save_and_retrieve_quiz_attempt(self) -> None:
        attempt = make_quiz_attempt("att_1", "student_a", "doc_1", "2026-01-01T00:00:00+00:00")
        self.database.save_quiz_attempt(attempt)

        retrieved = self.database.get_quiz_attempt("att_1")
        self.assertEqual(retrieved, attempt)

        student_attempts = self.database.list_student_quiz_attempts("student_a")
        self.assertEqual(len(student_attempts), 1)
        self.assertEqual(student_attempts[0].attempt_id, "att_1")

    def test_save_and_retrieve_recommendation(self) -> None:
        attempt = make_quiz_attempt("att_2", "student_b", "doc_1", "2026-01-01T00:00:00+00:00")
        self.database.save_quiz_attempt(attempt)

        rec = make_recommendation("rec_1", "att_2", "student_b", "doc_1", "2026-01-01T00:00:00+00:00")
        self.database.save_recommendation(rec)

        retrieved = self.database.get_recommendation("rec_1")
        self.assertEqual(retrieved, rec)

        by_attempt = self.database.get_recommendation_by_attempt("att_2")
        self.assertEqual(by_attempt, rec)

        student_recs = self.database.list_student_recommendations("student_b")
        self.assertEqual(len(student_recs), 1)
        self.assertEqual(student_recs[0].recommendation_id, "rec_1")
