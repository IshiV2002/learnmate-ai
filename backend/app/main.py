from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.quizzes import router as quizzes_router
from app.api.recommendations import router as recommendations_router
from app.api.tutor import router as tutor_router
from app.core.config import FRONTEND_ORIGINS


app = FastAPI(title="LearnMate AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(documents_router)
app.include_router(quizzes_router)
app.include_router(recommendations_router)
app.include_router(tutor_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return basic information about the API."""
    return {
        "name": "LearnMate AI API",
        "status": "running",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """Confirm that the API is running."""
    return {"status": "healthy"}
