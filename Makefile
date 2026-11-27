.PHONY: help docker-up docker-down docker-logs prod-up prod-down prod-logs seed test-all test-backend test-evals test-frontend dev-backend dev-worker dev-frontend

help:
	@echo "LeaderShipApp - Execution Commands"
	@echo "--------------------------------------------------------"
	@echo "  make docker-up      Boot development stack via Docker Compose"
	@echo "  make prod-up        Boot production stack (Hostinger VPS)"
	@echo "  make prod-down      Stop production stack"
	@echo "  make prod-logs      Follow production container logs"
	@echo "  make seed           Seed demo users (Manager, Coach, Coachee)"
	@echo "  make test-all       Run all tests (Backend, Evals, Frontend)"
	@echo "  make test-backend   Run Backend unit & contract tests"
	@echo "  make test-evals     Run Socratic LLM evaluation gate"
	@echo "  make test-frontend  Run Frontend typecheck, lint, and Jest"
	@echo "  make dev-backend    Start local FastAPI dev server (:8000)"
	@echo "  make dev-worker     Start local Outbox Daemon worker"
	@echo "  make dev-frontend   Start local Next.js dev server (:3000)"

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

seed:
	@if [ -d "leadershipApp_backend/.venv" ]; then \
		cd leadershipApp_backend && .venv/bin/python scripts/seed_demo_data.py; \
	else \
		docker compose exec api python scripts/seed_demo_data.py; \
	fi

test-all: test-backend test-evals test-frontend
	@echo "\n========================================================"
	@echo "✅ ALL PLATFORM VERIFICATIONS PASSED SUCCESSFULLY!"
	@echo "========================================================"

test-backend:
	cd leadershipApp_backend && .venv/bin/python -m unittest discover -s tests -q

test-evals:
	cd leadershipApp_backend && .venv/bin/python scripts/run_evals.py --mode offline

test-frontend:
	cd leadershipApp_frontend && npm run type-check && npm run lint && npm test -- --runInBand

dev-backend:
	cd leadershipApp_backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-worker:
	cd leadershipApp_backend && .venv/bin/python -m app.workers.outbox_daemon

dev-frontend:
	cd leadershipApp_frontend && npm run dev

