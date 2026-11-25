from fastapi import APIRouter
from app.api.v1 import health, mock, auth, teams, scores, issues, todos, rocks, meetings

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(mock.router, tags=["Mock"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth & Permissions"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(scores.router, tags=["Scores"])
api_router.include_router(issues.router, tags=["Issues"])
api_router.include_router(todos.router, tags=["Todos"])
api_router.include_router(rocks.router, tags=["Rocks"])
api_router.include_router(meetings.router, tags=["Meetings"])
