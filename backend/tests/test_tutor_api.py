import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.agents.tutor_agent import TutorAgent
from app.api import documents, tutor
from app.database.database import DocumentDatabase
from app.database.models import DocumentRecord
from app.main import app


class MockRetrievalAgent:
    """Mock Retrieval Agent for API test grounding."""

    def search(self, document_id: str, query: str, top_k: int = 3) -> list[dict]:
        return [
            {
                "page_number": 2,
                "chunk_index": 0,
                "source": "ethics_intro.pdf",
                "text": f"Lecture citation for {query}: Algorithmic fairness requires addressing sample selection bias.",
                "distance": 0.05,
            }
        ]


class TutorAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "learnmate.db"
        self.database = DocumentDatabase(self.database_path)
        self.database.initialize()

        # Seed test document
        self.database.create_document(
            DocumentRecord(
                document_id="doc_ethics_01",
                original_filename="ethics_intro.pdf",
                stored_filename="stored_ethics_intro.pdf",
                page_count=6,
                pages_with_text=6,
                chunk_count=12,
                file_size_bytes=4096,
                created_at="2026-01-01T00:00:00+00:00",
            )
        )

        self.mock_retrieval = MockRetrievalAgent()
        self.test_tutor_agent = TutorAgent(
            database=self.database,
            retrieval_agent=self.mock_retrieval,  # type: ignore[arg-type]
        )

        # Patch singletons
        self.database_patch = patch.object(
            documents, "_document_database", self.database
        )
        self.tutor_agent_patch = patch.object(
            tutor, "_tutor_agent", self.test_tutor_agent
        )
        self.database_patch.start()
        self.tutor_agent_patch.start()

        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.tutor_agent_patch.stop()
        self.temporary_directory.cleanup()

    def test_start_tutor_session_endpoint(self) -> None:
        payload = {
            "student_id": "student_test_01",
            "document_id": "doc_ethics_01",
            "mode": "socratic",
            "topic_focus": "Algorithmic Bias",
        }

        response = self.client.post("/tutor/session/start", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["session_id"].startswith("tut_"))
        self.assertEqual(data["student_id"], "student_test_01")
        self.assertEqual(data["topic_focus"], "Algorithmic Bias")
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["role"], "tutor")

    def test_chat_message_endpoint(self) -> None:
        # 1. Start session
        init_res = self.client.post(
            "/tutor/session/start",
            json={
                "student_id": "student_test_01",
                "document_id": "doc_ethics_01",
                "mode": "socratic",
            },
        )
        session_id = init_res.json()["session_id"]

        # 2. Send chat message
        chat_payload = {
            "session_id": session_id,
            "message": "What is selection bias?",
            "mode": "step_by_step",
        }
        chat_res = self.client.post("/tutor/chat", json=chat_payload)
        self.assertEqual(chat_res.status_code, 200)
        chat_data = chat_res.json()
        self.assertEqual(chat_data["session_id"], session_id)
        self.assertEqual(chat_data["mode"], "step_by_step")
        self.assertTrue(len(chat_data["citations"]) > 0)
        self.assertEqual(chat_data["citations"][0]["page_number"], 2)
        self.assertTrue(len(chat_data["suggested_followups"]) > 0)

        # 3. Fetch session history
        hist_res = self.client.get(f"/tutor/session/{session_id}")
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        # 1 init greeting + 1 student msg + 1 tutor msg = 3
        self.assertEqual(len(hist_data["messages"]), 3)

    def test_list_student_sessions_endpoint(self) -> None:
        # Create 2 sessions
        self.client.post(
            "/tutor/session/start",
            json={
                "student_id": "student_multi",
                "document_id": "doc_ethics_01",
                "mode": "socratic",
            },
        )
        self.client.post(
            "/tutor/session/start",
            json={
                "student_id": "student_multi",
                "document_id": "doc_ethics_01",
                "mode": "step_by_step",
            },
        )

        res = self.client.get("/tutor/student/student_multi")
        self.assertEqual(res.status_code, 200)
        sessions = res.json()
        self.assertEqual(len(sessions), 2)

    def test_delete_session_endpoint(self) -> None:
        init_res = self.client.post(
            "/tutor/session/start",
            json={
                "student_id": "student_del",
                "document_id": "doc_ethics_01",
            },
        )
        session_id = init_res.json()["session_id"]

        del_res = self.client.delete(f"/tutor/session/{session_id}")
        self.assertEqual(del_res.status_code, 200)

        get_res = self.client.get(f"/tutor/session/{session_id}")
        self.assertEqual(get_res.status_code, 404)
