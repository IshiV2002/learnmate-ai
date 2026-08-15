import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import documents, quizzes, recommendations
from app.database.database import DocumentDatabase
from app.database.models import DocumentRecord
from app.main import app


class QuizzesAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_api_test_01",
                original_filename="ir_scoring.pdf",
                stored_filename="ir_scoring.stored.pdf",
                page_count=6,
                pages_with_text=6,
                chunk_count=12,
                file_size_bytes=3000,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        self.test_quiz_agent = quizzes.QuizAgent(
            database=self.database,
            retrieval_agent=None,
        )
        self.test_rec_agent = recommendations.RecommendationAgent(
            database=self.database,
            retrieval_agent=None,
        )

        self.database_patch = patch.object(
            documents, "_document_database", self.database
        )
        self.quiz_agent_patch = patch.object(
            quizzes, "_quiz_agent", self.test_quiz_agent
        )
        self.rec_agent_patch = patch.object(
            recommendations, "_recommendation_agent", self.test_rec_agent
        )

        self.database_patch.start()
        self.quiz_agent_patch.start()
        self.rec_agent_patch.start()

        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.quiz_agent_patch.stop()
        self.rec_agent_patch.stop()
        self.temporary_directory.cleanup()

    def test_generate_quiz_endpoint(self) -> None:
        response = self.client.post(
            "/quizzes/generate",
            json={
                "document_id": "doc_api_test_01",
                "topic": "Vector Space Model",
                "num_questions": 3,
                "difficulty": "medium",
                "question_types": ["mcq"],
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["quiz_id"].startswith("quiz_"))
        self.assertEqual(data["document_id"], "doc_api_test_01")
        self.assertEqual(len(data["questions"]), 3)

    def test_get_quiz_hides_answers_by_default(self) -> None:
        # 1. Generate
        gen_res = self.client.post(
            "/quizzes/generate",
            json={
                "document_id": "doc_api_test_01",
                "num_questions": 2,
            },
        )
        quiz_id = gen_res.json()["quiz_id"]

        # 2. Get without solutions
        get_res = self.client.get(f"/quizzes/{quiz_id}")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertNotIn("correct_answer", data["questions"][0])
        self.assertNotIn("explanation", data["questions"][0])

        # 3. Get with solutions
        get_sol_res = self.client.get(f"/quizzes/{quiz_id}?include_solutions=true")
        self.assertEqual(get_sol_res.status_code, 200)
        sol_data = get_sol_res.json()
        self.assertIn("correct_answer", sol_data["questions"][0])
        self.assertIn("explanation", sol_data["questions"][0])

    def test_list_document_quizzes_endpoint(self) -> None:
        self.client.post(
            "/quizzes/generate",
            json={"document_id": "doc_api_test_01", "num_questions": 2},
        )
        res = self.client.get("/quizzes/document/doc_api_test_01")
        self.assertEqual(res.status_code, 200)
        quizzes_list = res.json()
        self.assertEqual(len(quizzes_list), 1)

    def test_evaluate_quiz_endpoint(self) -> None:
        gen_res = self.client.post(
            "/quizzes/generate",
            json={
                "document_id": "doc_api_test_01",
                "num_questions": 2,
            },
        )
        quiz_data = gen_res.json()
        quiz_id = quiz_data["quiz_id"]
        q1 = quiz_data["questions"][0]

        eval_res = self.client.post(
            f"/quizzes/{quiz_id}/evaluate",
            json={
                "student_id": "student_jordan",
                "time_spent_seconds": 30,
                "answers": [
                    {
                        "question_id": q1["question_id"],
                        "answer_text": q1["correct_answer"],
                    }
                ],
            },
        )
        self.assertEqual(eval_res.status_code, 200)
        eval_data = eval_res.json()
        self.assertEqual(eval_data["student_id"], "student_jordan")
        self.assertEqual(eval_data["score"], 1.0)
        self.assertTrue(eval_data["results"][0]["is_correct"])

    def test_evaluate_and_recommend_endpoint(self) -> None:
        gen_res = self.client.post(
            "/quizzes/generate",
            json={
                "document_id": "doc_api_test_01",
                "topic": "Inverted Index",
                "num_questions": 2,
            },
        )
        quiz_data = gen_res.json()
        quiz_id = quiz_data["quiz_id"]
        q1 = quiz_data["questions"][0]

        eval_rec_res = self.client.post(
            f"/quizzes/{quiz_id}/evaluate-and-recommend",
            json={
                "student_id": "student_casey",
                "time_spent_seconds": 40,
                "answers": [
                    {
                        "question_id": q1["question_id"],
                        "answer_text": "Incorrect answer",
                    }
                ],
            },
        )
        self.assertEqual(eval_rec_res.status_code, 200)
        data = eval_rec_res.json()
        self.assertIsNotNone(data["recommendation"])
        self.assertEqual(data["recommendation"]["student_id"], "student_casey")
        self.assertTrue(len(data["recommendation"]["knowledge_gaps"]) > 0)
