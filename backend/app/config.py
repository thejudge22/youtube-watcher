import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/youtube-watcher.db"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # Issue #41: Optional Authentication
    # Set to true to require login before accessing the application
    # When enabled, AUTH_USERNAME and AUTH_PASSWORD_HASH are required
    auth_enabled: bool = False
    
    # Username for login (only used if auth_enabled is true)
    auth_username: str = ""
    
    # PBKDF2-SHA256 hashed password in hex format (only used if auth_enabled is true)
    # Generate using: ./scripts/generate-password-hash.sh YOUR_PASSWORD
    auth_password_hash: str = ""
    
    # Secret key for JWT signing (auto-generated if not provided)
    jwt_secret_key: str = ""
    
    # JWT token expiration in hours (default: 336 = 14 days)
    jwt_expire_hours: int = 336
    
    def model_post_init(self, __context):
        """Auto-generate JWT secret if not provided."""
        if not self.jwt_secret_key:
            self.jwt_secret_key = secrets.token_urlsafe(32)
    
    class Config:
        env_file = ".env"

settings = Settings()
