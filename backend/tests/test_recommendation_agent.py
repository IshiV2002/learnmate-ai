import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.agents.recommendation_agent import (
    RecommendationAgent,
    RecommendationAgentError,
)
from app.database.database import DocumentDatabase
from app.database.models import (
    DocumentRecord,
    QuestionMistakeDetail,
    QuizSubmissionRequest,
)


class MockRetrievalAgent:
    """Mock Retrieval Agent returning realistic search chunk results."""

    def search(self, document_id: str, query: str, top_k: int = 2) -> list[dict]:
        return [
            {
                "page_number": 4,
                "chunk_index": 1,
                "source": "ir_lecture_4.pdf",
                "text": f"Lecture explanation for concept: {query}. Inverted indexes map terms to postings lists.",
                "distance": 0.12,
            }
        ]


class RecommendationAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed a test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_101",
                original_filename="ir_lecture_4.pdf",
                stored_filename="ir_lecture_4.stored.pdf",
                page_count=10,
                pages_with_text=10,
                chunk_count=20,
                file_size_bytes=5000,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        self.mock_retrieval = MockRetrievalAgent()
        self.agent = RecommendationAgent(
            database=self.database,
            retrieval_agent=self.mock_retrieval,  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_analyze_and_recommend_generates_complete_payload(self) -> None:
        questions = [
            QuestionMistakeDetail(
                question_id="q1",
                topic="Inverted Index",
                difficulty="medium",
                cognitive_level="understanding",
                question_text="What is a postings list?",
                selected_answer="A list of document lengths",
                correct_answer="A list of document IDs containing the term",
                is_correct=False,
                explanation="Postings lists record document occurrences.",
            ),
            QuestionMistakeDetail(
                question_id="q2",
                topic="Inverted Index",
                difficulty="easy",
                cognitive_level="recall",
                question_text="What does an inverted index store?",
                selected_answer="Dictionary of terms mapped to postings",
                correct_answer="Dictionary of terms mapped to postings",
                is_correct=True,
                explanation="The dictionary maps vocabulary to document lists.",
            ),
        ]

        request = QuizSubmissionRequest(
            student_id="student_42",
            document_id="doc_101",
            quiz_id="quiz_ir_1",
            quiz_title="IR: Inverted Indexes",
            time_spent_seconds=90,
            questions=questions,
        )

        response = self.agent.analyze_and_recommend(request)

        self.assertTrue(response.recommendation_id.startswith("rec_"))
        self.assertTrue(response.attempt_id.startswith("att_"))
        self.assertEqual(response.student_id, "student_42")
        self.assertEqual(response.document_id, "doc_101")
        self.assertEqual(response.total_questions, 2)
        self.assertEqual(response.overall_score, 1)
        self.assertEqual(response.score_percentage, 50.0)
        self.assertEqual(len(response.knowledge_gaps), 1)
        self.assertEqual(response.knowledge_gaps[0].topic, "Inverted Index")

        # Verify Tutor Handoff package
        self.assertEqual(response.tutor_handoff.student_id, "student_42")
        self.assertIn("Inverted Index", response.tutor_handoff.target_topics)
        self.assertTrue(len(response.tutor_handoff.relevant_lecture_chunks) > 0)
        self.assertEqual(
            response.tutor_handoff.relevant_lecture_chunks[0]["page_number"], 4
        )

        # Verify persistence and retrieval
        retrieved_rec = self.agent.get_recommendation_by_id(response.recommendation_id)
        self.assertIsNotNone(retrieved_rec)
        self.assertEqual(retrieved_rec.recommendation_id, response.recommendation_id)

        student_history = self.agent.get_student_recommendations("student_42")
        self.assertEqual(len(student_history), 1)

        tutor_handoff = self.agent.get_tutor_handoff(response.recommendation_id)
        self.assertIsNotNone(tutor_handoff)
        self.assertEqual(tutor_handoff.document_id, "doc_101")
