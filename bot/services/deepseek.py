import json
from openai import AsyncOpenAI
from bot.config import settings
from bot.models import RouteResult

class DeepSeekClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.model = settings.DEEPSEEK_MODEL

    async def generate(self, user_message: str, system_prompt: str, temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

    async def chat_completion(self, system_prompt: str, messages: list, temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

    async def route(self, user_message: str, case_state: dict) -> RouteResult:
        from bot.utils.formatting import load_prompt
        system = await load_prompt('router/system.txt')
        system += f"\n\nCurrent case state (JSON):\n{json.dumps(case_state, ensure_ascii=False, indent=2)}"
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            return RouteResult(**data)
        except Exception as e:
            return RouteResult(route_to="partner", confidence=0.0, reason_tags=[f"parse_error: {str(e)}"])

deepseek_client = DeepSeekClient()
