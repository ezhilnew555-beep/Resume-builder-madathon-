from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProfileResponse(BaseModel):
    id: str = Field(..., description="Unique user identifier matching auth.users")
    email: Optional[str] = Field(None, description="Candidate email address")
    full_name: Optional[str] = Field(None, description="Full name of student")
    education: Optional[str] = Field(None, description="Educational background / university")
    target_role: Optional[str] = Field(None, description="Target career role")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=150)
    education: Optional[str] = Field(None, max_length=255)
    target_role: Optional[str] = Field(None, max_length=150)

class GitHubConnectRequest(BaseModel):
    username_or_url: str = Field(..., min_length=1, max_length=255, description="GitHub username or public profile URL")

class ProfileConnectionUpdate(BaseModel):
    platform_id: str = Field(..., description="Platform identifier (github, leetcode, etc.)")
    username_or_url: str = Field(..., max_length=500, description="Profile username or URL")
    status: Optional[str] = Field("connected", description="Connection status")

class MetricPreviewItem(BaseModel):
    label: str
    value: str

class ProfileConnectionItem(BaseModel):
    id: str
    name: str
    icon_name: str
    description: str
    status: str  # 'connected', 'not_connected', 'partially_connected', 'inaccessible', 'rate_limited'
    username_or_url: str
    last_synced: Optional[str] = None
    retrieval_status: str = "Active"
    metrics_preview: List[MetricPreviewItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProfileConnectionsResponse(BaseModel):
    connections: List[ProfileConnectionItem] = Field(default_factory=list)
    total_connected: int = 0
    message: str = "Profile connections retrieved."
