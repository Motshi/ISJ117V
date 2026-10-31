from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "smart_cv_platform"

    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "za"

    cv_upload_dir: str = "uploads/cvs"
    max_cv_size_mb: int = 5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
