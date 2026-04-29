import httpx
import json
from typing import AsyncGenerator, List, Dict, Any

class AgentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

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

        if provider == "openai":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._openai_chat(message, api_base, api_key, history):
                yield chunk
        elif provider == "anthropic":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._anthropic_chat(message, api_base, api_key, history):
                yield chunk
        else:
            yield {"type": "error", "content": f"Unsupported provider: {provider}"}

        yield {"type": "done"}

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
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        import json as json_module
        url = f"{api_base.rstrip('/')}/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": history + [{"role": "user", "content": message}],
            "max_tokens": 1024,
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
