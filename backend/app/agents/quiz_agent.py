from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.agents.recommendation_agent import RecommendationAgent
    from app.agents.retrieval_agent import RetrievalAgent

from app.database.database import DocumentDatabase
from app.database.models import (
    QuestionEvaluationResult,
    QuestionMistakeDetail,
    QuizAttemptRecord,
    QuizEvaluationRequest,
    QuizEvaluationResponse,
    QuizGenerationRequest,
    QuizQuestionItem,
    QuizRecord,
    QuizSubmissionRequest,
    RecommendationResponse,
)
from app.services.llm_service import LLMService


class QuizAgentError(Exception):
    """Raised when quiz synthesis, retrieval, or answer evaluation fails."""


class QuizAgent:
    """Intelligent Quiz Agent for LearnMate AI.
    
    Generates formative assessments grounded in retrieved lecture context,
    evaluates student responses, provides pedagogical feedback, and packages
    results for seamless gap analysis by the Recommendation Agent.
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

    def generate_quiz(self, request: QuizGenerationRequest) -> QuizRecord:
        """Synthesize a new quiz from indexed lecture document context."""
        doc = self.database.get_document(request.document_id)
        if doc is None:
            raise QuizAgentError(
                f"Document with ID '{request.document_id}' not found in the system."
            )

        # 1. Retrieve relevant lecture chunks
        context_chunks: list[dict[str, Any]] = []
        if self.retrieval_agent:
            query = request.topic or "Core concepts, definitions, algorithms, and key principles"
            try:
                search_results = self.retrieval_agent.search(
                    document_id=request.document_id,
                    query=query,
                    top_k=min(8, max(4, request.num_questions)),
                )
                context_chunks = [
                    {
                        "text": res["text"],
                        "page_number": res["page_number"],
                        "chunk_index": res["chunk_index"],
                        "source": res["source"],
                    }
                    for res in search_results
                ]
            except Exception:
                context_chunks = []

        # If vector search returned no chunks (or mock offline), create fallback context reference
        if not context_chunks:
            context_chunks = [
                {
                    "text": f"Lecture document: {doc.original_filename}. Subject area: {request.topic or 'Fundamental Principles'}.",
                    "page_number": 1,
                    "chunk_index": 0,
                    "source": doc.original_filename,
                }
            ]

        # 2. Synthesize questions via LLM Service (with pedagogical fallback)
        try:
            raw_questions = self.llm_service.generate_quiz_questions(
                context_chunks=context_chunks,
                topic=request.topic,
                num_questions=request.num_questions,
                difficulty=request.difficulty,
                question_types=request.question_types,
            )
        except Exception as error:
            raise QuizAgentError(
                f"Failed to generate questions from lecture context: {error}"
            ) from error

        # 3. Validate and sanitize questions through Pydantic
        validated_questions: list[QuizQuestionItem] = []
        for idx, q_dict in enumerate(raw_questions):
            q_id = q_dict.get("question_id") or f"q{idx + 1}"
            validated_questions.append(
                QuizQuestionItem(
                    question_id=q_id,
                    topic=q_dict.get("topic") or request.topic or "Core Concept",
                    difficulty=q_dict.get("difficulty") or "medium",
                    cognitive_level=q_dict.get("cognitive_level") or "understanding",
                    question_type=q_dict.get("question_type") or "mcq",
                    question_text=q_dict.get("question_text") or "Assessment Question",
                    options=q_dict.get("options") or [],
                    correct_answer=q_dict.get("correct_answer") or "",
                    explanation=q_dict.get("explanation") or "",
                    rubric=q_dict.get("rubric") or "",
                    source_page=q_dict.get("source_page"),
                    source_chunk_index=q_dict.get("source_chunk_index"),
                )
            )

        if not validated_questions:
            raise QuizAgentError("No valid questions could be synthesized.")

        # 4. Determine Quiz Title and Metadata
        title = request.title
        if not title:
            base_name = doc.original_filename.replace(".pdf", "")
            if request.topic:
                title = f"{base_name}: {request.topic}"
            else:
                title = f"{base_name} Quiz"

        quiz_id = f"quiz_{uuid.uuid4().hex[:12]}"
        now_timestamp = datetime.now(timezone.utc).isoformat()

        quiz_record = QuizRecord(
            quiz_id=quiz_id,
            document_id=request.document_id,
            title=title,
            topic=request.topic or "Comprehensive",
            total_questions=len(validated_questions),
            difficulty=request.difficulty,
            questions_json=json.dumps([q.model_dump() for q in validated_questions]),
            created_at=now_timestamp,
        )

        # 5. Persist to SQLite
        self.database.save_quiz(quiz_record)
        return quiz_record

    def get_quiz(self, quiz_id: str) -> QuizRecord | None:
        """Fetch a persisted quiz by its unique ID."""
        return self.database.get_quiz(quiz_id)

    def list_document_quizzes(self, document_id: str) -> list[QuizRecord]:
        """List all quizzes created for a given lecture document."""
        return self.database.list_document_quizzes(document_id)

    def list_all_quizzes(self) -> list[QuizRecord]:
        """List all generated quizzes in the platform."""
        return self.database.list_all_quizzes()

    def evaluate_quiz(
        self,
        quiz_id: str,
        submission: QuizEvaluationRequest,
    ) -> QuizEvaluationResponse:
        """Grade student answers, generate feedback, and record the attempt."""
        quiz = self.database.get_quiz(quiz_id)
        if quiz is None:
            raise QuizAgentError(f"Quiz with ID '{quiz_id}' not found.")

        try:
            questions_data = json.loads(quiz.questions_json)
            questions = [QuizQuestionItem(**q) for q in questions_data]
        except Exception as error:
            raise QuizAgentError("Failed to parse quiz questions from database.") from error

        # Map student answers by question_id
        student_answers_map = {
            ans.question_id: ans.answer_text.strip() for ans in submission.answers
        }

        eval_results: list[QuestionEvaluationResult] = []
        mistake_details: list[QuestionMistakeDetail] = []
        total_awarded_score: float = 0.0

        for q in questions:
            user_ans = student_answers_map.get(q.question_id, "")
            is_correct = False
            awarded_score = 0.0
            feedback = ""

            if q.question_type in ("mcq", "true_false"):
                # Exact or normalized match for MCQs
                norm_user = user_ans.strip().lower()
                norm_correct = q.correct_answer.strip().lower()

                # Check direct match or letter prefix match (e.g. "A" vs "A. ...")
                if norm_user == norm_correct or (
                    len(norm_user) == 1 and norm_correct.startswith(norm_user)
                ):
                    is_correct = True
                    awarded_score = 1.0
                    feedback = "Correct! Well done."
                else:
                    is_correct = False
                    awarded_score = 0.0
                    feedback = f"Incorrect. Correct answer: {q.correct_answer}. {q.explanation}"
            else:
                # Open-ended / Conceptual question evaluation
                is_correct, score_frac, feedback = self.llm_service.evaluate_conceptual_answer(
                    question_text=q.question_text,
                    reference_answer=q.correct_answer,
                    student_answer=user_ans,
                    rubric=q.rubric,
                )
                awarded_score = round(score_frac, 2)

            total_awarded_score += awarded_score

            eval_results.append(
                QuestionEvaluationResult(
                    question_id=q.question_id,
                    topic=q.topic,
                    difficulty=q.difficulty,
                    cognitive_level=q.cognitive_level,
                    question_type=q.question_type,
                    question_text=q.question_text,
                    student_answer=user_ans if user_ans else "(No Answer)",
                    correct_answer=q.correct_answer,
                    is_correct=is_correct,
                    score=awarded_score,
                    max_score=1.0,
                    explanation=q.explanation,
                    feedback=feedback,
                    source_page=q.source_page,
                )
            )

            # Build standardized QuestionMistakeDetail for Recommendation Agent
            mistake_details.append(
                QuestionMistakeDetail(
                    question_id=q.question_id,
                    topic=q.topic,
                    difficulty=q.difficulty,  # type: ignore[arg-type]
                    cognitive_level=q.cognitive_level,  # type: ignore[arg-type]
                    question_text=q.question_text,
                    selected_answer=user_ans if user_ans else "(No Answer)",
                    correct_answer=q.correct_answer,
                    is_correct=is_correct,
                    explanation=q.explanation or feedback,
                )
            )

        attempt_id = f"att_{uuid.uuid4().hex[:12]}"
        now_timestamp = datetime.now(timezone.utc).isoformat()
        total_questions = len(questions)
        score_percentage = round((total_awarded_score / max(1, total_questions)) * 100.0, 1)

        # Build RecommendationAgent-compatible payload
        recommendation_payload = QuizSubmissionRequest(
            student_id=submission.student_id,
            document_id=quiz.document_id,
            quiz_id=quiz.quiz_id,
            quiz_title=quiz.title,
            time_spent_seconds=submission.time_spent_seconds,
            questions=mistake_details,
        )

        # Persist QuizAttemptRecord to SQLite
        attempt_record = QuizAttemptRecord(
            attempt_id=attempt_id,
            student_id=submission.student_id,
            document_id=quiz.document_id,
            quiz_id=quiz.quiz_id,
            quiz_title=quiz.title,
            total_questions=total_questions,
            score=int(round(total_awarded_score)),
            time_spent_seconds=submission.time_spent_seconds,
            submission_data_json=json.dumps([m.model_dump() for m in mistake_details]),
            created_at=now_timestamp,
        )
        self.database.save_quiz_attempt(attempt_record)

        return QuizEvaluationResponse(
            quiz_id=quiz.quiz_id,
            attempt_id=attempt_id,
            student_id=submission.student_id,
            document_id=quiz.document_id,
            quiz_title=quiz.title,
            total_questions=total_questions,
            score=total_awarded_score,
            max_possible_score=float(total_questions),
            score_percentage=score_percentage,
            time_spent_seconds=submission.time_spent_seconds,
            created_at=now_timestamp,
            results=eval_results,
            submission_payload=recommendation_payload,
            recommendation=None,
        )

    def evaluate_and_recommend(
        self,
        quiz_id: str,
        submission: QuizEvaluationRequest,
        recommendation_agent: RecommendationAgent,
    ) -> QuizEvaluationResponse:
        """Evaluate quiz answers and immediately run Recommendation Agent analysis."""
        eval_response = self.evaluate_quiz(quiz_id=quiz_id, submission=submission)
        try:
            rec_response = recommendation_agent.analyze_and_recommend(
                eval_response.submission_payload
            )
            eval_response.recommendation = rec_response
        except Exception:
            # If recommendation agent analysis fails, we still return the valid quiz evaluation
            pass

        return eval_response
