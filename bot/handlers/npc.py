from bot.services.deepseek import deepseek_client
from bot.utils.formatting import load_prompt, serialize_state
from bot.services.evidence import check_evidence_triggers, check_stage_triggers
from bot.db import update_user_state
from bot.models import CaseState, MessageTurn

async def handle_npc(character_id: str, user_message: str, state: CaseState, user_id: int) -> str:
    # Получаем текущую стадию
    npc_state = state.npc_states.get(character_id)
    if not npc_state:
        from bot.models import NPCState
        npc_state = NPCState(stage=0)
        state.npc_states[character_id] = npc_state
    
    stage = npc_state.stage
    
    # Загружаем промпт
    prompt_path = f'npc/{character_id}/stage_{stage}.txt'
    try:
        system = await load_prompt(prompt_path)
    except FileNotFoundError:
        # Fallback на stage_0
        system = await load_prompt(f'npc/{character_id}/stage_0.txt')
    
    # Добавляем историю диалога с этим персонажем
    context_messages = []
    # Берём последние сообщения из state.recent_messages, где name == character_id
    for msg in reversed(state.recent_messages[-10:]):
        if msg.role == 'npc' and msg.name == character_id:
            context_messages.append({"role": "assistant", "content": msg.text})
        elif msg.role == 'user':
            context_messages.append({"role": "user", "content": msg.text})
    context_messages.reverse()  # в хронологическом порядке
    
    # Вызов DeepSeek
    response = await deepseek_client.chat_completion(
        system_prompt=system,
        messages=context_messages + [{"role": "user", "content": user_message}],
        temperature=0.7
    )
    
    # Обновляем last_active_character
    state.last_active_character = character_id
    
    # Проверяем триггеры улик и смены стадии
    state = await check_evidence_triggers(state, user_message, character_id)
    state = await check_stage_triggers(state, user_message, character_id)
    
    # Сохраняем
    await update_user_state(user_id,
                           last_active_character=state.last_active_character,
                           npc_states=state.npc_states,
                           open_evidence=state.open_evidence,
                           recent_messages=state.recent_messages)
    
    return response
