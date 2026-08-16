from threading import Lock
from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.agents.recommendation_agent import (
    RecommendationAgent,
    RecommendationAgentError,
)
from app.api.documents import get_document_database, get_retrieval_agent
from app.database.database import DocumentDatabaseError
from app.database.models import (
    QuizSubmissionRequest,
    RecommendationResponse,
    TutorHandoffPackage,
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])

_recommendation_agent: RecommendationAgent | None = None
_recommendation_agent_lock = Lock()


def get_recommendation_agent() -> RecommendationAgent:
    """Create one reusable Recommendation Agent instance when first needed."""
    global _recommendation_agent

    if _recommendation_agent is None:
        with _recommendation_agent_lock:
            if _recommendation_agent is None:
                try:
                    db = get_document_database()
                    retrieval_agent = None
                    try:
                        retrieval_agent = get_retrieval_agent()
                    except Exception:
                        pass

                    _recommendation_agent = RecommendationAgent(
                        database=db,
                        retrieval_agent=retrieval_agent,
                    )
                except Exception as error:
                    raise RecommendationAgentError(
                        "The Recommendation Agent could not be initialized."
                    ) from error

    return _recommendation_agent


@router.post(
    "/analyze",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze Quiz Results & Generate Recommendations",
)
async def analyze_quiz_submission(
    submission: QuizSubmissionRequest,
) -> RecommendationResponse:
    """Ingest quiz submission details, perform gap analysis, and generate explainable study recommendations."""
    db = get_document_database()

    # Validate that the associated document exists in the system
    try:
        doc = await run_in_threadpool(db.get_document, submission.document_id)
    except DocumentDatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify associated document metadata.",
        ) from error

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{submission.document_id}' not found.",
        )

    try:
        agent = get_recommendation_agent()
        response = await run_in_threadpool(agent.analyze_and_recommend, submission)
        return response
    except RecommendationAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Get Recommendation Details",
)
async def get_recommendation(
    recommendation_id: str,
) -> RecommendationResponse:
    """Retrieve full explainable recommendation analysis by recommendation ID."""
    try:
        agent = get_recommendation_agent()
        recommendation = await run_in_threadpool(
            agent.get_recommendation_by_id, recommendation_id
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve recommendation details.",
        ) from error

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID '{recommendation_id}' not found.",
        )

    return recommendation


@router.get(
    "/attempt/{attempt_id}",
    response_model=RecommendationResponse,
    summary="Get Recommendation for a Quiz Attempt",
)
async def get_recommendation_by_attempt(
    attempt_id: str,
) -> RecommendationResponse:
    """Retrieve recommendations linked directly to a specific quiz attempt ID."""
    try:
        agent = get_recommendation_agent()
        recommendation = await run_in_threadpool(
            agent.get_recommendation_by_attempt, attempt_id
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve attempt recommendations.",
        ) from error

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No recommendations found for quiz attempt '{attempt_id}'.",
        )

    return recommendation


@router.get(
    "/student/{student_id}",
    response_model=list[RecommendationResponse],
    summary="List Student Recommendations",
)
async def list_student_recommendations(
    student_id: str,
) -> list[RecommendationResponse]:
    """Retrieve historical recommendations generated for a student."""
    try:
        agent = get_recommendation_agent()
        recommendations = await run_in_threadpool(
            agent.get_student_recommendations, student_id
        )
        return recommendations
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve student recommendations.",
        ) from error


@router.get(
    "/{recommendation_id}/tutor-handoff",
    response_model=TutorHandoffPackage,
    summary="Get Tutor Agent Handoff Package",
)
async def get_tutor_handoff(
    recommendation_id: str,
) -> TutorHandoffPackage:
    """Retrieve the synthesized Socratic prompt, pedagogical guidance, and cited lecture chunks for the Tutor Agent."""
    try:
        agent = get_recommendation_agent()
        handoff = await run_in_threadpool(
            agent.get_tutor_handoff, recommendation_id
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate tutor handoff package.",
        ) from error

    if handoff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with ID '{recommendation_id}' not found.",
        )

    return handoff
