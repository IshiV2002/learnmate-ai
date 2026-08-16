from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.agents.retrieval_agent import RetrievalAgent

from app.database.database import DocumentDatabase
from app.database.models import (
    KnowledgeGap,
    QuizAttemptRecord,
    QuizSubmissionRequest,
    RecommendationRecord,
    RecommendationResponse,
    StudyActionItem,
    TopicMastery,
    TutorHandoffPackage,
)
from app.services.gap_analysis_service import GapAnalysisService
from app.services.llm_service import LLMService
from app.services.tutor_handoff_service import TutorHandoffService


class RecommendationAgentError(Exception):
    """Raised when recommendation generation or analysis fails."""


class RecommendationAgent:
    """Intelligent Recommendation Agent for LearnMate AI.
    
    Analyzes quiz mistake logs, identifies conceptual knowledge gaps,
    generates explainable study recommendations, and prepares targeted
    remedial packages for the Tutor Agent.
    """

    def __init__(
        self,
        database: DocumentDatabase | None = None,
        retrieval_agent: RetrievalAgent | None = None,
        gap_analysis_service: GapAnalysisService | None = None,
        llm_service: LLMService | None = None,
        tutor_handoff_service: TutorHandoffService | None = None,
    ) -> None:
        self.database = database or DocumentDatabase()
        self.retrieval_agent = retrieval_agent
        self.gap_analysis_service = gap_analysis_service or GapAnalysisService()
        self.llm_service = llm_service or LLMService()
        self.tutor_handoff_service = tutor_handoff_service or TutorHandoffService(
            retrieval_agent=self.retrieval_agent,
            llm_service=self.llm_service,
        )

    def analyze_and_recommend(
        self,
        submission: QuizSubmissionRequest,
    ) -> RecommendationResponse:
        """Process quiz results, generate explainable recommendations, and persist to database."""
        attempt_id = f"att_{uuid.uuid4().hex[:12]}"
        recommendation_id = f"rec_{uuid.uuid4().hex[:12]}"
        now_timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # 1. Run Knowledge Gap Analysis
            (
                score_pct,
                mastery_level,
                base_summary,
                topic_masteries,
                knowledge_gaps,
                action_items,
            ) = self.gap_analysis_service.analyze(submission.questions)

            # 2. Generate Pedagogical Summary via LLM (or fallback)
            pedagogical_summary = self.llm_service.generate_pedagogical_summary(
                quiz_title=submission.quiz_title,
                score_percentage=score_pct,
                gaps=knowledge_gaps,
            )

            # 3. Enrich with Lecture Citations & Form Tutor Handoff Package
            enriched_action_items, tutor_package = (
                self.tutor_handoff_service.enrich_citations_and_build_handoff(
                    recommendation_id=recommendation_id,
                    student_id=submission.student_id,
                    document_id=submission.document_id,
                    quiz_title=submission.quiz_title,
                    gaps=knowledge_gaps,
                    action_items=action_items,
                )
            )

            # 4. Persist Quiz Attempt to SQLite
            total_correct = sum(1 for q in submission.questions if q.is_correct)
            quiz_record = QuizAttemptRecord(
                attempt_id=attempt_id,
                student_id=submission.student_id,
                document_id=submission.document_id,
                quiz_id=submission.quiz_id,
                quiz_title=submission.quiz_title,
                total_questions=len(submission.questions),
                score=total_correct,
                time_spent_seconds=submission.time_spent_seconds,
                submission_data_json=json.dumps(
                    [q.model_dump() for q in submission.questions]
                ),
                created_at=now_timestamp,
            )
            self.database.save_quiz_attempt(quiz_record)

            # 5. Persist Recommendation Record to SQLite
            rec_record = RecommendationRecord(
                recommendation_id=recommendation_id,
                attempt_id=attempt_id,
                student_id=submission.student_id,
                document_id=submission.document_id,
                overall_score_percentage=score_pct,
                mastery_level=mastery_level,
                summary=pedagogical_summary,
                topic_mastery_json=json.dumps(
                    [tm.model_dump() for tm in topic_masteries]
                ),
                knowledge_gaps_json=json.dumps(
                    [kg.model_dump() for kg in knowledge_gaps]
                ),
                action_items_json=json.dumps(
                    [ai.model_dump() for ai in enriched_action_items]
                ),
                tutor_handoff_json=json.dumps(tutor_package.model_dump()),
                created_at=now_timestamp,
            )
            self.database.save_recommendation(rec_record)

            # 6. Return Structured API Response
            return RecommendationResponse(
                recommendation_id=recommendation_id,
                attempt_id=attempt_id,
                student_id=submission.student_id,
                document_id=submission.document_id,
                created_at=now_timestamp,
                overall_score=total_correct,
                total_questions=len(submission.questions),
                score_percentage=score_pct,
                mastery_level=mastery_level,
                summary=pedagogical_summary,
                topic_mastery=topic_masteries,
                knowledge_gaps=knowledge_gaps,
                action_items=enriched_action_items,
                tutor_handoff=tutor_package,
            )

        except Exception as error:
            raise RecommendationAgentError(
                f"Failed to generate study recommendations: {error}"
            ) from error

    def get_recommendation_by_id(
        self, recommendation_id: str
    ) -> RecommendationResponse | None:
        """Fetch a persisted recommendation and reconstruct its typed response."""
        record = self.database.get_recommendation(recommendation_id)
        if not record:
            return None
        return self._record_to_response(record)

    def get_recommendation_by_attempt(
        self, attempt_id: str
    ) -> RecommendationResponse | None:
        """Fetch recommendation corresponding to a specific quiz attempt."""
        record = self.database.get_recommendation_by_attempt(attempt_id)
        if not record:
            return None
        return self._record_to_response(record)

    def get_student_recommendations(
        self, student_id: str
    ) -> list[RecommendationResponse]:
        """Fetch all historical recommendations for a student."""
        records = self.database.list_student_recommendations(student_id)
        return [self._record_to_response(r) for r in records]

    def get_tutor_handoff(
        self, recommendation_id: str
    ) -> TutorHandoffPackage | None:
        """Fetch just the Tutor Agent handoff package for an immediate tutoring session."""
        record = self.database.get_recommendation(recommendation_id)
        if not record:
            return None
        try:
            handoff_dict = json.loads(record.tutor_handoff_json)
            return TutorHandoffPackage(**handoff_dict)
        except Exception:
            return None

    def _record_to_response(
        self, record: RecommendationRecord
    ) -> RecommendationResponse:
        """Convert a database row into a structured Pydantic RecommendationResponse."""
        attempt = self.database.get_quiz_attempt(record.attempt_id)
        total_questions = attempt.total_questions if attempt else 0
        overall_score = attempt.score if attempt else 0

        topic_mastery_list = [
            TopicMastery(**item)
            for item in json.loads(record.topic_mastery_json)
        ]
        knowledge_gaps_list = [
            KnowledgeGap(**item)
            for item in json.loads(record.knowledge_gaps_json)
        ]
        action_items_list = [
            StudyActionItem(**item)
            for item in json.loads(record.action_items_json)
        ]
        tutor_handoff = TutorHandoffPackage(
            **json.loads(record.tutor_handoff_json)
        )

        return RecommendationResponse(
            recommendation_id=record.recommendation_id,
            attempt_id=record.attempt_id,
            student_id=record.student_id,
            document_id=record.document_id,
            created_at=record.created_at,
            overall_score=overall_score,
            total_questions=total_questions,
            score_percentage=record.overall_score_percentage,
            mastery_level=record.mastery_level,
            summary=record.summary,
            topic_mastery=topic_mastery_list,
            knowledge_gaps=knowledge_gaps_list,
            action_items=action_items_list,
            tutor_handoff=tutor_handoff,
        )
