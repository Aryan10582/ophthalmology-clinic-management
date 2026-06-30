from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, calendar, followups, health, operations, patients, payments, queue, realtime, settings, setup, suggestions, supplies, users, visits

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(setup.router, prefix="/setup", tags=["setup"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(visits.router, prefix="/visits", tags=["visits"])
api_router.include_router(queue.router, prefix="/queue", tags=["queue"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(followups.router, prefix="/followups", tags=["followups"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(supplies.router, prefix="/supplies", tags=["supplies"])
api_router.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])
api_router.include_router(analytics.router, prefix="/analytics-finance", tags=["analytics-finance"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["realtime"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
