from bot.services.deepseek import deepseek_client
from bot.utils.formatting import load_prompt, serialize_state
from bot.db import update_user_state
from bot.models import CaseState

async def handle_partner(user_message: str, state: CaseState, user_id: int, hint: str = "") -> str:
    system = await load_prompt('partner/system.txt')
    system += f"\n\nCurrent case state:\n{serialize_state(state)}"
    if hint:
        system += f"\n\nAdditional hint: {hint}"
    
    response = await deepseek_client.generate(
        user_message=user_message,
        system_prompt=system,
        temperature=0.5
    )
    return response
