import httpx
import json
import re
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple
from services.weather import WeatherService

class AgentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.weather_service = WeatherService()

    async def stream_chat(
        self,
        message: str,
        model_config: Dict[str, Any],
        skills: List[Dict[str, Any]],
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        provider = model_config.get("provider", "openai")
        api_base = model_config.get("api_base")
        api_key = model_config.get("api_key")
        max_tokens = model_config.get("max_tokens", 4096)

        # Check if weather skill is enabled
        weather_skill = next((s for s in skills if s.get("id") == "weather" and s.get("enabled")), None)
        weather_info = None

        if weather_skill:
            location, day_offset = self._extract_location_and_day(message)
            if location:
                weather_config = weather_skill.get("config", {})
                weather_api_key = weather_config.get("api_key")
                weather_api_host = weather_config.get("api_host", "devapi.qweather.com")
                if weather_api_key:
                    yield {"type": "thinking", "content": "正在查询天气..."}
                    weather_info = await self.weather_service.get_weather(location, weather_api_key, weather_api_host, day_offset)
                else:
                    weather_info = {"success": False, "error": "未配置天气API密钥"}

        # Build enhanced message with weather info
        enhanced_message = message
        if weather_info and weather_info.get("success"):
            weather_text = self._format_weather(weather_info)
            enhanced_message = f"{message}\n\n[天气信息]: {weather_text}"
        elif weather_info and not weather_info.get("success"):
            weather_text = f"查询失败: {weather_info.get('error')}"
            enhanced_message = f"{message}\n\n[天气信息]: {weather_text}"

        if provider == "openai":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._openai_chat(enhanced_message, api_base, api_key, history):
                yield chunk
        elif provider == "anthropic":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._anthropic_chat(enhanced_message, api_base, api_key, history, max_tokens):
                yield chunk
        else:
            yield {"type": "error", "content": f"Unsupported provider: {provider}"}

        yield {"type": "done"}

    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from user message."""
        location, _ = self._extract_location_and_day(message)
        return location

    def _extract_location_and_day(self, message: str) -> Tuple[Optional[str], int]:
        """Extract location and day offset (0=today, 1=tomorrow, 2=day after tomorrow)."""
        day_offset = 0
        if "明天" in message or "tomorrow" in message.lower():
            day_offset = 1
        if "后天" in message:
            day_offset = 2

        # Pattern for Chinese: "上海天气", "北京天气怎么样", "上海明天天气"
        patterns = [
            r'([一-龥]+)天气',
            r'天气\s*([一-龥]+)',
            r'([一-龥]+)的天气',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1), day_offset

        # Pattern for English: "weather in Shanghai", "Shanghai weather tomorrow"
        match = re.search(r'weather\s+(?:in|at)?\s*(\w+)', message, re.IGNORECASE)
        if match:
            return match.group(1), day_offset

        return None, 0

    def _format_weather(self, weather: Dict[str, Any]) -> str:
        """Format weather data into readable text."""
        return (
            f"{weather.get('location', 'Unknown')}: "
            f"{weather.get('condition', 'N/A')}, "
            f"温度{weather.get('temp', 'N/A')}°C, "
            f"体感{weather.get('feels_like', 'N/A')}°C, "
            f"{weather.get('wind', 'N/A')}, "
            f"湿度{weather.get('humidity', 'N/A')}%, "
            f"能见度{weather.get('vis', 'N/A')}km"
        )

    async def _openai_chat(
        self,
        message: str,
        api_base: str,
        api_key: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        import json as json_module
        url = f"{api_base.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4",
            "messages": history + [{"role": "user", "content": message}],
            "stream": True
        }

        async with self.client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json_module.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield {"type": "text", "content": content}
                    except json_module.JSONDecodeError:
                        pass

    async def _anthropic_chat(
        self,
        message: str,
        api_base: str,
        api_key: str,
        history: List[Dict[str, str]],
        max_tokens: int = 4096
    ) -> AsyncGenerator[Dict[str, Any], None]:
        import json as json_module
        url = f"{api_base.rstrip('/')}/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": history + [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "stream": True
        }

        async with self.client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json_module.loads(data)
                        content = chunk.get("delta", {}).get("text", "")
                        if content:
                            yield {"type": "text", "content": content}
                    except json_module.JSONDecodeError:
                        pass

    async def close(self):
        await self.client.aclose()
        await self.weather_service.close()