from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "CareerLens API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Comma-separated or list of allowed origins
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    MAX_UPLOAD_SIZE_MB: int = 5
    MAX_RESUME_PAGES: int = 15
    MAX_OCR_PAGES: int = 5
    TESSERACT_CMD: Optional[str] = None

    # Supabase Configuration (Optional until user provides them)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # GitHub Integration Configuration (Optional token for higher rate limits)
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_TIMEOUT: int = 10

    # AI Explanation & Assistant Configuration (Phase 8)
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "auto"  # 'gemini', 'openai', 'deterministic', or 'auto'
    AI_MODEL_NAME: str = "gemini-1.5-flash"
    AI_REQUEST_TIMEOUT: int = 15
    AI_MAX_TOKENS: int = 1500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and (self.SUPABASE_ANON_KEY or self.SUPABASE_JWT_SECRET))

settings = Settings()
