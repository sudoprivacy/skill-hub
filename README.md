# Skill Hub

A Quart-based API Server for managing skills and digital assistants with fixed header token authentication.

## Features

- **Quart-based REST API**: Clean and modular async API structure
- **Fixed Header Token Authentication**: Simple token-based authentication via Authorization header
- **Modular Architecture**: Organized code structure with clear separation of concerns
- **Health Checks**: Built-in health, readiness, and liveness endpoints
- **Error Handling**: Comprehensive error handling with standardized responses
- **Configuration Management**: Environment-based configuration with validation

## Project Structure

```
skill-hub/
├── skill_hub/                    # Main package
│   ├── __init__.py              # Package metadata
│   ├── config/                  # Configuration
│   │   ├── __init__.py
│   │   └── config.py           # Configuration class
│   ├── api/                     # API utilities
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication utilities
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── responses.py        # Response utilities
│   ├── server/                  # Server management
│   │   ├── __init__.py
│   │   ├── app.py              # Quart app factory
│   │   └── server.py           # Server class
│   └── routes/                  # API routes
│       ├── __init__.py
│       ├── routes.py           # Route registration
│       ├── health.py           # Health check routes
│       ├── auth.py             # Authentication routes
│       ├── skills.py           # Skills management routes
│       ├── skill_versions.py   # Skill version routes
│       ├── categories.py       # Category routes
│       └── assistants.py       # Digital assistant routes
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Project configuration
├── .env.example               # Example environment variables
└── README.md                  # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd skill-hub
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` file with your configuration:
   ```bash
   SKILL_HUB_AUTH_TOKEN=your-secret-token-here
   SKILL_HUB_HOST=0.0.0.0
   SKILL_HUB_PORT=8080
   SKILL_HUB_DEBUG=false
   SKILL_HUB_DATA_DIR=./data
   SKILL_HUB_LOG_LEVEL=INFO
   SKILL_HUB_API_PREFIX=/api
   ```

## Usage

### Starting the Server

Using command line arguments:
```bash
python main.py --auth-token your-secret-token --port 8080 --debug
```

Using environment variables:
```bash
export SKILL_HUB_AUTH_TOKEN=your-secret-token
export SKILL_HUB_PORT=8080
export SKILL_HUB_DEBUG=true
python main.py
```

## API Reference

The default API prefix is `/api`. Change it with `SKILL_HUB_API_PREFIX`.

### Authentication

Skill Hub uses fixed header token authentication. Include the token in the `Authorization` header:

```bash
# Using Bearer prefix
Authorization: Bearer your-secret-token

# Or without prefix
Authorization: your-secret-token
```

All `/api/*` endpoints require this header. Swagger UI, ReDoc, OpenAPI JSON, health checks, and `/` are public.

### Response Format

