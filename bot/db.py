import json
import aiosqlite
from typing import Optional, Dict, Any
from bot.models import CaseState
from bot.config import settings

DB_PATH = settings.DATABASE_URL.replace('sqlite+aiosqlite:///', '')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_user_state(user_id: int) -> Optional[CaseState]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT state FROM users WHERE user_id = ?',
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = json.loads(row['state'])
            return CaseState(**data)
        return None

async def save_user_state(user_id: int, state: CaseState):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, state, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                state = excluded.state,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, state.model_dump_json()))
        await db.commit()

async def update_user_state(user_id: int, **updates):
    state = await get_user_state(user_id)
    if not state:
        # Создаём новое состояние по умолчанию
        from bot.models import CaseState, NPCState
        state = CaseState(
            mode='MENU',
            open_characters=['artem'],  # Артём открыт сразу
            open_locations=['home_maxim'],
            open_evidence=['E1', 'E2', 'E3'],
            last_active_character=None,
            npc_states={},
            recent_messages=[],
            flags={}
        )
    # Рекурсивное обновление
    new_state = state.model_copy(deep=True)
    for key, value in updates.items():
        if hasattr(new_state, key):
            setattr(new_state, key, value)
    await save_user_state(user_id, new_state)
    return new_state
