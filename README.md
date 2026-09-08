# High-Throughput Async RAG Backend

A production-oriented, backend-only FastAPI service for ingesting documents, creating embeddings, hybrid pgvector/PostgreSQL full-text retrieval, and returning context-grounded answers. It contains no frontend code.

## Architecture

![Implemented RAG architecture](assets/rag-architecture.png)

```text
                    ┌──────────────────────┐
                    │      API Client      │
                    └──────────┬───────────┘
                               ▼
                    │ FastAPI + async middleware
                    └──────────┬───────────┘
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
  Redis token bucket      Redis query cache    Document ingestion
          │                    │                    │
          └────────────────────┴──────────┬─────────┘
                                           ▼
                                 ┌──────────────────┐
                                 │   RAG Service    │
                                 └────────┬─────────┘
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
          Embedding Service      Hybrid Retrieval        LLM Service
                    │                    │                    │
                    │          pgvector cosine + FTS           │
                    ▼                    ▼                    ▼
          configured provider   PostgreSQL + pgvector    validated JSON
          or local test mode    (HNSW + GIN indexes)       response
```

## Stack

Python 3.12, FastAPI, SQLAlchemy 2 async ORM, asyncpg, PostgreSQL 16 with pgvector, Redis, HTTPX, Alembic, pytest, and Locust. All external calls, database access, caching, and rate-limit state are asynchronous.

## Project structure

```text
app/                 FastAPI application, routes, middleware, schemas, services
migrations/          Alembic environment and pgvector/FTS schema migration
tests/unit/          Service-level tests
tests/integration/   Live PostgreSQL + Redis document-to-query test
locust/              Query workload used for benchmarking
scripts/             Optional seed script
```

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

Docker runs migrations before starting the API. Visit `/docs`, `/redoc`, or `/openapi.json`. The API uses Docker service names in `.env` when run in Compose: set `DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/ragdb` and `REDIS_URL=redis://redis:6379/0`.

For a host-native server, keep the example localhost URLs, install requirements, migrate, and run:

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

`EMBEDDING_API_KEY` and `LLM_API_KEY` configure OpenAI-compatible endpoints. With no embedding key, a deterministic local embedding provider is used for development/testing. With no LLM key, the service returns a clearly labelled grounded retrieval result rather than fabricating an answer.

### Configuration

Copy `.env.example` to `.env` for host-native configuration. Do not commit `.env`.

