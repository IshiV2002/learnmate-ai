from threading import Lock
from typing import Any
from fastapi import APIRouter, HTTPException, Query, status
from starlette.concurrency import run_in_threadpool

from app.agents.quiz_agent import QuizAgent, QuizAgentError
from app.api.documents import get_document_database, get_retrieval_agent
from app.api.recommendations import get_recommendation_agent
from app.database.database import DocumentDatabaseError
from app.database.models import (
    QuizEvaluationRequest,
    QuizEvaluationResponse,
    QuizGenerationRequest,
)

router = APIRouter(prefix="/quizzes", tags=["quizzes"])

_quiz_agent: QuizAgent | None = None
_quiz_agent_lock = Lock()


def get_quiz_agent() -> QuizAgent:
    """Create one reusable Quiz Agent instance when first needed."""
    global _quiz_agent

    if _quiz_agent is None:
        with _quiz_agent_lock:
            if _quiz_agent is None:
                try:
                    db = get_document_database()
                    retrieval_agent = None
                    try:
                        retrieval_agent = get_retrieval_agent()
                    except Exception:
                        pass

                    _quiz_agent = QuizAgent(
                        database=db,
                        retrieval_agent=retrieval_agent,
                    )
                except Exception as error:
                    raise QuizAgentError(
                        "The Quiz Agent could not be initialized."
                    ) from error

    return _quiz_agent


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate a New Assessment from Lecture PDF",
)
async def generate_quiz(
    request: QuizGenerationRequest,
) -> dict[str, Any]:
    """Synthesize a multi-question quiz anchored to the document's indexed semantic context."""
    db = get_document_database()

    # Validate that document exists
    try:
        doc = await run_in_threadpool(db.get_document, request.document_id)
    except DocumentDatabaseError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify document metadata.",
        ) from error

    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{request.document_id}' not found.",
        )

    try:
        agent = get_quiz_agent()
        quiz_record = await run_in_threadpool(agent.generate_quiz, request)
        return quiz_record.to_dict(include_solutions=True)
    except QuizAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.get(
    "/{quiz_id}",
    summary="Get Quiz Details",
)
async def get_quiz(
    quiz_id: str,
    include_solutions: bool = Query(
        default=False,
        description="Set to true to include correct answers and explanations (e.g. for post-test review)",
    ),
) -> dict[str, Any]:
    """Retrieve quiz questions and parameters."""
    try:
        agent = get_quiz_agent()
        quiz = await run_in_threadpool(agent.get_quiz, quiz_id)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve quiz.",
        ) from error

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID '{quiz_id}' not found.",
        )

    return quiz.to_dict(include_solutions=include_solutions)


@router.get(
    "/document/{document_id}",
    summary="List Quizzes for Document",
)
async def list_document_quizzes(
    document_id: str,
) -> list[dict[str, Any]]:
    """List all quizzes created for a specific lecture PDF."""
    try:
        agent = get_quiz_agent()
        quizzes = await run_in_threadpool(agent.list_document_quizzes, document_id)
        return [q.to_dict(include_solutions=False) for q in quizzes]
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not list document quizzes.",
        ) from error


@router.get(
    "",
    summary="List All Generated Quizzes",
)
async def list_all_quizzes() -> list[dict[str, Any]]:
    """List all quizzes created in the system."""
    try:
        agent = get_quiz_agent()
        quizzes = await run_in_threadpool(agent.list_all_quizzes)
        return [q.to_dict(include_solutions=False) for q in quizzes]
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not list quizzes.",
        ) from error


@router.post(
    "/{quiz_id}/evaluate",
    response_model=QuizEvaluationResponse,
    summary="Submit and Grade Quiz Answers",
)
async def evaluate_quiz_submission(
    quiz_id: str,
    submission: QuizEvaluationRequest,
) -> QuizEvaluationResponse:
    """Evaluate student answers against the quiz rubric, compute scores, and save the attempt."""
    try:
        agent = get_quiz_agent()
        response = await run_in_threadpool(
            agent.evaluate_quiz, quiz_id, submission
        )
        return response
    except QuizAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during quiz evaluation: {error}",
        ) from error


@router.post(
    "/{quiz_id}/evaluate-and-recommend",
    response_model=QuizEvaluationResponse,
    summary="Evaluate Answers & Trigger Recommendation Agent",
)
async def evaluate_and_recommend(
    quiz_id: str,
    submission: QuizEvaluationRequest,
) -> QuizEvaluationResponse:
    """Evaluate answers and immediately run multi-agent gap analysis and study recommendations."""
    try:
        quiz_agent = get_quiz_agent()
        rec_agent = get_recommendation_agent()
        response = await run_in_threadpool(
            quiz_agent.evaluate_and_recommend,
            quiz_id,
            submission,
            rec_agent,
        )
        return response
    except QuizAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete multi-agent evaluation and recommendation: {error}",
        ) from error


@router.delete(
    "/{quiz_id}",
    summary="Delete Quiz",
)
async def delete_quiz(quiz_id: str) -> dict[str, str]:
    """Delete a generated quiz."""
    try:
        db = get_document_database()
        existed = await run_in_threadpool(db.delete_quiz, quiz_id)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete quiz.",
        ) from error

    if not existed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID '{quiz_id}' not found.",
        )

    return {"message": "Quiz deleted successfully."}
