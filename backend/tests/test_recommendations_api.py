import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import documents, recommendations
from app.database.database import DocumentDatabase
from app.database.models import DocumentRecord
from app.main import app


class RecommendationsAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_valid_1",
                original_filename="ai_ethics.pdf",
                stored_filename="ai_ethics.stored.pdf",
                page_count=5,
                pages_with_text=5,
                chunk_count=10,
                file_size_bytes=2048,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        # Create isolated test RecommendationAgent
        self.test_agent = recommendations.RecommendationAgent(
            database=self.database,
            retrieval_agent=None,
        )

        # Patch singletons
        self.database_patch = patch.object(
            documents, "_document_database", self.database
        )
        self.rec_agent_patch = patch.object(
            recommendations, "_recommendation_agent", self.test_agent
        )
        self.database_patch.start()
        self.rec_agent_patch.start()

        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.rec_agent_patch.stop()
        self.temporary_directory.cleanup()

    def test_analyze_quiz_submission_success(self) -> None:
        payload = {
            "student_id": "student_01",
            "document_id": "doc_valid_1",
            "quiz_id": "quiz_ethics_1",
            "quiz_title": "AI Ethics & Fairness",
            "time_spent_seconds": 150,
            "questions": [
                {
                    "question_id": "q1",
                    "topic": "Algorithmic Bias",
                    "difficulty": "medium",
                    "cognitive_level": "understanding",
                    "question_text": "What causes training data bias?",
                    "selected_answer": "Hardware overheating",
                    "correct_answer": "Unrepresentative sampling of populations",
                    "is_correct": False,
                    "explanation": "Biased training sets yield biased models.",
                },
                {
                    "question_id": "q2",
                    "topic": "Algorithmic Bias",
                    "difficulty": "easy",
                    "cognitive_level": "recall",
                    "question_text": "Is bias mitigation possible pre-processing?",
                    "selected_answer": "Yes, via data re-weighting",
                    "correct_answer": "Yes, via data re-weighting",
                    "is_correct": True,
                    "explanation": "Pre-processing re-weights underrepresented groups.",
                },
                {
                    "question_id": "q3",
                    "topic": "Explainability",
                    "difficulty": "hard",
                    "cognitive_level": "application",
                    "question_text": "How does SHAP calculate feature attribution?",
                    "selected_answer": "Shapley values from game theory",
                    "correct_answer": "Shapley values from game theory",
                    "is_correct": True,
                    "explanation": "SHAP computes marginal contributions.",
                },
            ],
        }

        response = self.client.post("/recommendations/analyze", json=payload)
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertEqual(data["student_id"], "student_01")
        self.assertEqual(data["document_id"], "doc_valid_1")
        self.assertEqual(data["total_questions"], 3)
        self.assertEqual(data["overall_score"], 2)
        self.assertAlmostEqual(data["score_percentage"], 66.7, places=1)
        self.assertEqual(len(data["knowledge_gaps"]), 1)
        self.assertEqual(data["knowledge_gaps"][0]["topic"], "Algorithmic Bias")
        self.assertTrue("tutor_handoff" in data)

        rec_id = data["recommendation_id"]

        # Verify GET /recommendations/{id}
        get_response = self.client.get(f"/recommendations/{rec_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["recommendation_id"], rec_id)

        # Verify GET /recommendations/student/{student_id}
        student_response = self.client.get("/recommendations/student/student_01")
        self.assertEqual(student_response.status_code, 200)
        self.assertEqual(len(student_response.json()), 1)

        # Verify GET /recommendations/{id}/tutor-handoff
        handoff_response = self.client.get(f"/recommendations/{rec_id}/tutor-handoff")
        self.assertEqual(handoff_response.status_code, 200)
        handoff_data = handoff_response.json()
        self.assertEqual(handoff_data["student_id"], "student_01")
        self.assertIn("Algorithmic Bias", handoff_data["target_topics"])

    def test_analyze_quiz_submission_nonexistent_document_returns_404(self) -> None:
        payload = {
            "student_id": "student_01",
            "document_id": "nonexistent_doc_id",
            "quiz_id": "quiz_1",
            "quiz_title": "Quiz Title",
            "time_spent_seconds": 60,
            "questions": [
                {
                    "question_id": "q1",
                    "topic": "Topic A",
                    "difficulty": "medium",
                    "cognitive_level": "recall",
                    "question_text": "Sample question?",
                    "selected_answer": "A",
                    "correct_answer": "A",
                    "is_correct": True,
                    "explanation": "",
                }
            ],
        }

        response = self.client.post("/recommendations/analyze", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    def test_analyze_quiz_submission_empty_questions_returns_422(self) -> None:
        payload = {
            "student_id": "student_01",
            "document_id": "doc_valid_1",
            "quiz_id": "quiz_1",
            "quiz_title": "Quiz Title",
            "time_spent_seconds": 60,
            "questions": [],
        }

        response = self.client.post("/recommendations/analyze", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_get_nonexistent_recommendation_returns_404(self) -> None:
        response = self.client.get("/recommendations/rec_does_not_exist")
        self.assertEqual(response.status_code, 404)