| Variable group | Key settings |
| --- | --- |
| Infrastructure | `DATABASE_URL`, `REDIS_URL`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT` |
| Providers | `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_BASE_URL`, `EMBEDDING_DIMENSION` |
| Ingestion | `MAX_DOCUMENT_CHARS`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `EMBEDDING_CONCURRENCY` |
| Retrieval | `TOP_K`, `VECTOR_WEIGHT`, `KEYWORD_WEIGHT`, `MIN_RETRIEVAL_SCORE` |
| Resilience | `REDIS_CACHE_TTL`, `RATE_LIMIT_CAPACITY`, `RATE_LIMIT_REFILL_RATE` |

### PostgreSQL, pgvector, Redis, and migrations

Compose starts PostgreSQL 16 with the pgvector extension and Redis 7. The `0001_initial` Alembic migration creates `documents`, `document_chunks`, pgvector HNSW cosine index, and PostgreSQL GIN full-text index. Run `alembic upgrade head` for host-native migration; Compose runs the same command before Uvicorn starts. Redis is used for query cache entries and atomic Lua token-bucket state. Both cache and limiter fail open only when Redis is unavailable, allowing the API to remain available while logging the outage.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Dependency-aware health response |
| `POST` | `/api/v1/documents` | Persist, chunk, and embed a document |
| `GET` | `/api/v1/documents/{document_id}` | Read a stored document |
| `POST` | `/api/v1/query` | Retrieve context and produce structured RAG output |

```bash
curl -X POST http://localhost:8000/api/v1/documents -H "content-type: application/json" -d '{"title":"Runbook","content":"Escalate P1 incidents to the on-call manager within fifteen minutes.","metadata":{"team":"ops"}}'
curl -X POST http://localhost:8000/api/v1/query -H "content-type: application/json" -d '{"query":"When is a P1 escalated?","top_k":5}'
curl http://localhost:8000/api/v1/health
```

`POST /api/v1/query` returns `answer`, cited `sources`, and `grounded`. Answers are only sent to the LLM when scores meet `MIN_RETRIEVAL_SCORE`; malformed provider JSON becomes a controlled 502 response.

## Retrieval and operations

The RAG pipeline validates input, chunks documents deterministically, embeds chunks with controlled concurrency, stores embeddings and metadata, performs hybrid retrieval, removes low-score context, asks the strict context-only LLM prompt for JSON, validates the resulting schema, caches the response, and returns cited sources.

Retrieval combines pgvector cosine similarity with `websearch_to_tsquery`/`ts_rank_cd`, using configurable vector and keyword weights. The migration enables pgvector, HNSW cosine indexing, and GIN FTS indexing. Redis response caching hashes normalized query/retrieval configuration and uses a TTL. The token bucket is implemented atomically in Redis Lua, so it works across API instances; cache and limiter fail open if Redis is unavailable to preserve basic query availability.

Configuration is fully documented in `.env.example`, including embedding dimension, pooling, chunking, cache TTL, and rate limits. Never commit `.env`.

## Tests

```bash
pytest
RUN_INTEGRATION=1 DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ragdb pytest tests/integration
```

Unit tests cover chunking, cache miss/hit/failure, Redis token-bucket decisions, insufficient context, local LLM mode, and malformed LLM JSON. Integration services are opt-in so unit tests remain portable.

Verified locally against the running Compose stack:

- Swagger UI: `POST /api/v1/documents` returned **201** with a persisted document; `POST /api/v1/query` returned **200**, `grounded: true`, and cited chunk sources.
- Validation: an invalid document payload returned **422** JSON.
- Infrastructure: PostgreSQL and Redis health checks passed; pgvector extension `0.8.6`, the migration version table, document tables, HNSW vector index, GIN FTS index, and Redis query cache key were verified directly from containers.
- Integration: the Docker-networked document-to-query round trip passed with PostgreSQL, pgvector, and Redis.

## Load testing

```bash
TARGET_HOST=http://localhost:8000 locust -f locust/locustfile.py
```

Target: **100+ RPS**. To measure, seed representative documents, run Locust headless with a chosen user count, spawn rate, and duration (for example `-u 100 -r 20 -t 2m`), then record the Locust-produced RPS, p95 latency, and failure rate. Actual capacity depends on database size/index tuning, provider latency, cache-hit ratio, and infrastructure.

### Measured benchmark (local Docker)

Target: **100+ RPS**

Measured: **304.39 RPS**

| Metric | Actual result |
| --- | ---: |
| Tool | Locust 2.46.5 |
| Endpoint | `POST /api/v1/query` |
| Concurrent users | 200 |
| Spawn rate | 100 users/sec |
| Test duration | 30 seconds |
| Peak RPS | 326.80 |
| Average RPS | 304.39 |
| Total requests | 8,849 |
| Failed requests | 0 |
| Failure percentage | 0.00% |
| Average response time | 581.04 ms |
| Median response time | 570 ms |
| p95 latency | 760 ms |
| p99 latency | 890 ms |
| Maximum latency | 1,068.38 ms |

This is an actual local measurement from the Locust CSV report, not a capacity guarantee. The run used the deterministic local embedding/LLM fallback, an already-warm query cache, Docker Desktop, and a benchmark-only rate-limit configuration of 10,000 tokens capacity/refill per second; production rate-limit defaults remain `100` and `10` respectively. Results will differ with external providers, cold cache, data size, CPU, network, and database tuning.

Benchmark methodology: Locust sent the repository's realistic query payload to the running local API for 30 seconds, ramping to 200 users at 100 users/sec. The final Locust statistics CSV provides average RPS and latency percentiles; its one-second history report provides the 326.80 peak RPS. After the run, the API container was recreated without benchmark overrides. Its active configuration was verified as capacity `100`, refill `10`; a controlled burst produced both `200` and `429` responses, and a later health request returned `200`.

## Known limitations

The bundled provider implementation targets the OpenAI-compatible embedding/chat API shape. Production deployments should supply managed secrets, observability export, backup policy, and an integration test environment. The local embedding mode is for deterministic development only, not semantic-quality production retrieval.
