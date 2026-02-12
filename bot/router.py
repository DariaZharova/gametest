import json
from bot.db import get_user_state, update_user_state
from bot.services.deepseek import deepseek_client
from bot.services.narrator_actions import detect_action
from bot.handlers import narrator, partner, npc
from bot.models import CaseState, RouteResult

async def route_message(user_message: str, user_id: int) -> str:
    state = await get_user_state(user_id)
    if not state:
        # Создаём дефолтное состояние
        from bot.db import update_user_state
        state = await update_user_state(user_id)

    # Вызываем роутер DeepSeek
    route_result = await deepseek_client.route(user_message, state.model_dump())
    
    # Проверка: если низкая уверенность — отправляем к напарнику
    if route_result.confidence < 0.6:
        route_result.route_to = 'partner'
        route_result.reason_tags.append('low_confidence')

    # Обработка в зависимости от route_to
    if route_result.route_to == 'narrator':
        # Определяем действие и локацию
        action_info = detect_action(user_message)
        if action_info:
            response = await narrator.handle_travel(action_info, state, user_id)
        else:
            # Если не смогли распознать — спросить напарника
            route_result.route_to = 'partner'
            response = await partner.handle_partner(user_message, state, user_id)
    
    elif route_result.route_to == 'partner':
        response = await partner.handle_partner(user_message, state, user_id)
    
    else:
        character_id = route_result.route_to
        # Проверяем, открыт ли персонаж
        if character_id not in state.open_characters:
            response = await partner.handle_partner(
                user_message, state, user_id,
                hint=f"Персонаж {character_id} ещё не доступен. Сначала откройте его."
            )
        else:
            response = await npc.handle_npc(character_id, user_message, state, user_id)
    
    # Обновляем recent_messages (добавляем реплики)
    state.recent_messages.append({"role": "user", "text": user_message})
    state.recent_messages.append({"role": "npc", "name": route_result.route_to, "text": response})
    # Ограничиваем историю
    if len(state.recent_messages) > 10:  # храним 10 последних
        state.recent_messages = state.recent_messages[-10:]
    
    await update_user_state(user_id, recent_messages=state.recent_messages)
    
    return response
