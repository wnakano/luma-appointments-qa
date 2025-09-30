# MCP Server

This MCP server exposes modular services including:

- `database` (legacy DatabaseService) tools: db_query, db_write, db_transaction, db_schema
- `postgres` (PostgresService) tools: pg_query, pg_execute, pg_schema

## Environment Variables

Set one of the following (PostgresService checks `POSTGRES_URL` first):

- `POSTGRES_URL=postgresql://user:pass@host:5432/dbname`
- `DATABASE_URL=postgresql://user:pass@host:5432/dbname`

## Tools

### PostgresService
- `pg_query(query: str, params?: List[str])` - Run a SELECT query (read-only)
- `pg_execute(query: str, params?: List[str])` - Execute INSERT/UPDATE/DELETE
- `pg_schema(table_name?: str)` - Inspect a table or list schema of all public tables

Responses are JSON strings with `status` or `error` fields.

## Health & Tool Discovery

- `GET /mcp/health` - Service health
- `GET /mcp/ready` - Readiness
- `GET /mcp/tools` - Lists tools grouped by service

## Running

The FastMCP app is created in `src/main.py`. Ensure dependencies installed (see `pyproject.toml`) then start via your chosen runner (e.g. uvicorn if exposing ASGI) after setting environment variables.
