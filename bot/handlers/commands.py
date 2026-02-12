from aiogram.types import Message
from bot.db import update_user_state
from bot.services.evidence import get_evidence_text

START_MATERIALS = [
    ("E1", "📄 Протокол осмотра места происшествия"),
    ("E2", "🩸 Заключение СМЭ (оперативная справка)"),
    ("E3", "🗣️ Протокол опроса свидетеля Логинова А.С.")
]

async def handle(message: Message):
    cmd = message.text.lower()
    user_id = message.from_user.id
    
    if cmd == '/start':
        # Инициализируем состояние, выдаём стартовые материалы
        await update_user_state(user_id)  # создаст состояние с E1,E2,E3
        text = (
            "🔍 Вы следователь. Расследуете убийство Максима Лебедева.\n"
            "Доступны первичные материалы:\n"
        )
        for eid, title in START_MATERIALS:
            text += f"\n• {title}"
        text += "\n\nНачните с допроса свидетеля: напишите <b>Артём</b> или <b>@artem</b>."
        await message.answer(text)
    
    elif cmd == '/notes':
        from bot.handlers.partner import handle_partner
        state = await update_user_state(user_id)  # просто чтобы получить
        response = await handle_partner("составь краткую сводку по делу", state, user_id)
        await message.answer(response)
    
    elif cmd == '/evidence':
        from bot.db import get_user_state
        state = await get_user_state(user_id)
        if state and state.open_evidence:
            text = "📁 Открытые улики:\n"
            for eid in state.open_evidence:
                ev_text = get_evidence_text(eid)
                text += f"\n• {ev_text}"
        else:
            text = "Улик пока нет."
        await message.answer(text)
    
    elif cmd == '/help':
        text = (
            "🕵️‍♂️ <b>Детективное агентство</b>\n"
            "Пишите сообщения как при реальном допросе.\n"
            "Чтобы поговорить с конкретным персонажем — начните с @имя или имя: \n"
            "Например: <i>Артём, что ты видел?</i>\n"
            "Чтобы поехать: <i>поехать в бар</i>, <i>идти к Илье</i>\n"
            "Команды: /notes — сводка, /evidence — улики."
        )
        await message.answer(text)
