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

    def test_tutor_declines_when_course_evidence_is_unavailable(self) -> None:
        agent = TutorAgent(database=self.database, retrieval_agent=None)
        session = agent.start_session(
            TutorSessionInitRequest(
                student_id="student_99",
                document_id="doc_vsm_01",
                topic_focus="Unsupported Topic",
            )
        )

        response = agent.respond(
            TutorChatRequest(
                session_id=session.session_id,
                message="Explain a topic that is not supported by this PDF.",
            )
        )

        self.assertEqual(response.citations, [])
        self.assertIn("could not find enough supporting text", response.reply)
        self.assertIn("will not invent", response.reply)

    def test_tutor_filters_non_substantive_title_citations_and_explains_concept(self) -> None:
        class NoiseFilteringMockRetrieval:
            def search(self, document_id: str, query: str, top_k: int = 3) -> list[dict]:
                return [
                    {
                        "page_number": 4,
                        "chunk_index": 0,
                        "source": "Lecture 01.pdf",
                        "text": "Introduction to Information Retrieval 4",
                        "distance": 0.12,
                    },
                    {
                        "page_number": 5,
                        "chunk_index": 0,
                        "source": "Lecture 01.pdf",
                        "text": (
                            "Information Retrieval • Manning et al, 2008: Information Retrieval (IR) is finding material "
                            "(usually documents) of an unstructured nature (usually text) that satisfies an information need "
                            "from within large collections (usually stored on computers)."
                        ),
                        "distance": 0.18,
                    },
                ]

        agent = TutorAgent(
            database=self.database,
            retrieval_agent=NoiseFilteringMockRetrieval(),  # type: ignore[arg-type]
        )
        session = agent.start_session(
            TutorSessionInitRequest(
                student_id="student_99",
                document_id="doc_vsm_01",
                mode="socratic",
            )
        )

        response = agent.respond(
            TutorChatRequest(
                session_id=session.session_id,
                message="what is information retrieval",
            )
        )

        # 1. Page 4 is a title slide with no substantive explanation, so it MUST be excluded from citations
        cited_pages = [c["page_number"] for c in response.citations]
        self.assertNotIn(4, cited_pages)
        self.assertIn(5, cited_pages)

        # 2. Response must explain the actual concept (Information Retrieval), not generic 'Course Foundations'
        self.assertIn("Information Retrieval", response.reply)
        self.assertNotIn("Course Foundations", response.reply)
        self.assertIn("Key Concepts", response.reply)

    def test_resolve_conversational_turn(self) -> None:
        previous_tutor_prompt = [
            {
                "role": "tutor",
                "content": (
                    "To connect this with your course material, would you like to explore how search "
                    "systems determine relevance, or how they index large document collections?"
                ),
            }
        ]

        # 1. Affirmative answer "yes"
        query, topic, is_followup = TutorAgent.resolve_conversational_turn(
            student_message="yes",
            previous_messages=previous_tutor_prompt,
            session_topic="Information Retrieval",
        )
        self.assertTrue(is_followup)
        self.assertIn("relevance", query)
        self.assertIn("index", query)
        self.assertEqual(topic, "Relevance and Document Indexing")

        # 2. Affirmative answer "sure"
        query, topic, is_followup = TutorAgent.resolve_conversational_turn(
            student_message="sure",
            previous_messages=previous_tutor_prompt,
            session_topic="Information Retrieval",
        )
        self.assertTrue(is_followup)
        self.assertEqual(topic, "Relevance and Document Indexing")

        # 3. Topic option "relevance"
        query, topic, is_followup = TutorAgent.resolve_conversational_turn(
            student_message="relevance",
            previous_messages=previous_tutor_prompt,
            session_topic="Information Retrieval",
        )
        self.assertTrue(is_followup)
        self.assertEqual(topic, "Information Relevance")
        self.assertIn("determine relevance", query)

        # 4. Topic option "indexing"
        query, topic, is_followup = TutorAgent.resolve_conversational_turn(
            student_message="how they index",
            previous_messages=previous_tutor_prompt,
            session_topic="Information Retrieval",
        )
        self.assertTrue(is_followup)
        self.assertEqual(topic, "Document Indexing")
        self.assertIn("inverted index", query)

        # 5. Direct conceptual question
        query, topic, is_followup = TutorAgent.resolve_conversational_turn(
            student_message="What is an inverted index?",
            previous_messages=previous_tutor_prompt,
            session_topic="Information Retrieval",
        )
        self.assertFalse(is_followup)
        self.assertEqual(query, "What is an inverted index?")
        self.assertEqual(topic, "Inverted Index")

    def test_tutor_agent_handles_conversational_affirmation_without_confusion(self) -> None:
        searched_queries = []

        class MultiTurnMockRetrieval:
            def search(self, document_id: str, query: str, top_k: int = 3) -> list[dict]:
                searched_queries.append(query)
                if "relevance" in query and "index" in query:
                    return [
                        {
                            "page_number": 12,
                            "chunk_index": 0,
                            "source": "Lecture 01.pdf",
                            "text": (
                                "Information Need and Relevance: An information need is the topic about which the user desires to know. "
                                "A query is what the user conveys to the computer. A document is relevant if the user perceives that it contains valuable information."
                            ),
                            "distance": 0.05,
                        },
                        {
                            "page_number": 14,
                            "chunk_index": 0,
                            "source": "Lecture 01.pdf",
                            "text": (
                                "Information Relevance: Are the retrieved documents about the target subject? up-to-date? from a trusted source? satisfying user needs?"
                            ),
                            "distance": 0.06,
                        },
                        {
                            "page_number": 37,
                            "chunk_index": 0,
                            "source": "Lecture 01.pdf",
                            "text": (
                                "The inverted index we just built maps dictionary terms to postings lists of DocIDs for fast query evaluation."
                            ),
                            "distance": 0.08,
                        },
                    ]
                return [
                    {
                        "page_number": 5,
                        "chunk_index": 0,
                        "source": "Lecture 01.pdf",
                        "text": (
                            "Information Retrieval is finding material of an unstructured nature that satisfies an information need from within large collections."
                        ),
                        "distance": 0.05,
                    }
                ]

        agent = TutorAgent(
            database=self.database,
            retrieval_agent=MultiTurnMockRetrieval(),  # type: ignore[arg-type]
        )
        session = agent.start_session(
            TutorSessionInitRequest(
                student_id="student_99",
                document_id="doc_vsm_01",
                mode="socratic",
                topic_focus="Information Retrieval",
            )
        )

        # First turn: student asks what IR is
        first_resp = agent.respond(
            TutorChatRequest(
                session_id=session.session_id,
                message="What is information retrieval?",
            )
        )
        self.assertIn("would you like to explore how search systems determine", first_resp.reply)

        # Second turn: student replies with "yes"
        second_resp = agent.respond(
            TutorChatRequest(
                session_id=session.session_id,
                message="yes",
            )
        )

        # Verify search query used by retrieval agent was resolved contextually, not just searching "yes"
        self.assertNotIn("yes", searched_queries[-1].lower().split())
        self.assertIn("relevance", searched_queries[-1].lower())
        self.assertIn("index", searched_queries[-1].lower())

        # Verify tutor response explains relevance and document indexing without confusion
        self.assertIn("relevance", second_resp.reply.lower())
        self.assertIn("index", second_resp.reply.lower())
        self.assertNotIn("conflicting evidence", second_resp.reply.lower())
        self.assertNotIn("compare the surrounding text", " ".join(second_resp.suggested_followups).lower())
        self.assertGreaterEqual(len(second_resp.citations), 2)


