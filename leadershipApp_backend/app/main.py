from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.admin import dashboard_router, documents_router, coach_command_router
from app.api.v1.manager import router as manager_router
from app.api.v1.user import chat_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.db.database import ensure_schema_compatibility
from app.services.embedding_service import preload_embedding_model

app = FastAPI(
    title="V2alarry Backend",
    description="AI-powered knowledge base with RAG",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(documents_router, prefix="/api/v1", tags=["Admin"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["Admin"])
app.include_router(coach_command_router, prefix="/api/v1", tags=["Coach Command Center"])
app.include_router(manager_router, prefix="/api/v1/manager", tags=["Manager Observability"])
app.include_router(chat_router, prefix="/api/v1", tags=["User"])


@app.on_event("startup")
async def startup_event():
    preload_embedding_model()
    ensure_schema_compatibility()
    try:
        from app.workers.coaching_workers import CoachingEventConsumers
        consumers = CoachingEventConsumers()
        await consumers.register_handlers()
    except Exception as exc:
        pass

@app.get("/")
async def root():
    return {
        "message": "V2alarry Backend API",
        "version": "2.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "admin_documents": "/api/v1/admin/documents",
            "chat": "/api/v1/chat"
        }
    }

@app.get("/health")
@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "backend-api"}
