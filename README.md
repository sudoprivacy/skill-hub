# Skill Hub

A Flask-based API Server for managing skills with fixed header token authentication.

## Features

- **Flask-based REST API**: Clean and modular API structure
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
│   │   ├── app.py              # Flask app factory
│   │   └── server.py           # Server class
│   └── routes/                  # API routes
│       ├── __init__.py
│       ├── routes.py           # Route registration
│       ├── health.py           # Health check routes
│       ├── auth.py             # Authentication routes
│       └── skills.py           # Skills management routes
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

### API Endpoints

#### Public Endpoints
- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /live` - Liveness check

#### Authentication Endpoints
- `POST /api/auth/login` - Login with token
- `GET /api/auth/verify` - Verify token from header
- `GET /api/auth/info` - Get authentication information

#### Protected Endpoints (require authentication)
- `GET /api/skills` - List skills (paginated)
- `POST /api/skills` - Create a new skill
- `GET /api/skills/<id>` - Get a specific skill
- `PUT /api/skills/<id>` - Update a skill
- `DELETE /api/skills/<id>` - Delete a skill

#### API Documentation
- `GET /api/docs` - API documentation

### Authentication

Skill Hub uses fixed header token authentication. Include the token in the `Authorization` header:

```bash
# Using Bearer prefix
Authorization: Bearer your-secret-token

# Or without prefix
Authorization: your-secret-token
```

### Example API Calls

#### Login
```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"token": "your-secret-token"}'
```

#### Verify Token
```bash
curl -X GET http://localhost:8080/api/auth/verify \
  -H "Authorization: Bearer your-secret-token"
```

#### List Skills
```bash
curl -X GET http://localhost:8080/api/skills \
  -H "Authorization: Bearer your-secret-token"
```

#### Create Skill
```bash
curl -X POST http://localhost:8080/api/skills \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Analysis",
    "description": "Data analysis and visualization skills",
    "category": "Analytics",
    "level": "Intermediate"
  }'
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

This project is structured similarly to the reference project at `/Users/zhangsuochao/gpustack/gpustack/gpustack`, with adaptations for Flask:

- **Configuration**: Similar configuration class pattern
- **API Structure**: Modular API with authentication, exceptions, and responses
- **Routes**: Organized route registration similar to FastAPI routers
- **Server**: Flask-based server with similar lifecycle management

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
