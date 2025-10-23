# Parvarish AI – FastAPI Backend Skeleton

A clean, scalable FastAPI backend structure for building an Islamic parenting chatbot.

## Highlights
- FastAPI app with modular architecture
- PostgreSQL via SQLAlchemy (psycopg2 driver)
- Clear separation of concerns: routes, db, nlp, services, schemas, utils, data
- Boilerplate only — ready for future implementation

## Folder Structure
- `app/`
	- `db/`
		- `base.py` – SQLAlchemy Base
		- `session.py` – Engine and session factory
		- `models/` – ORM models (e.g., `user.py`, `message.py`)
		- `crud/` – CRUD utilities (e.g., `user.py`, `message.py`)
	- `routes/` – API routers (`auth.py`, `chatbot.py`)
	- `nlp/` – NLP placeholders (`intent_detection.py`, `reference_fetcher.py`)
	- `services/` – External integrations (`llm_client.py`)
	- `schemas/` – Pydantic models (`user.py`, `chat.py`)
	- `utils/` – Helpers (`config.py`, `logging.py`)
- `data/` – Static JSON datasets (`quran_references.json`, `hadith_references.json`)
- `main.py` – App entry point (includes routers)
- `requirements.txt` – Dependencies
- `.env.example` – Sample environment variables

## Quickstart (Windows PowerShell)
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install --upgrade pip; pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ to see the health endpoint.

## Environment
- Set `DATABASE_URL` in `.env` (see `.env.example`). Example:
	`postgresql+psycopg2://user:password@localhost:5432/parvarish`

## Notes
- This is a skeleton. Functions raise `NotImplementedError` where logic will be added.
- Replace placeholder JSON in `data/` with curated references as you progress.
