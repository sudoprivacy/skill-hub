# Skill Hub

Skill Hub contains a Quart API backend and a React admin console for managing skills, skill versions, categories, and assistants.

## Project Structure

```text
skill-hub/
├── backend/                 # Quart API, database models, migrations, Dockerfile
├── frontend/                # React + Vite admin console, Nginx Dockerfile
├── docker-compose.yml       # API + admin web + PostgreSQL
├── docker-compose.prod.yml  # Production image wiring
└── README.md
```

## Run With Docker Compose

```bash
export SKILL_HUB_AUTH_TOKEN=your-secret-token
docker compose up -d --build
```

Services:

- API: `http://localhost:${SKILL_HUB_PORT:-8080}`
- Admin console: `http://localhost:${SKILL_HUB_ADMIN_PORT:-5173}`
- PostgreSQL: internal service `db`

The admin console uses the same fixed token as the backend. Enter `SKILL_HUB_AUTH_TOKEN` on the login screen.

## Local Development

Backend:

```bash
cd backend
pip install -r requirements.txt
python main.py --auth-token your-secret-token --database-url postgresql://skill_hub:skill_hub@localhost:5432/skill_hub
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8080` by default. Override with `VITE_API_PROXY_TARGET` if needed.

## Admin Features

- Token-based login and session persistence in browser storage
- CRUD for skills
- CRUD for skill versions
- CRUD for categories
- CRUD and approval for assistants
- Search/filter controls for the list views

## Authentication

All protected API routes require:

```text
Authorization: Bearer your-secret-token
```

The admin login endpoint validates the token at:

```text
POST /api/auth/login
```

## Useful Endpoints

- `GET /health`
- `GET /api/docs`
- `GET /api/skills/admin/cursor`
- `GET /api/skill-versions`
- `GET /api/categories/admin`
- `GET /api/assistants/admin/cursor`

## Stop The Stack

```bash
docker compose down
docker compose down -v
```

The `-v` variant removes persisted database and app data volumes.
