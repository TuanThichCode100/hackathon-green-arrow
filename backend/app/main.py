from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import check_database_connection
from app.core.scheduler import start_scheduler

# Import routers safely
routers = []
try:
    from app.modules.communes.router import router as communes_router
    routers.append(communes_router)
    from app.modules.residents.router import router as residents_router
    routers.append(residents_router)
    from app.modules.predictions.router import router as predictions_router
    routers.append(predictions_router)
    from app.modules.stats.router import router as stats_router
    routers.append(stats_router)
    from app.modules.auth.router import router as auth_router
    routers.append(auth_router)
    from app.modules.agent.router import router as agent_router
    routers.append(agent_router)
    from app.modules.notifications.router import router as notif_router
    routers.append(notif_router)
    from app.modules.documents.router import router as docs_router
    routers.append(docs_router)
    from app.modules.disaster_types.router import router as disaster_router
    routers.append(disaster_router)
    from app.modules.users.router import router as users_router
    routers.append(users_router)
    from app.modules.feedback.router import router as feedback_router
    routers.append(feedback_router)
except ImportError as e:
    print(f"Warning: A router could not be imported. {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_available = check_database_connection()
    scheduler = start_scheduler() if database_available else None
    yield
    if scheduler:
        scheduler.shutdown()

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in routers:
    app.include_router(r)

@app.get("/")
def root():
    return {"message": "GreenForecast API is running"}


@app.get("/health")
def health():
    database_available = check_database_connection()
    return {
        "status": "healthy" if database_available else "degraded",
        "api": "available",
        "database": "available" if database_available else "unavailable",
        "schema": "managed_by_alembic",
    }
