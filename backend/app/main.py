from fastapi import FastAPI


app = FastAPI(title="LearnMate AI API")


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
