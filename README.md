# Healthcare Appointment Management System

A full-stack monorepo application providing an AI-powered healthcare chatbot for managing patient appointments through natural conversation.

## Overview

This system combines three services:

- **AI Service** (Port 8000): LangGraph-powered conversational AI backend using OpenAI/Anthropic
- **MCP Server** (Port 8080): Model Context Protocol server exposing database operations as tools
- **UI Service** (Port 8501): Streamlit-based chat interface for patients

**Core Capabilities**: Patient verification, appointment viewing, scheduling, rescheduling, and cancellation via natural language.

## Repository Structure

```
.
├── apps/
│   ├── ai-service/         # FastAPI + LangGraph conversational backend
│   ├── mcp-server/         # FastMCP server for database tools
│   ├── ui-service/         # Streamlit chat interface
│   └── utils/              # Shared utilities (logging, retries, file I/O)
├── database/scripts/       # PostgreSQL schema and seed data
├── docker-compose.yml      # Multi-service orchestration
└── README.md
```

## Quick Start

### Prerequisites

- Docker (v20.10+) and Docker Compose (v2.0+)
- OpenAI API key (`OPENAI_API_KEY`)

### Setup

1. **Clone and configure**

```bash
git clone <repository-url>
cd lumahealth-assignment

# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
EOF
```

2. **Start all services**

```bash
docker-compose up --build -d
```

3. **Access the application**

- **Chatbot UI**: http://localhost:8501
- **AI Service API**: http://localhost:8000/docs
- **MCP Server**: http://localhost:8080/mcp/

### Verify Installation

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Services

### AI Service (Port 8000)

**Technology Stack**: FastAPI, LangGraph, LangChain, PostgreSQL checkpointing, FastMCP client

**Key Features**:
- Multi-turn conversation with state management
- Natural language understanding for appointment operations
- Conversation persistence via LangGraph checkpoints
- Integration with MCP tools for database operations

**Development**:
```bash
cd apps/ai-service
uv sync --frozen --no-dev --no-install-project
export DATABASE_URL=postgresql://postgres:password@localhost:5432/db-appointments
export MCP_SERVER_URL=http://localhost:8080/mcp
export OPENAI_API_KEY=your-key
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### MCP Server (Port 8080)

**Technology Stack**: FastMCP, asyncpg

**Available Tools**:
- `pg_query`: Execute SELECT queries (read-only)
- `pg_execute`: Run INSERT/UPDATE/DELETE operations
- `pg_schema`: Inspect database schema
- `db_transaction`: Execute multiple queries atomically

**Development**:
```bash
cd apps/mcp-server
uv sync --frozen --no-dev --no-install-project
export DATABASE_URL=postgresql://postgres:password@localhost:5432/db-appointments
uv run uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

### UI Service (Port 8501)

**Technology Stack**: Streamlit, SQLAlchemy

**Features**:
- ChatGPT-like interface
- Session-based conversation history
- Structured data collection forms (name, phone, DOB)
- Real-time AI service integration

**Development**:
```bash
cd apps/ui-service
uv sync --frozen --no-dev --no-install-project
export DATABASE_URL=postgresql://postgres:password@localhost:5432/db-appointments
export CHATBOT_API_URL=http://localhost:8000/api/v1/chatbot/question
uv run streamlit run src/app.py
```

## API Reference

### AI Service

#### POST `/api/v1/chatbot/question`

Submit a question to the AI chatbot.

**Request**:
```json
{
  "request_id": "req-123",           // Required
  "user_id": "user-456",             // Required
  "user_message": "Show my appointments",  // Required
  "session_id": "session-789"        // Required
}
```

**Response (200)**:
```json
{
  "request_id": "req-123",
  "user_id": "user-456",
  "system_answer": "I'd be happy to help. First, I need to verify your identity..."
}
```

**Error Codes**: 400 (Bad Request), 422 (Validation Error), 500 (Internal Error), 502 (QA Processing Error)

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chatbot/question \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "I want to cancel my appointment",
    "session_id": "session-123"
  }'
