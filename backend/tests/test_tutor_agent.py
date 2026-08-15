import json
import tempfile
import unittest
from pathlib import Path

from app.agents.tutor_agent import TutorAgent, TutorAgentError
from app.database.database import DocumentDatabase
from app.database.models import (
    DocumentRecord,
    RecommendationRecord,
    TutorChatRequest,
    TutorSessionInitRequest,
)


class MockRetrievalAgent:
    """Mock Retrieval Agent returning realistic search chunk results."""

    def search(self, document_id: str, query: str, top_k: int = 3) -> list[dict]:
        return [
            {
                "page_number": 3,
                "chunk_index": 2,
                "source": "lecture_vsm.pdf",
                "text": f"Lecture explanation for query: {query}. Vector space scoring uses cosine similarity with length normalization.",
                "distance": 0.08,
            }
        ]


class TutorAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed a test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_vsm_01",
                original_filename="lecture_vsm.pdf",
                stored_filename="stored_lecture_vsm.pdf",
                page_count=12,
                pages_with_text=12,
                chunk_count=24,
                file_size_bytes=8000,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        self.mock_retrieval = MockRetrievalAgent()
        self.agent = TutorAgent(
            database=self.database,
            retrieval_agent=self.mock_retrieval,  # type: ignore[arg-type]
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_start_standalone_session(self) -> None:
        request = TutorSessionInitRequest(
            student_id="student_99",
            document_id="doc_vsm_01",
            mode="socratic",
            topic_focus="Cosine Similarity",
        )

        response = self.agent.start_session(request)

        self.assertTrue(response.session_id.startswith("tut_"))
        self.assertEqual(response.student_id, "student_99")
        self.assertEqual(response.document_id, "doc_vsm_01")
        self.assertEqual(response.topic_focus, "Cosine Similarity")
        self.assertEqual(response.mode, "socratic")
        self.assertEqual(len(response.messages), 1)
        self.assertEqual(response.messages[0]["role"], "tutor")
        self.assertIn("AI Socratic Tutor", response.messages[0]["content"])

        # Verify DB persistence
        history = self.agent.get_session_history(response.session_id)
        self.assertIsNotNone(history)
        self.assertEqual(len(history.messages), 1)

    def test_start_session_with_recommendation_handoff(self) -> None:
        # Seed a recommendation record
        handoff_data = {
            "recommendation_id": "rec_test_123",
            "student_id": "student_99",
            "document_id": "doc_vsm_01",
            "target_topics": ["Term Weighting", "Length Normalization"],
            "gap_severity": "CRITICAL",
            "pedagogical_instruction": "Guide student to discover sublinear scaling benefits.",
            "suggested_opening_prompt": "Hello student! Let's explore why log-scaling is applied to term frequency.",
            "relevant_lecture_chunks": [
                {
                    "page_number": 5,
                    "chunk_index": 1,
                    "source": "lecture_vsm.pdf",
                    "text_preview": "TF-IDF weighting applies sublinear scaling...",
                }
            ],
        }

        rec = RecommendationRecord(
            recommendation_id="rec_test_123",
            attempt_id="att_test_123",
            student_id="student_99",
            document_id="doc_vsm_01",
            overall_score_percentage=40.0,
            mastery_level="Needs Remediation",
            summary="Review needed on Term Weighting.",
            topic_mastery_json="[]",
            knowledge_gaps_json="[]",
            action_items_json="[]",
            tutor_handoff_json=json.dumps(handoff_data),
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.database.save_recommendation(rec)

        init_request = TutorSessionInitRequest(
            student_id="student_99",
            document_id="doc_vsm_01",
            recommendation_id="rec_test_123",
            mode="socratic",
        )

        session = self.agent.start_session(init_request)
        self.assertEqual(session.topic_focus, "Term Weighting")
        self.assertIn("Let's explore why log-scaling is applied", session.messages[0]["content"])
        self.assertEqual(len(session.messages[0]["citations"]), 1)

    def test_multi_turn_chat_with_grounding_and_modes(self) -> None:
        init_req = TutorSessionInitRequest(
            student_id="student_99",
            document_id="doc_vsm_01",
            mode="socratic",
            topic_focus="Vector Space Scoring",
        )
        session = self.agent.start_session(init_req)

        # First chat turn (Socratic)
        chat_req1 = TutorChatRequest(
            session_id=session.session_id,
            message="Why do we normalize document vectors?",
        )
        resp1 = self.agent.respond(chat_req1)

        self.assertEqual(resp1.session_id, session.session_id)
        self.assertEqual(resp1.mode, "socratic")
        self.assertTrue(len(resp1.citations) > 0)
        self.assertEqual(resp1.citations[0]["page_number"], 3)
        self.assertTrue(len(resp1.suggested_followups) > 0)
        self.assertIsNotNone(resp1.concept_check_question)

        # Second chat turn switching to Step-by-Step mode
        chat_req2 = TutorChatRequest(
            session_id=session.session_id,
            message="Please show me the steps to compute cosine similarity.",
            mode="step_by_step",
        )
        resp2 = self.agent.respond(chat_req2)

        self.assertEqual(resp2.mode, "step_by_step")
        self.assertIn("1.", resp2.reply)

        # Verify complete history in DB
        history = self.agent.get_session_history(session.session_id)
        self.assertIsNotNone(history)
        # Initial greeting + 2 student turns + 2 tutor turns = 5 messages
        self.assertEqual(len(history.messages), 5)
        self.assertEqual(history.messages[1]["role"], "student")
        self.assertEqual(history.messages[2]["role"], "tutor")
        self.assertEqual(history.messages[3]["role"], "student")
        self.assertEqual(history.messages[4]["role"], "tutor")

    def test_list_and_delete_sessions(self) -> None:
        init_req = TutorSessionInitRequest(
            student_id="student_42",
            document_id="doc_vsm_01",
            mode="concept_check",
            topic_focus="Inverted Index",
        )
        session = self.agent.start_session(init_req)

        student_sessions = self.agent.list_student_sessions("student_42")
        self.assertEqual(len(student_sessions), 1)
        self.assertEqual(student_sessions[0].session_id, session.session_id)

        deleted = self.agent.delete_session(session.session_id)
        self.assertTrue(deleted)

        self.assertIsNone(self.agent.get_session_history(session.session_id))
        self.assertEqual(len(self.agent.list_student_sessions("student_42")), 0)

    def test_invalid_session_or_document_raises_error(self) -> None:
        with self.assertRaises(TutorAgentError):
            self.agent.start_session(
                TutorSessionInitRequest(
                    student_id="student_1",
                    document_id="non_existent_doc",
                )
            )

        with self.assertRaises(TutorAgentError):
            self.agent.respond(
                TutorChatRequest(
                    session_id="non_existent_session",
                    message="Hello!",
                )
            )
