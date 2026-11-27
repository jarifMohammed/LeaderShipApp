# LeaderShipApp: Enterprise AI Leadership Coaching Platform

> **Tier-1 Engineering Standard**: Built with non-directive Socratic coaching intelligence, OpenTelemetry W3C distributed tracing, per-conversation Redis concurrency locks, transactional outbox event relay with PostgreSQL `SKIP LOCKED`, role-separated observability (Coach vs. Platform Owner), and one-command Docker reproducibility.

---

## 🌟 Architecture & System Overview

LeaderShipApp separates coaching clinical workflows from platform engineering unit economics through strict role boundaries:

```
                                  TIER-1 ARCHITECTURE OVERVIEW

  [ EXECUTIVE COACHEE (USER) ]                    [ LEADERSHIP COACH (ADMIN) ]             [ PLATFORM OWNER (MANAGER) ]
               │                                               │                                        │
  Next.js 16 Client (/coaching/*)                Next.js 16 Client (/dashboard/users)    Next.js 16 (/dashboard/manager)
               │ (SSE Stream)                                  │                                        │
               ▼                                               ▼                                        ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                    FASTAPI BACKEND & RBAC GATEWAY                                           │
  │  • require_user / require_admin / require_manager Auth Guards & JWT Token Validation                        │
  │  • Dynamic Coach-Client Assignment Scoping (Coaches only see assigned coachees)                            │
  │  • Diagnostics Sanitizer: Strips USD cost & span latency for ADMIN; serves raw telemetry for MANAGER       │
  └──────────────────────────────────────┬──────────────────────────────────────────────────────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 1. PER-CONVERSATION CONCURRENCY LOCK          │
                 │    • Redis lock:conv:{id} (TTL 60s)           │
                 │    • Fast 409 Conflict if turn in-flight      │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 2. ENTERPRISE SAFETY & INPUT GUARDRAILS       │
                 │    • PII Sanitizer: Masks SSNs, CCs, emails   │
                 │    • Guardrails: Blocks injection & overrides │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 3. OPENTELEMETRY TRACE CONTEXT PROPAGATION    │
                 │    • Generates W3C traceparent & root span   │
                 │    • Child Spans: context_retrieval, ttft,    │
                 │      socratic_guard, generation_stream        │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 4. SOCRATIC CHAT WORKFLOW (LangGraph)         │
                 │    • Load 360° Client Dossier & Active Goals  │
                 │    • Qdrant Vector Retrieval (2.5s Timeout    │
                 │      circuit breaker -> fallback if slow)     │
                 │    • Local Jinja2 Prompt Templates Loader     │
                 │    • Non-Directive ICF Socratic Directives    │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 5. STREAMING GENERATION & METERING            │
                 │    • Live SSE stream with TTFT tracking       │
                 │    • Heartbeat keep-alives (15s ping)         │
                 │    • Deterministic USD Pricing Engine         │
                 │    • Persist turn_diagnostics with telemetry  │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │ 6. TRANSACTIONAL OUTBOX PATTERN               │
                 │    • Writes outbox_events in DB transaction   │
                 │    • Guaranteed at-least-once delivery        │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                               DEDICATED OUTBOX DAEMON WORKER (Background)                                   │
  │  • Polls outbox_events with SELECT ... FOR UPDATE SKIP LOCKED (zero worker deadlocks or race conditions)   │
  │  • Consumer Idempotency Keys (consumer_idempotency_keys prevents duplicate execution)                       │
  │  • Async Handlers: Client Memory Profile extraction, Goal Tracking, Transcript Ingestion                   │
  │  • Speaker Attribution: Distinguishes [Coach] suggestions from [Client] commitments                         │
  └─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart: One-Command Execution (Docker Compose)

The entire platform—databases, caching, vector engine, API, background worker, and frontend—boots with a single command:

```bash
docker compose up --build
```

### Accessing the Platform
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Seeding Demo Accounts & Data
Run the automated seed script to populate test accounts and mock telemetry:
```bash
docker compose exec api python scripts/seed_demo_data.py
```

### Pre-Configured Demo Credentials
| Role | Email | Password | Landing Page | Key Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Manager (Platform Owner)** | `manager@company.com` | `Password123!` | `/dashboard/manager` | Financial unit economics, USD cost/turn, token burn, latency spans (p50/p95 TTFT), Outbox health, live trace inspector. |
| **Coach (Admin)** | `coach@company.com` | `Password123!` | `/dashboard/users` | Assigned coachee 360° dossiers, goals, transcript upload with speaker attribution, Socratic chat insights (costs/tokens sanitized). |
| **Coachee (User)** | `coachee@company.com` | `Password123!` | `/coaching/new` | Live non-directive Socratic coaching chat with Jess, goal formation, action commitment reflection. |

---

## 💻 Local Development Setup (Without Docker)

### 1. Prerequisites
- **Python**: 3.12+
- **Node.js**: 20+ (LTS) & npm 10+
- **PostgreSQL 16**: Running on port `5432` with database `leadership_app`
- **Redis 7**: Running on port `6379`
- **Qdrant**: Running on port `6333`

### 2. Backend Setup
```bash
cd leadershipApp_backend

