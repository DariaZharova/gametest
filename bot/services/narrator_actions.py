def detect_action(text: str) -> dict | None:
    text = text.lower().strip()
    # Поехать в бар
    if any(word in text for word in ['бар', 'bar', 'старый друг']):
        return {'action': 'TRAVEL', 'location': 'bar'}
    # Поехать к Илье
    if any(word in text for word in ['илья', 'крот', 'ilya']):
        return {'action': 'TRAVEL', 'location': 'home_ilya'}
    # Поехать в ресторан
    if any(word in text for word in ['ресторан', 'крест палочек', 'restaurant']):
        return {'action': 'TRAVEL', 'location': 'restaurant'}
    # Квартира жертвы
    if any(word in text for word in ['квартира', 'максим', 'жертва']):
        return {'action': 'TRAVEL', 'location': 'home_maxim'}
    return None
