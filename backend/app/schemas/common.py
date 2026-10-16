from pydantic import BaseModel, Field
from typing import Optional, Any

class HealthResponse(BaseModel):
    status: str = Field(..., description="Operational status of backend service")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")
    components: Optional[dict] = Field(None, description="Detailed component readiness and subsystem statuses")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error explanation")
    error_code: Optional[str] = Field(None, description="Internal error code")

class PendingImplementationResponse(BaseModel):
    status: str = Field(default="pending_implementation", description="Lifecycle status")
    endpoint: str = Field(..., description="Target endpoint")
    message: str = Field(..., description="Explanation of roadmap phase")
    scheduled_phase: str = Field(..., description="Target implementation phase")
    validated_input: Optional[Any] = Field(None, description="Summary of validated request fields")
