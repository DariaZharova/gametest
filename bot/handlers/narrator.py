import json
from bot.services.deepseek import deepseek_client
from bot.services.evidence import check_location_unlock
from bot.db import update_user_state
from bot.models import CaseState
from bot.utils.formatting import load_prompt

async def handle_travel(action_info: dict, state: CaseState, user_id: int) -> str:
    location_id = action_info.get('location')
    # Проверяем, открыта ли локация
    if location_id not in state.open_locations:
        # Пытаемся открыть
        if not check_location_unlock(location_id, state):
            return "🚫 Эта локация ещё недоступна. Нужно больше улик."
    
    # Формируем системный промпт нарратора
    system = await load_prompt('narrator/system.txt')
    
    # Дополняем данными о локации
    from bot.data.locations import locations
    loc_data = locations.get(location_id, {})
    prompt_data = {
        "action": action_info.get('action', 'TRAVEL'),
        "location": loc_data,
        "available_npcs": loc_data.get('available_npcs', []),
        "new_materials": []  # можно добавить логику
    }
    
    system += f"\n\nInput data:\n{json.dumps(prompt_data, ensure_ascii=False, indent=2)}"
    
    response = await deepseek_client.generate(
        user_message=f"Опиши прибытие в {loc_data.get('name', 'локацию')}.",
        system_prompt=system,
        temperature=0.7
    )
    
    # После прибытия открываем локацию и NPC
    if location_id not in state.open_locations:
        state.open_locations.append(location_id)
    for npc_id in loc_data.get('available_npcs', []):
        if npc_id not in state.open_characters:
            state.open_characters.append(npc_id)
            # Инициализируем состояние NPC
            if npc_id not in state.npc_states:
                from bot.models import NPCState
                state.npc_states[npc_id] = NPCState(stage=0)
    
    state.mode = 'DIALOGUE'
    await update_user_state(user_id, 
                           open_locations=state.open_locations,
                           open_characters=state.open_characters,
                           npc_states=state.npc_states,
                           mode=state.mode)
    
    return response