# 1. Activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env to set your database, Redis, and OpenAI API key

# 4. Run database migrations
alembic upgrade head

# 5. Seed demo data
python scripts/seed_demo_data.py

# 6. Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Background Outbox Worker
In a separate terminal window:
```bash
cd leadershipApp_backend
source .venv/bin/activate
python -m app.workers.outbox_daemon
```

### 4. Frontend Setup
In a third terminal window:
```bash
cd leadershipApp_frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env.local

# 3. Start Next.js development server
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to interact with the app.

---

## 🧪 Verification & Test Suites

Run the full verification suite across backend, evals, and frontend:

```bash
# Run all tests via Makefile
make test-all

# Or run individually:
# 1. Backend Unit & Contract Tests (289 tests)
cd leadershipApp_backend && .venv/bin/python -m unittest discover -s tests -q

# 2. Socratic Quality & Non-Directiveness Eval Gate (25 golden scenarios)
cd leadershipApp_backend && .venv/bin/python scripts/run_evals.py --mode offline

# 3. Frontend Type-Check, Lint, and Unit Tests (49 tests)
cd leadershipApp_frontend && npm run type-check && npm run lint && npm test -- --runInBand
```

---

## 🔍 How Everything Works Under the Hood

### 1. Live Socratic Chat & Concurrency Safety
- When a user submits a prompt, `ConversationLock` acquires a Redis key `lock:conv:{id}` with a 60-second TTL.
- If the user double-clicks or triggers an overlapping prompt, the server immediately returns `409 Conflict` (`"Jess is still responding to your previous message"`), preventing duplicate API spend or hallucinated interleavings.
- Upon completion or failure, the lock is freed in a `finally` block.

### 2. Socratic Non-Directive Intelligence
- The core prompt is decoupled into [`socratic_coach_system.jinja2`](file:///home/jarif/Desktop/Projects/LeaderShipApp/leadershipApp_backend/app/prompts/templates/socratic_coach_system.jinja2).
- Rather than prescribing advice, Jess asks high-leverage questions to move the coachee through the ICF GROW framework (Goal $\to$ Reality $\to$ Options $\to$ Will).
- Every response undergoes pre-LLM PII masking (SSNs, emails, credit cards) and prompt injection detection.

### 3. Fault-Tolerant Hybrid Retrieval
- The workflow queries Qdrant vector database with an enforced `2.5s` circuit breaker timeout.
- If Qdrant experiences latency spikes or network timeouts, the system flags `rag_degraded = True` and safely completes the coaching turn utilizing the user's PostgreSQL 360° dossier and active goals without crashing.

### 4. Transactional Outbox Event Relay
- When turn state updates, the backend writes an `outbox_events` record inside the same atomic database transaction as the message.
- The dedicated `OutboxDaemon` worker polls `outbox_events` using PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED`, guaranteeing that multiple worker instances never process the same event concurrently.
- Consumer handlers verify execution via `consumer_idempotency_keys` to ensure strictly at-least-once delivery with exactly-once execution.

### 5. Role-Separated Telemetry & Unit Economics
- Every LLM completion tracks exact token usage (`prompt_tokens`, `completion_tokens`) and computes USD cost using deterministic model pricing (`gpt-4o`: \$2.50 / 1M prompt, \$10.00 / 1M completion).
- When a Coach (`ADMIN`) inspects chat history, `turn_diagnostics` is sanitized to strip USD costs and raw millisecond timings, presenting only coaching-relevant insights.
- When a Platform Owner (`MANAGER`) logs into `/dashboard/manager`, they access full unit economics: total USD spend, average cost per turn, p50/p95 TTFT, and distributed trace drilldowns.

