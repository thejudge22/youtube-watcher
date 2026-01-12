from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/youtube-watcher.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
