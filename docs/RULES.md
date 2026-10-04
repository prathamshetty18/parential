# Project Rules & Development Guidelines

1. **Strict PRD Adherence**: Follow `docs/PRD.md` only. Do not build features outside the specified scope.
2. **Incremental Development**: Work in small, well-defined steps. Always present an implementation plan before making edits.
3. **Comprehensive Test Coverage**: Every API endpoint must have a corresponding `pytest` test suite.
4. **Environment Configuration & Security**: No secrets or credentials in source code. Read all configurations and secrets strictly from environment variables.
5. **Child Data Privacy**: Child data is strictly sensitive: never log child names, personal details, or raw reasoning text in application logs.
6. **Fixed Backend Stack**: The backend stack is locked to **Python 3.12, FastAPI, PostgreSQL, SQLAlchemy, and Alembic**. Do not switch to Node.js or any other framework/language.
