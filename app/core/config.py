from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TalentBridge"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    DATABASE_URL: str = "sqlite:///./talentbridge.db"  # Switch to PostgreSQL in prod
    
    class Config:
        case_sensitive = True

settings = Settings()

