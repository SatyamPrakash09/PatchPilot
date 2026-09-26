from dotenv import load_dotenv
load_dotenv()

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DEVELOPMENT:str = False
    PORT:int = 3000
    
    
    
    class Config:
        env_file=".env"
        env_file_encoding="utf-8"
        case_sensitive=True
        extra="ignore"
        
@lru_cache
def get_config():
    return Settings()