```

#### GET `/api/v1/health/checker`

Health check endpoint.

**Response (200)**:
```json
{
  "status": "RUNNING",
  "timestamp": "2025-09-29T12:34:56.789Z"
}
```

### MCP Server

#### GET `/mcp/health`

Check server and service health.

**Response (200)**:
```json
{
  "status": "ok",
  "server": "Modular MCP Server",
  "services": {
    "database": {"ok": true, "error": null},
    "postgres": {"ok": true, "error": null}
  }
}
```

#### GET `/mcp/ready`

Check if server is ready to accept requests.

**Response (200/503)**:
```json
{
  "status": "ready",                  // or "degraded"
  "failed_services": []
}
```

#### GET `/mcp/tools`

List all available tools.

**Response (200)**:
```json
{
  "server": "Modular MCP Server",
  "tools": {
    "postgres": [
      {
        "name": "pg_query",
        "description": "Run a SELECT query (read-only)",
        "parameters": {
          "query": {"type": "string", "required": true},
          "params": {"type": "array", "required": false}
        }
      }
      // ... other tools
    ]
  }
}
```

### Database Tools (MCP Protocol)

These tools are invoked by the AI service via MCP.

#### `pg_query` - Read Data

Execute SELECT queries.

**Parameters**:
```json
{
  "query": "SELECT * FROM appointment WHERE patient_id = $1",
  "params": ["123e4567-e89b-12d3-a456-426614174000"]
}
```

**Response**:
```json
{
  "status": "success",
  "rows_returned": 2,
  "data": [
    {
      "id": "a1b2c3d4...",
      "patient_id": "123e4567...",
      "starts_at": "2025-10-15T10:00:00Z",
      "reason": "Annual checkup",
      "status": "scheduled"
    }
  ]
}
```

#### `pg_execute` - Write Data

Execute INSERT/UPDATE/DELETE operations.

**Example (INSERT)**:
```json
{
  "query": "INSERT INTO patient (full_name, phone, date_of_birth) VALUES ($1, $2, $3) RETURNING id",
  "params": ["John Doe", "+14155551234", "1985-05-15"]
}
```

**Example (UPDATE)**:
```json
{
  "query": "UPDATE appointment SET status = $1 WHERE id = $2",
  "params": ["canceled_by_patient", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Query executed successfully: INSERT 0 1"
}
```

#### `pg_schema` - Inspect Schema

Get database schema information.

**Parameters**:
```json
{
  "table_name": "appointment"  // Optional: omit to list all tables
}
```

**Response (specific table)**:
```json
{
  "status": "success",
  "schema_info": [
    {
      "column_name": "id",
      "data_type": "uuid",
      "is_nullable": "NO",
      "column_default": "gen_random_uuid()"
    }
  ]
}
```

#### `db_transaction` - Atomic Operations

Execute multiple queries within a transaction.

**Parameters**:
```json
{
  "queries": [
    {
      "query": "INSERT INTO patient (...) VALUES (...) RETURNING id",
      "params": ["Jane Smith", "+14155559876", "1990-08-20"]
    },
    {
      "query": "INSERT INTO appointment (...) VALUES (...)",
      "params": ["patient-id", "clinic-id", "provider-id", "2025-11-01T14:00:00Z"]
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Transaction completed successfully",
  "results": ["INSERT 0 1", "INSERT 0 1"]
}
```

### Database Schema

**Core Tables**:

- **`clinic`**: Healthcare facilities (id, name, address, created_at)
- **`provider`**: Healthcare providers (id, clinic_id, full_name, specialty, created_at)
- **`patient`**: Patient records (id, full_name, phone [unique], date_of_birth, email, created_at)
- **`appointment`**: Appointments (id, patient_id, clinic_id, provider_id, starts_at, ends_at, reason, status, created_at, updated_at)

**Appointment Status Values**: `scheduled`, `confirmed`, `canceled_by_patient`, `canceled_by_clinic`

## Architecture

### System Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   UI Service    │ (Streamlit - Port 8501)
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐      ┌──────────────┐
│   AI Service    │◄────►│  MCP Server  │ (Port 8080)
│   (FastAPI)     │ MCP  │  (FastMCP)   │
└────────┬────────┘      └──────┬───────┘
         │                      │
         │ LangGraph            │ asyncpg
         │ Checkpointing        │
         ▼                      ▼
    ┌─────────────────────────────┐
    │      PostgreSQL DB          │ (Port 5432)
    └─────────────────────────────┘
```

### Conversation Flow

1. User sends message via Streamlit UI
2. UI forwards to AI service `/api/v1/chatbot/question`
3. AI service:
   - Uses LangGraph to determine conversation state
   - Invokes MCP tools for database operations
   - Stores checkpoints in PostgreSQL
4. Response returned to UI and displayed

### AI Workflow

The AI service uses LangGraph for multi-step conversation orchestration:

![QA Graph](images/qa_graph.png)

## Development

### Installing Dependencies

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies for a service
cd apps/<service-name>
uv sync

# Add new dependency
uv add <package-name>
```

### Testing

#### Test Organization

Tests are organized to **mirror the source code structure**, making it easy to locate and maintain tests:

```
apps/
├── ai-service/
│   ├── src/
│   │   └── ai/graph/services/        # Source code
│   │       ├── llm.py
│   │       └── qa/
│   │           ├── intent.py
│   │           ├── extraction.py
│   │           ├── validation.py
│   │           ├── response.py
│   │           ├── query_tool.py
│   │           └── query_orm.py
│   │
│   └── tests/
│       ├── conftest.py               # Root fixtures (DB, MCP, env)
│       │
│       └── ai/graph/services/        # Tests mirror source structure
│           ├── conftest.py           # Service-specific fixtures
│           ├── test_llm.py           # Tests for llm.py
│           └── qa/
│               ├── test_intent.py    # Tests for qa/intent.py
│               ├── test_extraction.py
│               ├── test_validation.py
│               ├── test_response.py
│               ├── test_query_tool.py
│               └── test_query_orm.py
│
├── mcp-server/tests/
└── ui-service/tests/
```

**Test Structure Benefits**:
- **1:1 Mapping**: Each source file has a corresponding test file in the same relative location
- **Easy Navigation**: Know the source path → know the test path
- **Clear Organization**: Tests grouped by service component
- **Shared Fixtures**: `conftest.py` files at multiple levels provide reusable fixtures

#### Running Tests

**AI Service Tests**:
```bash
cd apps/ai-service

# Run all tests
uv run pytest

# Run tests for specific service
uv run pytest tests/ai/graph/services/qa/test_intent.py

# Run all QA service tests
uv run pytest tests/ai/graph/services/qa/

# Run all service tests (excludes legacy test_ai_services.py)
uv run pytest tests/ai/graph/services/

# Run with coverage
uv run pytest --cov=src tests/

# Run with verbose output
uv run pytest -v --tb=short

# Run specific test method
uv run pytest tests/ai/graph/services/qa/test_intent.py::TestIntentService::test_classify_appointment_intent -v
```

**MCP Server Tests** **[NOT IMPLEMENTED]**:
```bash
cd apps/mcp-server
uv run pytest
uv run pytest --cov=src tests/
```

**UI Service Tests** **[NOT IMPLEMENTED]**:
```bash
cd apps/ui-service
uv run pytest
uv run pytest --cov=src tests/
```

**Run All Tests**:
```bash
# From project root
for service in ai-service mcp-server ui-service; do
  echo "Testing $service..."
  (cd apps/$service && uv run pytest)
done
```

### Local Database Setup

```bash
# Create database
createdb db-appointments

# Run initialization scripts
psql -d db-appointments -f database/scripts/00_create_tables.sql
psql -d db-appointments -f database/scripts/01_seed.sql
```

### Common Errors

**"MCP server not reachable"**: 
- Ensure MCP server is running: `docker-compose ps mcp-server`
- Check `MCP_SERVER_URL` in `.env`

**"Database connection refused"**:
- Wait 10-15 seconds after `docker-compose up` for PostgreSQL initialization
- Check `DATABASE_URL` configuration

**"OpenAI API error"**:
- Verify API key is valid
- Check API quota/billing

## License

Proprietary software developed for LumaHealth. All rights reserved.
