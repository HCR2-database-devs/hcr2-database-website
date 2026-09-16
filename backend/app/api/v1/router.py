from fastapi import APIRouter

from app.api.v1.activity_log import router as activity_log_router
from app.api.v1.admin import router as admin_router
from app.api.v1.admin_community import router as admin_community_router
from app.api.v1.auth import router as auth_router
from app.api.v1.community import router as community_router
from app.api.v1.health import router as health_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.public import router as public_router
from app.api.v1.stats import router as stats_router
from app.api.v1.tippers import router as tippers_router

api_router = APIRouter()
api_router.include_router(activity_log_router)
api_router.include_router(admin_router)
api_router.include_router(admin_community_router)
api_router.include_router(auth_router)
api_router.include_router(notifications_router)
api_router.include_router(community_router)
api_router.include_router(health_router)
api_router.include_router(public_router)
api_router.include_router(stats_router)
api_router.include_router(tippers_router)
