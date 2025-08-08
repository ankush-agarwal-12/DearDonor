from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_KEY: str
    SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET: str  # JWT secret for verifying Supabase JWTs
    SUPABASE_DB_URL: str
    # Supabase Storage Configuration
    SUPABASE_STORAGE_URL: str = "https://wwqtkqvcmmcceskstnyf.supabase.co/storage/v1/s3"
    SUPABASE_STORAGE_REGION: str = "ap-south-1"
    SUPABASE_STORAGE_ACCESS_KEY_ID: str
    SUPABASE_STORAGE_SECRET_ACCESS_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "assets"
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    SMTP_SERVER: str
    SMTP_PORT: int
    ORG_NAME: str
    ORG_ADDRESS: str
    ORG_PHONE: str
    ORG_EMAIL: str
    ORG_WEBSITE: str
    ORG_REGISTRATION_NUMBER: str
    SECRET_KEY: str = "supersecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

def get_settings():
    return Settings()