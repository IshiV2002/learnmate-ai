# LearnMate AI Project Instructions

## Project

- Project name: LearnMate AI.
- LearnMate AI is a multi-agent personalized e-learning application.
- Frontend: React + Vite.
- Backend: Python FastAPI.
- Application database: SQLite.
- Vector database: ChromaDB.
- PDF processing: PyMuPDF.
- Embeddings: Sentence Transformers.
- LLM integration will use Gemini, but never hard-code API keys.

## Architecture

- Keep the frontend and backend clearly separated.
- Keep each AI agent in its own backend module.
- The planned agent modules are:
  - `retrieval_agent.py`
  - `tutor_agent.py`
  - `quiz_agent.py`
  - `recommendation_agent.py`
- Keep shared orchestration separate from agent-specific code.
- Design the Retrieval Agent so that the Tutor Agent and Quiz Agent can reuse it.

## Security

- Never commit `.env` files, API keys, passwords, JWT secrets, database secrets, or tokens.
- Use environment variables for all secrets.
- Validate uploaded files.
- Do not allow users to access another user's documents.
- Use safe filenames and prevent path traversal vulnerabilities.

## Development

- Prefer simple, beginner-readable implementations over unnecessary abstraction.
- Add comments where logic may be difficult for a beginner to understand.
- Do not introduce new frameworks unless necessary.
- Do not replace the agreed technology stack without asking first.
- Do not rewrite unrelated files when implementing a feature.
- Preserve other group members' work.
- Explain significant architectural changes before making them.

## Git

- Do not commit directly to `main` unless explicitly instructed.
- Work should be suitable for feature branches.
- Do not amend or rewrite another group member's commits.
- Keep commits focused on one logical change.

## Quality

- Validate code after making changes.
- Run relevant tests when they exist.
- Report which files were changed and why.
- If something cannot be tested, clearly say so.
