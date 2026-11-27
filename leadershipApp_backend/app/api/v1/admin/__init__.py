from .documents import router as documents_router
from .dashboard import router as dashboard_router
from .coach_command_center import router as coach_command_router

__all__ = ["documents_router", "dashboard_router", "coach_command_router"]