Successful JSON responses use the following envelope:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {}
}
```

Error responses use:

```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Human-readable error message"
  }
}
```

Some exception handlers return the same `error` object without the top-level `success` field.

### Public Endpoints

| Method | Path | Input | Output |
|--------|------|-------|--------|
| `GET` | `/` | None | Service metadata: `service`, `version`, `docs`, `health` |
| `GET` | `/health` | None | Health status |
| `GET` | `/ready` | None | Readiness status |
| `GET` | `/live` | None | Liveness status |
| `GET` | `/api/docs` | None | Swagger UI |
| `GET` | `/api/redoc` | None | ReDoc UI |
| `GET` | `/api/openapi.json` | None | OpenAPI schema |

### Auth Endpoints

These endpoints are also under `/api`, so include the `Authorization` header.

#### Verify Token

`GET /api/auth/verify`

Headers:

| Name | Required | Description |
|------|----------|-------------|
| `Authorization` | Yes | `Bearer <token>` or raw token |

Response `data`:

```json
{
  "authenticated": true,
  "message": "Token is valid"
}
```

#### Auth Info

`GET /api/auth/info`

Response `data`:

```json
{
  "auth_type": "fixed_token",
  "header_name": "Authorization",
  "token_prefix": "Bearer",
  "api_prefix": "/api"
}
```

### Skill Endpoints

Skills and assistants support multiple tenant owners. Skill APIs use
`tenant_ids`; assistant APIs use `tenantIds` and also accept `tenant_ids`.
The legacy singular fields remain in requests and responses. When plural and
singular fields are both present, the plural array is authoritative and the
singular value is synchronized to its first item. An empty array makes a
resource public.

#### List Published Skills

`GET /api/skills/cursor`

Returns published public skills by default. When `tenant_id` is omitted, only skills with no tenant are returned.

Query parameters:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `cursor` | string | No | `null` | Cursor returned by the previous page |
| `limit` | integer | No | `10` | Maximum number of records |
| `query` | string | No | `""` | Search skill name or description |
| `categories` | string | No | `""` | Filter by category |
| `tenant_id` | string | No | `null` | Match resources containing this tenant ID; omit for public resources |

Response `data`:

```json
{
  "skills": [
    {
      "id": "uuid",
      "name": "weather",
      "display_name": "Weather Forecast",
      "author_id": "uuid",
      "tenant_id": "tenant-a",
      "tenant_ids": ["tenant-a", "tenant-b"],
      "description": "Skill description",
      "category": "Tools",
      "categories": ["Tools"],
      "emoji": "sun",
      "icon": "skill-hub/<skill_id>/icon.png",
      "homepage": "https://example.com",
      "star_count": 0,
      "download_count": 0,
      "status": 1,
      "sort_order": 0,
      "core_features": "Feature list",
      "applicable_scenarios": "Scenario list",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-01T00:00:00",
      "latestVersion": {
        "version": "v1.0.0",
        "source_url": "https://...",
        "download_url": "/api/skill-versions/<version_id>/download",
        "checksum": "",
        "changelog": "Initial release",
        "created_at": "2026-01-01T00:00:00"
      }
    }
  ],
  "next_cursor": "opaque cursor or null",
  "has_more": false
}
```

#### List All Skills For Admin

`GET /api/skills/admin/cursor`

Same as `/api/skills/cursor`, plus:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `status` | integer | No | `null` | Filter by status. `0` means pending review, `1` means approved/published |

#### Get Skill Details

`GET /api/skills/{skill_id}`

Path parameters:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_id` | UUID | Yes | Skill ID |

Response `data`:

```json
{
  "skill": {
    "id": "uuid",
    "name": "weather",
    "display_name": "Weather Forecast",
    "author_id": "uuid",
    "tenant_id": "tenant-a",
    "tenant_ids": ["tenant-a", "tenant-b"],
    "description": "Skill description",
    "category": "Tools",
    "categories": ["Tools"],
    "emoji": "sun",
    "icon": "skill-hub/<skill_id>/icon.png",
    "homepage": "https://example.com",
    "star_count": 0,
    "download_count": 0,
    "status": 1,
    "sort_order": 0,
    "core_features": "Feature list",
    "applicable_scenarios": "Scenario list",
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
  },
  "versions": [
    {
      "id": "uuid",
      "skill_id": "uuid",
      "version": "v1.0.0",
      "source_url": "https://...",
      "download_url": "/api/skill-versions/<version_id>/download",
      "checksum": "",
      "changelog": "Initial release",
      "readme_content": "README content",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-01T00:00:00"
    }
  ]
}
```

#### Create Skill And First Version

`POST /api/skills`

Content type: `multipart/form-data`

Form fields:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Unique skill identifier |
| `display_name` | string | Yes | Display name |
| `version` | string | Yes | Version string, for example `v1.0.0` |
| `skill_file` | file | Yes | Skill package. Must be `.zip` |
| `icon_file` | file | No | Skill icon. Must be `.png` or `.svg` |
| `category` | string | No | Primary category |
| `categories` | string/list | No | Categories. Send repeated fields or a serialized value |
| `description` | string | No | Description |
| `core_features` | string | No | Core features |
| `applicable_scenarios` | string | No | Applicable scenarios |
| `emoji` | string | No | Emoji or short icon marker |
| `homepage` | string | No | Homepage URL |
| `changelog` | string | No | Version changelog |
| `author_id` | UUID | No | Author ID |
| `tenant_ids` or `tenantIds` | array/JSON/CSV | No | Tenant IDs. The plural field takes precedence; send `[]` for public skills |
| `tenant_id` or `tenantId` | string | No | Legacy single-tenant field, used only when the plural field is omitted |
| `sort_order` | integer | No | Display order. Defaults to `0` |
| `status` | integer | No | `0` pending review, `1` approved. Defaults to `0` |

