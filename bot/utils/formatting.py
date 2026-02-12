import json
import aiofiles
from bot.config import settings

async def load_prompt(path: str) -> str:
    """Загружает промпт из файла в папке prompts."""
    async with aiofiles.open(f'bot/prompts/{path}', 'r', encoding='utf-8') as f:
        return await f.read()

def serialize_state(state) -> str:
    """Сериализует CaseState в JSON, исключая несериализуемые поля."""
    return json.dumps(state.model_dump(), ensure_ascii=False, indent=2, default=str)
