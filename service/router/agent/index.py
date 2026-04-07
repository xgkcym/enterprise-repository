from fastapi import APIRouter


agent_router = APIRouter(prefix="/agent", tags=["Agent"])

from . import chat, query