Response `data`:

```json
{
  "skill": {
    "id": "uuid",
    "name": "weather",
    "display_name": "Weather Forecast",
    "status": 0
  },
  "version": {
    "id": "uuid",
    "skill_id": "uuid",
    "version": "v1.0.0",
    "source_url": "https://...",
    "download_url": "/api/skill-versions/<version_id>/download",
    "checksum": "",
    "changelog": "Initial release",
    "readme_content": null
  }
}
```

#### Update Skill

`PUT /api/skills/{skill_id}`

Content type: `application/json` or `multipart/form-data`

Supported fields:

| Name | Type | Description |
|------|------|-------------|
| `name` | string | New unique identifier |
| `display_name` or `displayName` | string | Display name |
| `category` | string | Primary category |
| `categories` | array/string | Categories. String values may be JSON or comma-separated |
| `description` | string | Description |
| `core_features` or `coreFeatures` | string | Core features |
| `applicable_scenarios` or `applicableScenarios` | string | Applicable scenarios |
| `emoji` | string | Emoji or short icon marker |
| `icon` | string | Existing icon object key or URL |
| `icon_file` | file | New icon. Multipart only, `.png` or `.svg` |
| `homepage` | string | Homepage URL |
| `author_id` or `authorId` | UUID | Author ID |
| `tenant_ids` or `tenantIds` | array/JSON/CSV | Complete tenant list. Takes precedence; send `[]` for a public skill |
| `tenant_id` or `tenantId` | string | Legacy single-tenant field |
| `sort_order` or `sortOrder` | integer | Display order |
| `status` | integer | Skill status |
| `star_count` or `starCount` | integer | Star count |
| `download_count` or `downloadCount` | integer | Download count |

Version fields such as `version`, `source_url`, `checksum`, `changelog`, `readme_content`, and `skill_file` are ignored by this endpoint.

Response `data`: updated skill object.

#### Approve Skill

`POST /api/skills/{skill_id}/approve`

Sets `status` to `1`.

Response `data`: updated skill object.

#### Delete Skill

`DELETE /api/skills/{skill_id}`

Response `data`: `null`.

#### Download Local Content

`GET /api/skills/content/{object_key}`

Serves a locally stored package or icon when local content mode is enabled. `object_key` is a stored key such as `skill-hub/<skill_id>/pkg.zip`.

### Skill Version Endpoints

#### Create Skill Version

`POST /api/skill-versions/`

Content type: `multipart/form-data`

Form fields:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `skill_id` | UUID | Yes | Parent skill ID |
| `version` | string | Yes | Version string |
| `skill_file` | file | Yes | Version package. Must be `.zip` |

Response `data`: skill version object.

#### Get Skill Version

`GET /api/skill-versions/{version_id}`

Response `data`:

