from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    db_url: str = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER','postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD','postgres')}@"
        f"{os.getenv('POSTGRES_HOST','localhost')}:{os.getenv('POSTGRES_PORT','5432')}/"
        f"{os.getenv('POSTGRES_DB','antibiotic_ai')}"
    )

settings = Settings()
