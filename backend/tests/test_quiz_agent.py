import json
import tempfile
import unittest
from pathlib import Path

from app.agents.quiz_agent import QuizAgent, QuizAgentError
from app.agents.recommendation_agent import RecommendationAgent
from app.database.database import DocumentDatabase
from app.database.models import (
    DocumentRecord,
    QuizEvaluationRequest,
    QuizGenerationRequest,
    StudentAnswerItem,
)


class MockRetrievalAgent:
    """Mock Retrieval Agent returning realistic search chunk results."""

    def search(self, document_id: str, query: str, top_k: int = 4) -> list[dict]:
        return [
            {
                "page_number": 2,
                "chunk_index": 0,
                "source": "ir_lecture_1.pdf",
                "text": "An inverted index is a database index storing a mapping from words to their locations in a document.",
                "distance": 0.08,
            },
            {
                "page_number": 3,
                "chunk_index": 1,
                "source": "ir_lecture_1.pdf",
                "text": "TF-IDF weighting calculates the product of Term Frequency and Inverse Document Frequency to assess term importance.",
                "distance": 0.12,
            },
        ]


class QuizAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate_test.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_ir_test_01",
                original_filename="ir_lecture_1.pdf",
                stored_filename="ir_lecture_1.stored.pdf",
                page_count=5,
                pages_with_text=5,
                chunk_count=10,
                file_size_bytes=4096,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        self.mock_retrieval = MockRetrievalAgent()
        self.agent = QuizAgent(
            database=self.database,
            retrieval_agent=self.mock_retrieval,  # type: ignore[arg-type]
        )
        self.rec_agent = RecommendationAgent(
            database=self.database,
            retrieval_agent=self.mock_retrieval,  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_generate_quiz_persists_and_returns_record(self) -> None:
        request = QuizGenerationRequest(
            document_id="doc_ir_test_01",
            topic="Inverted Index",
            num_questions=3,
            difficulty="mixed",
            question_types=["mcq", "true_false"],
        )

        quiz = self.agent.generate_quiz(request)

        self.assertTrue(quiz.quiz_id.startswith("quiz_"))
        self.assertEqual(quiz.document_id, "doc_ir_test_01")
        self.assertEqual(quiz.total_questions, 3)
        self.assertIn("Inverted Index", quiz.title)

        # Check database persistence
        retrieved_quiz = self.database.get_quiz(quiz.quiz_id)
        self.assertIsNotNone(retrieved_quiz)
        self.assertEqual(retrieved_quiz.quiz_id, quiz.quiz_id)

        questions = json.loads(retrieved_quiz.questions_json)
        self.assertEqual(len(questions), 3)
        self.assertEqual(questions[0]["question_id"], "q1")
        self.assertTrue(len(questions[0]["question_text"]) > 0)
        self.assertTrue(len(questions[0]["correct_answer"]) > 0)

    def test_evaluate_quiz_computes_score_and_saves_attempt(self) -> None:
        # 1. Generate quiz first
        gen_req = QuizGenerationRequest(
            document_id="doc_ir_test_01",
            topic="TF-IDF",
            num_questions=2,
            difficulty="easy",
            question_types=["mcq"],
        )
        quiz = self.agent.generate_quiz(gen_req)
        questions_list = json.loads(quiz.questions_json)
        q1 = questions_list[0]
        q2 = questions_list[1]

        # 2. Submit 1 correct and 1 incorrect answer
        submission = QuizEvaluationRequest(
            student_id="student_sam",
            time_spent_seconds=45,
            answers=[
                StudentAnswerItem(
                    question_id=q1["question_id"],
                    answer_text=q1["correct_answer"],  # Correct
                ),
                StudentAnswerItem(
                    question_id=q2["question_id"],
                    answer_text="Completely arbitrary wrong answer",  # Incorrect
                ),
            ],
        )

        eval_resp = self.agent.evaluate_quiz(quiz.quiz_id, submission)

        self.assertEqual(eval_resp.quiz_id, quiz.quiz_id)
        self.assertEqual(eval_resp.student_id, "student_sam")
        self.assertEqual(eval_resp.total_questions, 2)
        self.assertEqual(eval_resp.score, 1.0)
        self.assertEqual(eval_resp.score_percentage, 50.0)
        self.assertTrue(eval_resp.attempt_id.startswith("att_"))

        # Verify question-level feedback
        self.assertTrue(eval_resp.results[0].is_correct)
        self.assertFalse(eval_resp.results[1].is_correct)

        # Verify that QuizAttemptRecord was saved in SQLite
        attempt_record = self.database.get_quiz_attempt(eval_resp.attempt_id)
        self.assertIsNotNone(attempt_record)
        self.assertEqual(attempt_record.student_id, "student_sam")
        self.assertEqual(attempt_record.score, 1)

    def test_evaluate_and_recommend_bridges_to_recommendation_agent(self) -> None:
        gen_req = QuizGenerationRequest(
            document_id="doc_ir_test_01",
            topic="Term Weighting",
            num_questions=2,
            difficulty="medium",
            question_types=["mcq"],
        )
        quiz = self.agent.generate_quiz(gen_req)
        questions_list = json.loads(quiz.questions_json)

        # Submit answers with a gap
        submission = QuizEvaluationRequest(
            student_id="student_alex",
            time_spent_seconds=60,
            answers=[
                StudentAnswerItem(
                    question_id=questions_list[0]["question_id"],
                    answer_text="Wrong answer on term weighting",
                ),
                StudentAnswerItem(
                    question_id=questions_list[1]["question_id"],
                    answer_text=questions_list[1]["correct_answer"],
                ),
            ],
        )

        response = self.agent.evaluate_and_recommend(
            quiz_id=quiz.quiz_id,
            submission=submission,
            recommendation_agent=self.rec_agent,
        )

        self.assertIsNotNone(response.recommendation)
        self.assertEqual(response.recommendation.student_id, "student_alex")
        self.assertEqual(response.recommendation.score_percentage, 50.0)
        self.assertTrue(len(response.recommendation.knowledge_gaps) > 0)
        self.assertIsNotNone(response.recommendation.tutor_handoff)

    def test_invalid_document_raises_quiz_agent_error(self) -> None:
        req = QuizGenerationRequest(
            document_id="non_existent_doc",
            num_questions=3,
        )
        with self.assertRaises(QuizAgentError):
            self.agent.generate_quiz(req)
