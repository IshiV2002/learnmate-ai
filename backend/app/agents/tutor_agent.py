from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.agents.retrieval_agent import RetrievalAgent

from app.agents.retrieval_agent import filter_substantive_chunks
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

    @classmethod
    def resolve_conversational_turn(
        cls,
        student_message: str,
        previous_messages: list[TutorMessageRecord | dict[str, Any]],
        session_topic: str,
    ) -> tuple[str, str, bool]:
        """Resolve conversational student turns into effective retrieval query and topic focus.
        
        Handles:
        1. Affirmative continuation turns ('yes', 'sure', 'please', 'continue', 'sounds good')
        2. Option selections ('relevance', 'indexing', 'the first one', 'both')
        3. Short conversational prompts ('why?', 'how?', 'give me an example')
        4. Direct conceptual queries (e.g., 'What is inverted index?')
        
        Returns:
            (search_query, active_topic, is_followup)
        """
        raw_msg = (student_message or "").strip()
        msg_clean = raw_msg.lower().rstrip("!?.")

        # 1. Inspect previous tutor message to understand conversational context
        last_tutor_text = ""
        for msg in reversed(previous_messages):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if role == "tutor":
                last_tutor_text = content
                break

        last_tutor_lower = last_tutor_text.lower()

        # Check first if the student asked a direct, self-contained conceptual question
        detected_concept = LLMService._extract_concept_from_query(raw_msg)
        if detected_concept:
            return (
                raw_msg,
                detected_concept,
                False,
            )

        # 2. Check for affirmative agreement or continuation
        affirmative_phrases = {
            "yes", "yeah", "yep", "sure", "ok", "okay", "yup", "yes please",
            "please", "go ahead", "let's do it", "lets do it", "sounds good",
            "continue", "tell me more", "explain please", "proceed", "both",
            "all of them", "why not", "definitely", "sure thing", "i would",
            "yes i would", "yes lets do that", "yes please explain", "absolutely",
            "yes definitely", "yes sure", "yes go ahead", "yes please do"
        }
        is_affirmative = (
            msg_clean in affirmative_phrases
            or bool(re.match(r"^(?:yes|sure|okay|ok|yeah|yep|definitely|please|continue|go ahead|sounds good|absolutely)\b", msg_clean))
        )

        effective_fallback_topic = (
            session_topic
            if session_topic and session_topic not in ("Course Foundations", "Course Concepts", "this topic", "")
            else "Information Retrieval"
        )

        # Did the last tutor prompt offer options between relevance and indexing?
        has_relevance_and_indexing_prompt = (
            "relevance" in last_tutor_lower
            and ("index" in last_tutor_lower or "indexing" in last_tutor_lower)
        )

        if is_affirmative:
            if has_relevance_and_indexing_prompt:
                # Student agreed to explore how search systems determine relevance and index documents
                return (
                    "how search systems determine relevance and index large document collections inverted index",
                    "Relevance and Document Indexing",
                    True,
                )
            if "example" in last_tutor_lower or "analogy" in last_tutor_lower:
                return (
                    f"{effective_fallback_topic} concrete practical worked example",
                    effective_fallback_topic,
                    True,
                )
            # General affirmative: continue exploring course principles
            return (
                f"{effective_fallback_topic} core concepts and principles",
                effective_fallback_topic,
                True,
            )

        # 3. Check for topic or option selection from the tutor's prompt
        if has_relevance_and_indexing_prompt:
            if re.search(r"\b(relevance|relevant|scoring|ranking|first|1|option 1|part 1)\b", msg_clean):
                return (
                    "how search systems determine relevance information need",
                    "Information Relevance",
                    True,
                )
            if re.search(r"\b(index|indexing|inverted|second|2|option 2|part 2)\b", msg_clean):
                return (
                    "how search systems index large document collections inverted index postings list",
                    "Document Indexing",
                    True,
                )
            if re.search(r"\b(both|either|all|two)\b", msg_clean):
                return (
                    "how search systems determine relevance and index large document collections inverted index",
                    "Relevance and Document Indexing",
                    True,
                )

        # 4. Check for short follow-up or probing questions
        if msg_clean in {
            "why", "how", "how so", "what do you mean", "why is that",
            "explain more", "tell me why", "can you explain", "give me an example", "what else"
        } or (len(msg_clean.split()) <= 4 and any(w in msg_clean for w in ("why", "how", "what", "more", "example"))):
            return (
                f"{effective_fallback_topic} {raw_msg}",
                effective_fallback_topic,
                True,
            )

        # 5. Standard direct question
        detected_concept = LLMService._extract_concept_from_query(raw_msg)
        active_topic = detected_concept or session_topic or "Course Concepts"
        return (
            raw_msg,
            active_topic,
            False,
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

        # 2. Retrieve Conversation History before saving student turn
        try:
            all_messages = self.database.get_session_messages(request.session_id)
        except DocumentDatabaseError:
            all_messages = []

        # Resolve conversational multi-turn intent (e.g. 'yes', 'relevance', 'indexing', or direct questions)
        search_query, active_topic, is_followup = self.resolve_conversational_turn(
            student_message=request.message,
            previous_messages=all_messages,
            session_topic=session.topic_focus,
        )
        detected_concept = LLMService._extract_concept_from_query(request.message)
        persisted_topic = (
            active_topic
            if (active_topic and session.topic_focus in ("Course Foundations", "Course Concepts", "this topic", ""))
            else session.topic_focus
        )

        # 3. Persist Student Message
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

        # Updated history including current student message for LLM context
        all_messages_with_student = all_messages + [student_msg_record]
        history_for_llm = [
            {"role": m.role, "content": m.content}
            for m in all_messages_with_student[-8:]
        ]

        # 4. RAG Grounding: Query Retrieval Agent for verified lecture excerpts using resolved query
        retrieved_citations: list[dict[str, Any]] = []
        if self.retrieval_agent and session.document_id:
            try:
                # Query candidate pool using the resolved semantic search query
                search_results = self.retrieval_agent.search(
                    document_id=session.document_id,
                    query=search_query,
                    top_k=6,
                )
                # Filter for substantive, meaningful chunks (excludes title slides like Page 4)
                substantive_results = filter_substantive_chunks(search_results, min_words=12, limit=3)

                # Keep only chunks that are tightly relevant to the query.
                if substantive_results:
                    best_dist = substantive_results[0].get("distance", 0.0)
                    is_specific_query = bool(detected_concept) or is_followup
                    max_delta = 0.06 if is_specific_query else 0.10

                    tight_results = [
                        res for res in substantive_results
                        if res.get("distance", 0.0) <= best_dist + max_delta
                    ]
                    if is_specific_query and len(tight_results) > 1:
                        tight_results = tight_results[:3]

                    final_results = tight_results if tight_results else substantive_results[:1]
                else:
                    final_results = []

                for res in final_results:
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

        # 6. Generate a response only when the selected material supplied evidence.
        active_mode = request.mode or session.mode
        if not retrieved_citations:
            reply_text = (
                "I could not find enough supporting text in the selected course "
                "material to answer that reliably. Please rephrase the question or "
                "choose a topic covered by the PDF. I will not invent an unsupported answer."
            )
            followups = [
                "Help me rephrase this question for the course material.",
                "What topics from this document can we review?",
            ]
            check_q = None
        else:
            reply_text, followups, check_q = self.llm_service.generate_tutor_response(
                topic_focus=active_topic,
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
                topic_focus=persisted_topic,
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
