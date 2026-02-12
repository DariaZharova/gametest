from bot.models import CaseState, NPCState
from bot.data.evidence import evidence_conditions
from bot.data.stage_triggers import stage_triggers

async def check_evidence_triggers(state: CaseState, last_message: str, character_id: str) -> CaseState:
    # Упрощённая логика: проходим по условиям открытия улик
    for ev_id, condition in evidence_conditions.items():
        if ev_id in state.open_evidence:
            continue
        if condition(state, last_message, character_id):
            state.open_evidence.append(ev_id)
            # можно добавить системное сообщение в recent_messages
    return state

async def check_stage_triggers(state: CaseState, last_message: str, character_id: str) -> CaseState:
    if character_id not in state.npc_states:
        return state
    npc_state = state.npc_states[character_id]
    current_stage = npc_state.stage
    # Проверяем триггеры для следующей стадии
    for trigger in stage_triggers.get(character_id, []):
        if trigger['stage'] == current_stage + 1 and trigger['condition'](state, last_message):
            npc_state.stage = trigger['stage']
            state.npc_states[character_id] = npc_state
            # можно добавить системное уведомление
    return state

def get_evidence_text(evidence_id: str) -> str:
    from bot.data.evidence import evidence_descriptions
    return evidence_descriptions.get(evidence_id, evidence_id)

def check_location_unlock(location_id: str, state: CaseState) -> bool:
    from bot.data.locations import locations
    loc = locations.get(location_id)
    if not loc:
        return False
    if loc.get('open_by_default'):
        return True
    condition = loc.get('unlock_condition')
    if condition and condition.startswith('evidence.'):
        ev = condition.split('.')[1]
        return ev in state.open_evidence
    return False
