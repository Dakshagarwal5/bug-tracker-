# Bug Reporting System Backend

Authentication-secured REST API backend for a Bug Reporting System.

## Tech Stack
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (Async SQLAlchemy + Alembic)
- **Cache**: Redis
- **Auth**: JWT (RS256) + Argon2
- **Infrastructure**: Docker, Docker Compose, Nginx, Kubernetes

## Setup & Running

### Prerequisites
- Docker & Docker Compose

### Quick Start
1. **Generate Keys**: (Optional for dev, autocreated if missing or defined in env keys)
   The app expects RS256 keys. You can generate them:
   ```bash
   ssh-keygen -t rsa -b 4096 -m PEM -f keys/private.pem
   openssl rsa -in keys/private.pem -pubout -outform PEM -out keys/public.pem
   ```
   *Note: For this demo, update `.env` or `config.py` to point to keys, or ensure keys are in `keys/` directory mapped in docker-compose.*

2. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```
   This starts:
   - Backend on `http://localhost:8000` (Direct)
   - Nginx on `http://localhost:80` (Reverse Proxy)
   - Postgres on port `5432`
   - Redis on port `6379`

3. **Access API Docs**:
   - Swagger UI: `http://localhost:8000/api/v1/docs` (or via Nginx `http://localhost/api/v1/docs`)

4. **Run Migrations**:
   Inside the backend container:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Initial"
   docker-compose exec backend alembic upgrade head
   ```

## Testing
To run the tests (Unit & Integration):
```bash
# Install dependencies locally or run in container
pip install -r requirements.txt
pytest
```
*Note: Tests use in-memory SQLite for speed/isolation.*

## Architecture
- **Permissions**: Enforced in Service layer via RBAC checks.
- **State Machine**: Issue status transitions (`open` -> `in_progress` -> `resolved` ...) are strictly validated.
- **Soft Delete**: Projects are soft-deleted (`is_archived=True`); generic repositories handle filtering.
- **Security**: 
  - JWT RS256 for Auth.
  - Rate Limiting (Redis) for Login (5/min) and Global (100/min).
  - Secure Headers & CORS.

## Project Structure
- `app/core`: Config, Security, Logging
- `app/db`: Database connection & Base models
- `app/models`: SQLAlchemy Enitties
- `app/repositories`: DB Access Layer
- `app/services`: Business Logic & Permissions
- `app/api`: FastAPI Routes & Dependencies
- `infra/`: Kubernetes & Nginx configs