```json
{
  "id": "uuid",
  "skill_id": "uuid",
  "version": "v1.0.0",
  "source_url": "https://...",
  "download_url": "/api/skill-versions/<version_id>/download",
  "checksum": "",
  "changelog": "",
  "readme_content": "",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

#### Download Skill Version

`GET /api/skill-versions/{version_id}/download`

Returns a file response in local content mode, or redirects with HTTP `302` to the object storage URL. Each successful download increments the parent skill's `download_count`.

### Assistant Endpoints

#### List Published Assistants

`GET /api/assistants/cursor`

Returns published public assistants by default. When `tenant_id` is omitted, only assistants with no tenant are returned.

Query parameters:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `cursor` | string | No | `null` | Cursor returned by the previous page |
| `limit` | integer | No | `10` | Maximum number of records |
| `query` | string | No | `""` | Search assistant name or description |
| `category` | string | No | `""` | Filter by value in `categories` |
| `tenant_id` | string | No | `null` | Match resources containing this tenant ID; omit for public resources |

Response `data`:

```json
{
  "assistants": [
    {
      "id": "uuid",
      "name": "research-helper",
      "profession": "Research Assistant",
      "description": "Assistant description",
      "promptFile": "https://...",
      "avatar": "https://...",
      "sourceUrl": "https://...",
      "defaultInitPrompt": "Hello",
      "tenantId": "tenant-a",
      "tenantIds": ["tenant-a", "tenant-b"],
      "sortOrder": 0,
      "categories": ["Research"],
      "status": 1,
      "skills": ["uuid"],
      "createdAt": "2026-01-01T00:00:00",
      "updatedAt": "2026-01-01T00:00:00",
      "latestVersion": {
        "version": "v1.0.0",
        "source_url": "https://...",
        "checksum": "",
        "changelog": "Initial release",
        "created_at": "2026-01-01T00:00:00"
      }
    }
  ],
  "next_cursor": "opaque cursor or null",
  "has_more": false
}
```

#### List All Assistants For Admin

`GET /api/assistants/admin/cursor`

Same as `/api/assistants/cursor`, plus optional `status` query parameter.

#### Get Assistant Details

`GET /api/assistants/{assistant_id}`

Response `data`:

```json
{
  "assistant": {
    "id": "uuid",
    "name": "research-helper",
    "profession": "Research Assistant",
    "description": "Assistant description",
    "promptFile": "https://...",
    "avatar": "https://...",
    "sourceUrl": "https://...",
    "defaultInitPrompt": "Hello",
    "tenantId": "tenant-a",
    "tenantIds": ["tenant-a", "tenant-b"],
    "sortOrder": 0,
    "categories": ["Research"],
    "status": 1,
    "skills": ["uuid"],
    "createdAt": "2026-01-01T00:00:00",
    "updatedAt": "2026-01-01T00:00:00"
  },
  "versions": [
    {
      "id": "uuid",
      "assistant_id": "uuid",
      "version": "v1.0.0",
      "source_url": "https://...",
      "checksum": "",
      "changelog": "Initial release",
      "created_at": "2026-01-01T00:00:00",
      "updated_at": "2026-01-01T00:00:00"
    }
  ]
}
```

#### Create Assistant

`POST /api/assistants`

Content type: `multipart/form-data`

Form fields:

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Assistant name |
| `profession` | string | Yes | Role or profession |
| `version` | string | No | Source package version. Defaults to `v1.0.0` |
| `description` | string | No | Description |
| `defaultInitPrompt` or `default_init_prompt` | string | No | Default initial prompt |
| `tenantIds` or `tenant_ids` | array/JSON/CSV | No | Tenant IDs. The plural field takes precedence; send `[]` for public assistants |
| `tenantId` or `tenant_id` | string | No | Legacy single-tenant field, used only when the plural field is omitted |
| `sortOrder` or `sort_order` | integer | No | Display order. Defaults to `0` |
| `status` | integer | No | `0` pending review, `1` approved. Defaults to `0` |
| `categories` | array/string | No | Categories. String values may be JSON or comma-separated |
| `skills` | array/string | No | Skill UUIDs. String values may be JSON or comma-separated |
| `changelog` | string | No | Version changelog |
| `prompt_file` | file | No | Prompt file. Must be `.md` |
| `avatar` | file | No | Avatar. Must be `.png` |
| `source_url` | file | No | Source package. Must be `.zip` |

Response `data`:

```json
{
  "assistant": {
    "id": "uuid",
    "name": "research-helper",
    "profession": "Research Assistant",
    "latestVersion": {
      "id": "uuid",
      "assistant_id": "uuid",
      "version": "v1.0.0",
      "source_url": "https://...",
      "checksum": "",
      "changelog": "Initial release"
    }
  },
  "version": {
    "id": "uuid",
    "assistant_id": "uuid",
    "version": "v1.0.0",
    "source_url": "https://...",
    "checksum": "",
    "changelog": "Initial release"
  }
}
```

If no `source_url` file is uploaded, `version` is `null`.

#### Update Assistant

`PUT /api/assistants/{assistant_id}`

Content type: `application/json`

Supported fields:

| Name | Type | Description |
|------|------|-------------|
| `name` | string | Assistant name |
| `profession` | string | Role or profession |
| `description` | string | Description |
| `promptFile` or `prompt_file` | string | Prompt file URL or object key |
| `avatar` | string | Avatar URL or object key |
| `sourceUrl` or `source_url` | string | Source URL or object key |
| `defaultInitPrompt` or `default_init_prompt` | string | Default initial prompt |
| `tenantIds` or `tenant_ids` | array/JSON/CSV | Complete tenant list. Takes precedence; send `[]` for a public assistant |
| `tenantId` or `tenant_id` | string | Legacy single-tenant field |
| `sortOrder` or `sort_order` | integer | Display order |
| `categories` | array/string | Categories. String values may be JSON or comma-separated |
| `skills` | array/string | Skill UUIDs. String values may be JSON or comma-separated |
| `status` | integer | Assistant status |

Response `data`: updated assistant object.

#### Approve Assistant

`POST /api/assistants/{assistant_id}/approve`

Sets `status` to `1`.

Response `data`: updated assistant object.

#### Delete Assistant

`DELETE /api/assistants/{assistant_id}`

Response `data`: `null`.

### Category Endpoints

#### List Categories

`GET /api/categories`

Query parameters:

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `type` | integer | No | `0` | `0` for skill categories, `1` for assistant categories |

Response `data` is a list of display names:

```json
["Tools", "Research"]
```

#### Get Category

`GET /api/categories/{category_id}`

Response `data`:

```json
{
  "id": "uuid",
  "name": "tools",
  "display_name": "Tools",
  "order_index": 0,
  "icon_url": "https://...",
  "type": 0,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

#### Create Category

`POST /api/categories`

Content type: `application/json`

Request body:

```json
{
  "name": "tools",
  "display_name": "Tools",
  "order_index": 0,
  "icon_url": "https://example.com/icon.png",
  "type": 0
}
```

Response `data`: created category object.

### Example API Calls

#### Verify Token
```bash
curl -X GET http://localhost:8080/api/auth/verify \
  -H "Authorization: Bearer your-secret-token"
```

#### List Skills
```bash
curl -X GET "http://localhost:8080/api/skills/cursor?limit=10" \
  -H "Authorization: Bearer your-secret-token"
```

#### Create Skill
```bash
curl -X POST http://localhost:8080/api/skills \
  -H "Authorization: Bearer your-secret-token" \
  -F "name=data-analysis" \
  -F "display_name=Data Analysis" \
  -F "version=v1.0.0" \
  -F "category=Analytics" \
  -F "description=Data analysis and visualization skills" \
  -F "skill_file=@./data-analysis.zip" \
  -F "icon_file=@./icon.png"
```

#### Create Assistant
```bash
curl -X POST http://localhost:8080/api/assistants \
  -H "Authorization: Bearer your-secret-token" \
  -F "name=research-helper" \
  -F "profession=Research Assistant" \
  -F "version=v1.0.0" \
  -F "categories=Research,Writing" \
  -F "skills=00000000-0000-0000-0000-000000000000" \
  -F "prompt_file=@./prompt.md" \
  -F "avatar=@./avatar.png" \
  -F "source_url=@./assistant.zip"
```

## Docker

Skill Hub ships with a production-ready `Dockerfile` (multi-stage build, non-root user, tini as PID 1, healthcheck) and a `docker-compose.yml` that also provisions a PostgreSQL database for local use.

### Build the image

```bash
docker build -t skill-hub:latest .
```

### Run the container

```bash
docker run --rm -p 8080:8080 \
  -e SKILL_HUB_AUTH_TOKEN=your-secret-token \
  -e SKILL_HUB_DATABASE_URL=postgresql://user:pass@host:5432/skill_hub \
  -v skill-hub-data:/app/data \
  --name skill-hub \
  skill-hub:latest
```

All configuration options in the [Configuration Options](#configuration-options) table can be passed via `-e` environment variables. The container listens on port `8080` and runs as the non-root `skillhub` user.

### Run with docker-compose (app + PostgreSQL)

```bash
# Optional: override defaults by exporting variables or creating a .env file
export SKILL_HUB_AUTH_TOKEN=your-secret-token

docker compose up -d --build
```

This will start a PostgreSQL 16 instance and the Skill Hub API server wired together on an internal network. Data is persisted to the `pgdata` and `skill-hub-data` named volumes.

To stop and remove the stack:

```bash
docker compose down          # keep volumes
docker compose down -v       # also remove volumes (destructive)
```

### Publishing the image

You can tag and push the image to any container registry:

```bash
docker tag skill-hub:latest ghcr.io/<owner>/skill-hub:latest
docker push ghcr.io/<owner>/skill-hub:latest
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
flake8 .
```

### Project Structure Reference

This project is structured similarly to the reference project at `/Users/zhangsuochao/gpustack/gpustack/gpustack`, with adaptations for Quart:

- **Configuration**: Similar configuration class pattern
- **API Structure**: Modular API with authentication, exceptions, and responses
- **Routes**: Organized route registration similar to FastAPI routers
- **Server**: Quart-based server with similar lifecycle management

## Database Configuration

Skill Hub supports PostgreSQL database connections. Configure the database in your `.env` file:

```bash
# PostgreSQL Database Configuration
SKILL_HUB_DATABASE_URL=postgresql://username:password@localhost:5432/skill_hub
SKILL_HUB_DATABASE_POOL_SIZE=10
SKILL_HUB_DATABASE_MAX_OVERFLOW=20
SKILL_HUB_DATABASE_POOL_RECYCLE=3600
```

Or via command line arguments:
```bash
python main.py \
  --auth-token your-token \
  --database-url postgresql://user:pass@localhost:5432/skill_hub \
  --database-pool-size 10 \
  --database-max-overflow 20 \
  --database-pool-recycle 3600
```

### Database Migrations

Skill Hub uses Alembic for database migrations. To create and apply migrations:

1. Initialize Alembic (if not already initialized):
   ```bash
   alembic init alembic
   ```

2. Create a new migration:
   ```bash
   alembic revision --autogenerate -m "Create skills table"
   ```

3. Apply migrations:
   ```bash
   alembic upgrade head
   ```

4. Rollback migrations:
   ```bash
   alembic downgrade -1
   ```

### Skills Table Schema

The `skills` table has the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Unique identifier for the skill |
| name | VARCHAR(255) | Folder name/unique identifier (e.g., weather) |
| display_name | VARCHAR(255) | Display name (e.g., Weather Forecast Expert) |
| author_id | UUID | Developer ID |
| description | TEXT | Description from SKILL.md, used for keyword search |
| category | VARCHAR(100) | Category (e.g., AI/Vision, Tools, Social) |
| emoji | VARCHAR(10) | Corresponding icon (from metadata) |
| homepage | VARCHAR(500) | Skill homepage link |
| star_count | INTEGER | Number of stars/likes |
| download_count | INTEGER | Number of package downloads/installations |
| created_at | TIMESTAMP WITH TIME ZONE | First listing time |
| updated_at | TIMESTAMP WITH TIME ZONE | Last update time |

### Sample Data

Sample skills are included in the migration file for testing:
- Weather Forecast Expert (AI/Vision)
- Multi-language Translator (Tools)
- Code Review Assistant (Tools)
- Personal Fitness Coach (Social)
- Personal Finance Advisor (Tools)

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| SKILL_HUB_AUTH_TOKEN | (required) | Authentication token |
| SKILL_HUB_HOST | 0.0.0.0 | Server host |
| SKILL_HUB_PORT | 8080 | Server port |
| SKILL_HUB_DEBUG | false | Enable debug mode |
| SKILL_HUB_DATABASE_URL | (optional) | PostgreSQL database URL |
| SKILL_HUB_DATABASE_POOL_SIZE | 10 | Database connection pool size |
| SKILL_HUB_DATABASE_MAX_OVERFLOW | 20 | Database connection pool max overflow |
| SKILL_HUB_DATABASE_POOL_RECYCLE | 3600 | Connection pool recycle time (seconds) |
| SKILL_HUB_DATA_DIR | ./data | Data directory |
| SKILL_HUB_LOG_LEVEL | INFO | Logging level |
| SKILL_HUB_API_PREFIX | /api | API URL prefix |

## License

MIT License
