from fastapi import APIRouter

from app.routes.recommendations import router as recommendations_router
from app.routes.vector_db import router as vector_db_router

api_router = APIRouter()
api_router.include_router(vector_db_router)
api_router.include_router(recommendations_router)
