import httpx
import json
import re
from datetime import datetime
from typing import AsyncGenerator, List, Dict, Any, Optional, Tuple
from services.weather import WeatherService
from services.skill_loader import SkillLoader
from services.web_search import get_search_service

# Keywords that indicate a query needs real-time / factual information
REALTIME_QUERY_PATTERNS = [
    r"现在\s*几",
    r"今天\s*几号",
    r"今天\s*是\s*哪",
    r"当前\s*时间",
    r"最新",
    r"现在\s*在世",
    r"还在世",
    r"去世",
    r"去世了",
    r"去世.*吗",
    r"去世.*吗",
    r"还在世吗",
    r"有没有.*最新",
    r"最近.*怎么了",
    r"今天.*新闻",
    r"现在.*消息",
    r"实时",
    r"当前.*状况",
    r"截至?.*最新",
    r"什么时候.*死的",
    r"哪一年.*出生",
    r"今年.*多大",
    r"谁是.*现在",
    r"还?活着",
    r"死了",
    r"死亡",
    r"去世.*吗",
]


def _needs_realtime_info(message: str) -> bool:
    msg = message.lower()
    for pattern in REALTIME_QUERY_PATTERNS:
        if re.search(pattern, msg):
            return True
    return False


class AgentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.weather_service = WeatherService()
        self.skill_loader = SkillLoader()
        self._search = None  # lazy init

    @property
    def search(self):
        if self._search is None:
            self._search = get_search_service()
        return self._search

    async def stream_chat(
        self,
        message: str,
        model_config: Dict[str, Any],
        skills: List[Dict[str, Any]],
        history: List[Dict[str, str]],
        force_search: bool = False,
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

        # Web search: always search if force_search=True, otherwise check patterns
        if force_search or _needs_realtime_info(message):
            yield {"type": "thinking", "content": "正在搜索最新信息..."}
            try:
                # Build a targeted search query from the original message
                search_query = message.strip()
                # Transform conversational/factual queries into better search terms
                if len(search_query) > 20:
                    search_query = search_query.replace("请问", "").replace("一下", "").strip()
                # If asking about whether someone is alive/dead, search with "去世" keyword
                if re.search(r"还在世吗|还?活着|死了|死亡", search_query):
                    person = re.sub(r"还在世吗|还?活着|死了|死亡.*$", "", search_query).strip()
                    search_query = f"{person} 去世"
                elif force_search:
                    # When forced, keep the original query as-is for broad results
                    pass
                search_results = await self.search.search(search_query, num_results=5)
                if search_results:
                    search_context = self._format_search_results(search_results)
                    enhanced_message = f"{search_context}\n\n{enhanced_message}"
            except Exception as e:
                print(f"[agent] web search failed: {e}")

        # Append current date/time context
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        enhanced_message = f"[当前时间：{now}]\n\n{enhanced_message}"

        # Build skill context and inject into message
        skill_context = self.skill_loader.build_skill_context(skills)
        full_message = enhanced_message
        if skill_context:
            full_message = f"{skill_context}\n\n用户问题: {message}"

        if provider == "openai":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._openai_chat(full_message, api_base, api_key, history, skill_context):
                yield chunk
        elif provider == "anthropic":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._anthropic_chat(full_message, api_base, api_key, history, max_tokens, skill_context):
                yield chunk
        else:
            yield {"type": "error", "content": f"Unsupported provider: {provider}"}

        yield {"type": "done"}

    def _format_search_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results as a context block for the model."""
        if not results:
            return ""

        lines = ["[网络搜索结果]"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            url = r.get("url", "").strip()
            snippet = r.get("snippet", "").strip()
            lines.append(f"{i}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
            if url:
                lines.append(f"   来源: {url}")
            lines.append("")

        return "\n".join(lines)

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

        patterns = [
            r'([一-龥]+)天气',
            r'天气\s*([一-龥]+)',
            r'([一-龥]+)的天气',
        ]
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1), day_offset

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
        history: List[Dict[str, str]],
        skill_context: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        import json as json_module
        url = f"{api_base.rstrip('/')}/chat/completions"

        # Build messages with system prompt for skills
        system_content = (
            "你是一个有用的AI助手。注意：如果用户问及时事、新闻、最新数据、生平信息等问题，"
            "请先通过网络搜索获取最新信息再回答，不要仅凭训练数据作答。"
        )
        if skill_context:
            system_content += f"\n\n以下是可供使用的技能指引，请严格按照技能要求执行:\n{skill_context}"

        messages = [{"role": "system", "content": system_content}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4",
            "messages": messages,
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
        max_tokens: int = 4096,
        skill_context: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        import json as json_module
        url = f"{api_base.rstrip('/')}/v1/messages"

        system_content = (
            "你是一个有用的AI助手。注意：如果用户问及时事、新闻、最新数据、生平信息等问题，"
            "请先通过网络搜索获取最新信息再回答，不要仅凭训练数据作答。"
        )
        if skill_context:
            system_content += f"\n\n以下是可供使用的技能指引，请严格按照技能要求执行:\n{skill_context}"

        # Build messages for Anthropic (uses roles differently)
        anthropic_messages = []
        anthropic_messages.extend(history)
        anthropic_messages.append({"role": "user", "content": message})

        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "system": system_content,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "stream": True
        }

        async with self.client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("event: "):
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json_module.loads(data)
                        # MiniMax Anthropic 兼容格式
                        delta = chunk.get("delta", {})
                        delta_type = delta.get("type", "")
                        if delta_type == "text_delta":
                            content = delta.get("text", "")
                            if content:
                                yield {"type": "text", "content": content}
                    except json_module.JSONDecodeError:
                        pass

    async def close(self):
        await self.client.aclose()
        await self.weather_service.close()
        if self._search:
            await self._search.close()