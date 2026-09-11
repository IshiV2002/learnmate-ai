from threading import Lock
from typing import Any
from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.agents.tutor_agent import TutorAgent, TutorAgentError
from app.api.auth import CurrentUser
from app.api.documents import get_document_database, get_retrieval_agent
from app.database.models import (
    TutorChatRequest,
    TutorChatResponse,
    TutorSessionInitRequest,
    TutorSessionResponse,
)


router = APIRouter(prefix="/tutor", tags=["tutor"])

_tutor_agent: TutorAgent | None = None
_tutor_agent_lock = Lock()


def get_tutor_agent() -> TutorAgent:
    """Create one reusable Tutor Agent instance when first needed."""
    global _tutor_agent

    if _tutor_agent is None:
        with _tutor_agent_lock:
            if _tutor_agent is None:
                try:
                    db = get_document_database()
                    retrieval_agent = None
                    try:
                        retrieval_agent = get_retrieval_agent()
                    except Exception:
                        pass

                    _tutor_agent = TutorAgent(
                        database=db,
                        retrieval_agent=retrieval_agent,
                    )
                except Exception as error:
                    raise TutorAgentError(
                        "The Tutor Agent could not be initialized."
                    ) from error

    return _tutor_agent


@router.post(
    "/session/start",
    response_model=TutorSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a New AI Tutoring Session",
)
async def start_tutor_session(
    request: TutorSessionInitRequest,
    current_user: CurrentUser,
) -> TutorSessionResponse:
    """Initialize an AI tutoring session for a document or from a recommendation handoff."""
    try:
        if get_document_database().get_document(
            request.document_id, current_user.user_id
        ) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )
        request = request.model_copy(
            update={"student_id": current_user.user_id}
        )
        agent = get_tutor_agent()
        session = await run_in_threadpool(agent.start_session, request)
        return session
    except HTTPException:
        raise
    except TutorAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize tutoring session.",
        ) from error


@router.post(
    "/chat",
    response_model=TutorChatResponse,
    summary="Send Message to Socratic AI Tutor",
)
async def send_chat_message(
    request: TutorChatRequest,
    current_user: CurrentUser,
) -> TutorChatResponse:
    """Send student question/answer to the Tutor Agent and receive grounded Socratic explanation with citations."""
    try:
        agent = get_tutor_agent()
        session = await run_in_threadpool(
            agent.get_session_history, request.session_id
        )
        if session is None or session.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor session '{request.session_id}' not found.",
            )
        response = await run_in_threadpool(agent.respond, request)
        return response
    except HTTPException:
        raise
    except TutorAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process tutor conversational turn.",
        ) from error


@router.get(
    "/session/{session_id}",
    response_model=TutorSessionResponse,
    summary="Get Tutor Session History",
)
async def get_tutor_session(
    session_id: str,
    current_user: CurrentUser,
) -> TutorSessionResponse:
    """Retrieve full conversation history and metadata for an active or archived tutoring session."""
    try:
        agent = get_tutor_agent()
        session = await run_in_threadpool(agent.get_session_history, session_id)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve tutor session history.",
        ) from error

    if session is None or session.student_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor session '{session_id}' not found.",
        )

    return session


@router.get(
    "/student/{student_id}",
    summary="List Student Tutor Sessions",
)
async def list_student_tutor_sessions(
    student_id: str,
    current_user: CurrentUser,
) -> list[dict[str, Any]]:
    """List all AI tutoring sessions conducted by a student."""
    try:
        if student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access another user's tutor sessions.",
            )
        agent = get_tutor_agent()
        sessions = await run_in_threadpool(agent.list_student_sessions, student_id)
        return [s.to_dict() for s in sessions]
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not list student tutor sessions.",
        ) from error


@router.delete(
    "/session/{session_id}",
    summary="Delete Tutor Session",
)
async def delete_tutor_session(
    session_id: str,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Delete a tutor session and its message records."""
    try:
        agent = get_tutor_agent()
        session = await run_in_threadpool(agent.get_session_history, session_id)
        if session is None or session.student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor session '{session_id}' not found.",
            )
        deleted = await run_in_threadpool(agent.delete_session, session_id)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete tutor session.",
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor session '{session_id}' not found.",
        )

    return {
        "message": "Tutor session deleted successfully",
        "session_id": session_id,
    }
