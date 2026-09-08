from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(tags=["health"])

@router.get("/health", summary="Liveness and dependency health")
async def health(request: Request):
    database, redis = "ok", "ok"
    try:
        async with request.app.state.session_factory() as session: await session.execute(text("SELECT 1"))
    except Exception: database = "unavailable"
    try:
        if request.app.state.redis: await request.app.state.redis.ping()
        else: redis = "disabled"
    except Exception: redis = "unavailable"
    return {"status": "ok" if database == "ok" else "degraded", "database": database, "redis": redis}
