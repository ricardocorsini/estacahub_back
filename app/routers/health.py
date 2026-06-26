from fastapi import APIRouter

from app.schemas.health import HealthCheckResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:

    return HealthCheckResponse(
        status="ok",
        service="backend",
        version="0.1.0",
    )
