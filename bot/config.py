from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    TELEGRAM_TOKEN: str = Field(..., env='TELEGRAM_TOKEN')
    DEEPSEEK_API_KEY: str = Field(..., env='DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL: str = Field('https://api.deepseek.com/v1', env='DEEPSEEK_BASE_URL')
    DEEPSEEK_MODEL: str = Field('deepseek-chat', env='DEEPSEEK_MODEL')
    DATABASE_URL: str = Field('sqlite+aiosqlite:///data/detective.db', env='DATABASE_URL')
    LOG_LEVEL: str = Field('INFO', env='LOG_LEVEL')
    MAX_HISTORY_TURNS: int = 6

    class Config:
        env_file = '.env'
        extra = 'ignore'

settings = Settings()
