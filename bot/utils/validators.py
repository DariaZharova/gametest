import json
from bot.models import RouteResult

def validate_route_json(json_str: str) -> RouteResult | None:
    try:
        data = json.loads(json_str)
        return RouteResult(**data)
    except:
        return None
