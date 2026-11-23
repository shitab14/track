"""Mock endpoints for manual browser testing prior to full DB integration."""
from fastapi import APIRouter
from app.core.response import ApiResponse

router = APIRouter()

@router.get("/mock/team-summary", response_model=ApiResponse[dict])
def get_mock_team_summary():
    """Mock team summary endpoint for testing in the browser."""
    return ApiResponse.success(
        data={
            "team": {
                "id": "team_lead",
                "name": "Leadership"
            },
            "currentUser": {
                "id": "u1",
                "name": "Avery Admin",
                "role": "admin"
            },
            "summary": {
                "measurablesCount": 5,
                "unsolvedIssuesCount": 3,
                "overdueTodosCount": 1,
                "rocksCount": 5,
                "activeMeeting": False
            },
            "sampleMeasurables": [
                {
                    "id": "m1",
                    "name": "New deals closed",
                    "goal": "at least 10",
                    "latestScore": 8,
                    "status": "off_track"
                },
                {
                    "id": "m2",
                    "name": "Customer churn",
                    "goal": "at most 3.0%",
                    "latestScore": 3.0,
                    "status": "on_track"
                }
            ],
            "sampleIssues": [
                {
                    "id": "i1",
                    "title": "Hiring pipeline is slow",
                    "priority": 5,
                    "owner": "Casey Cho"
                },
                {
                    "id": "i2",
                    "title": "Two key accounts at risk",
                    "priority": 5,
                    "owner": "Blake Brooks"
                }
            ]
        },
        message="Mock team summary fetched successfully"
    )
