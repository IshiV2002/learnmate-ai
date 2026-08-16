from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.agents.retrieval_agent import RetrievalAgent

from app.database.database import DocumentDatabase, DocumentDatabaseError
from app.database.models import (
    TutorChatRequest,
    TutorChatResponse,
    TutorHandoffPackage,
    TutorMessageRecord,
    TutorSessionInitRequest,
    TutorSessionRecord,
    TutorSessionResponse,
)
from app.services.llm_service import LLMService


class TutorAgentError(Exception):
    """Raised when tutoring session initialization, dialogue generation, or retrieval fails."""


class TutorAgent:
    """Intelligent Conversational AI Tutor for LearnMate AI.

    Provides step-by-step conceptual explanations and Socratic dialogue,
    grounded in lecture document excerpts retrieved via the Retrieval Agent,
    and consumes remedial handoffs from the Recommendation Agent.
    """

    def __init__(
        self,
        database: DocumentDatabase | None = None,
        retrieval_agent: RetrievalAgent | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.database = database or DocumentDatabase()
        self.retrieval_agent = retrieval_agent
        self.llm_service = llm_service or LLMService()

    def start_session(
        self,
        request: TutorSessionInitRequest,
    ) -> TutorSessionResponse:
        """Initialize a new AI tutoring session (standalone or from recommendation handoff)."""
        session_id = f"tut_{uuid.uuid4().hex[:12]}"
        now_timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Verify associated document
        try:
            doc = self.database.get_document(request.document_id)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not access document records.") from error

        if doc is None:
            raise TutorAgentError(f"Document with ID '{request.document_id}' not found.")

        topic_focus = request.topic_focus or "Course Foundations"
        initial_greeting = ""
        initial_citations: list[dict[str, Any]] = []

        # 2. Check if initialized from a Recommendation Agent handoff
        if request.recommendation_id:
            try:
                rec_record = self.database.get_recommendation(request.recommendation_id)
                if rec_record:
                    handoff_dict = json.loads(rec_record.tutor_handoff_json)
                    handoff = TutorHandoffPackage(**handoff_dict)
                    if handoff.target_topics:
                        topic_focus = handoff.target_topics[0]
                    initial_greeting = handoff.suggested_opening_prompt
                    initial_citations = handoff.relevant_lecture_chunks
            except Exception:
                # If handoff parsing encounters issues, gracefully fall back
                pass

        if not initial_greeting:
            doc_name = doc.original_filename
            if request.mode == "socratic":
                initial_greeting = (
                    f"Hello! I am your AI Socratic Tutor for **{doc_name}**.\n\n"
                    f"Rather than just giving you the answers, I'll guide you step-by-step to build a deep, "
                    f"lasting understanding. What topic or concept would you like to explore today?"
                )
            elif request.mode == "step_by_step":
                initial_greeting = (
                    f"Welcome! I am your AI Study Coach for **{doc_name}**.\n\n"
                    f"I will break down complex concepts into simple, structured steps with clear examples. "
                    f"Which concept should we walk through?"
                )
            else:
                initial_greeting = (
                    f"Hello! Let's test and reinforce your mastery of **{doc_name}**.\n\n"
                    f"Ask me about any topic, and I'll explain the key takeaway and challenge you with a quick concept check!"
                )

        # 3. Create Session Record
        session_record = TutorSessionRecord(
            session_id=session_id,
            student_id=request.student_id,
            document_id=request.document_id,
            recommendation_id=request.recommendation_id,
            topic_focus=topic_focus,
            mode=request.mode,
            created_at=now_timestamp,
            updated_at=now_timestamp,
        )

        try:
            self.database.create_tutor_session(session_record)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Failed to persist new tutor session.") from error

        # 4. Save Initial Tutor Message
        first_message_id = f"msg_{uuid.uuid4().hex[:12]}"
        tutor_message = TutorMessageRecord(
            message_id=first_message_id,
            session_id=session_id,
            role="tutor",
            content=initial_greeting,
            citations_json=json.dumps(initial_citations),
            created_at=now_timestamp,
        )

        try:
            self.database.save_tutor_message(tutor_message)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Failed to save initial tutor greeting.") from error

        return TutorSessionResponse(
            session_id=session_id,
            student_id=request.student_id,
            document_id=request.document_id,
            recommendation_id=request.recommendation_id,
            topic_focus=topic_focus,
            mode=request.mode,
            messages=[tutor_message.to_dict()],
            created_at=now_timestamp,
            updated_at=now_timestamp,
        )

    def respond(self, request: TutorChatRequest) -> TutorChatResponse:
        """Process student message, perform semantic retrieval grounding, and generate tutor response."""
        now_timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Fetch Session
        try:
            session = self.database.get_tutor_session(request.session_id)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not access session database.") from error

        if session is None:
            raise TutorAgentError(f"Tutor session '{request.session_id}' not found.")

        # 2. Persist Student Message
        student_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        student_msg_record = TutorMessageRecord(
            message_id=student_msg_id,
            session_id=request.session_id,
            role="student",
            content=request.message,
            citations_json="[]",
            created_at=now_timestamp,
        )
        try:
            self.database.save_tutor_message(student_msg_record)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not save student message.") from error

        # 3. Retrieve Conversation History
        try:
            all_messages = self.database.get_session_messages(request.session_id)
        except DocumentDatabaseError:
            all_messages = [student_msg_record]

        history_for_llm = [
            {"role": m.role, "content": m.content}
            for m in all_messages[-8:]
        ]

        # 4. RAG Grounding: Query Retrieval Agent for verified lecture excerpts
        retrieved_citations: list[dict[str, Any]] = []
        if self.retrieval_agent and session.document_id:
            try:
                search_results = self.retrieval_agent.search(
                    document_id=session.document_id,
                    query=request.message,
                    top_k=3,
                )
                for res in search_results:
                    retrieved_citations.append(
                        {
                            "page_number": res.get("page_number", 1),
                            "chunk_index": res.get("chunk_index", 0),
                            "source": res.get("source", "Lecture PDF"),
                            "text": res.get("text", ""),
                            "distance": res.get("distance", 0.0),
                        }
                    )
            except Exception:
                # Retrieval is best-effort grounding
                retrieved_citations = []

        # 5. Extract Pedagogical Directive if linked to recommendation
        pedagogical_directive = None
        if session.recommendation_id:
            try:
                rec_record = self.database.get_recommendation(session.recommendation_id)
                if rec_record:
                    handoff = json.loads(rec_record.tutor_handoff_json)
                    pedagogical_directive = handoff.get("pedagogical_instruction")
            except Exception:
                pass

        # 6. Generate Response via LLM or deterministic pedagogical engine
        active_mode = request.mode or session.mode
        reply_text, followups, check_q = self.llm_service.generate_tutor_response(
            topic_focus=session.topic_focus,
            mode=active_mode,
            pedagogical_directive=pedagogical_directive,
            lecture_chunks=retrieved_citations,
            history=history_for_llm,
            student_message=request.message,
        )

        # 7. Persist Tutor Message & Update Session
        tutor_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        tutor_msg_record = TutorMessageRecord(
            message_id=tutor_msg_id,
            session_id=request.session_id,
            role="tutor",
            content=reply_text,
            citations_json=json.dumps(retrieved_citations),
            created_at=now_timestamp,
        )

        try:
            self.database.save_tutor_message(tutor_msg_record)
            self.database.update_tutor_session_activity(
                session_id=request.session_id,
                updated_at=now_timestamp,
                mode=active_mode,
            )
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not persist tutor response turn.") from error

        return TutorChatResponse(
            session_id=request.session_id,
            message_id=tutor_msg_id,
            reply=reply_text,
            mode=active_mode,
            citations=retrieved_citations,
            suggested_followups=followups,
            concept_check_question=check_q,
            created_at=now_timestamp,
        )

    def get_session_history(self, session_id: str) -> TutorSessionResponse | None:
        """Fetch full conversation thread for a given session."""
        try:
            session = self.database.get_tutor_session(session_id)
            if not session:
                return None
            messages = self.database.get_session_messages(session_id)
            return TutorSessionResponse(
                session_id=session.session_id,
                student_id=session.student_id,
                document_id=session.document_id,
                recommendation_id=session.recommendation_id,
                topic_focus=session.topic_focus,
                mode=session.mode,
                messages=[m.to_dict() for m in messages],
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not retrieve session history.") from error

    def list_student_sessions(self, student_id: str) -> list[TutorSessionRecord]:
        """List all historical tutoring sessions for a student."""
        try:
            return self.database.list_student_tutor_sessions(student_id)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not list student tutor sessions.") from error

    def delete_session(self, session_id: str) -> bool:
        """Delete an AI tutor session and its message history."""
        try:
            return self.database.delete_tutor_session(session_id)
        except DocumentDatabaseError as error:
            raise TutorAgentError("Could not delete tutor session.") from error
