from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config import load_json, save_json
from services.agent import AgentService
import json

router = APIRouter()
agent_service = AgentService()

class ChatRequest(BaseModel):
    message: str
    model_id: str | None = None

@router.get("/history")
def get_history():
    data = load_json("chat_history.json")
    return data

@router.delete("/history")
def clear_history():
    save_json("chat_history.json", {"history": []})
    return {"success": True}

@router.post("/")
async def chat(request: ChatRequest):
    data = load_json("models.json")
    model_id = request.model_id or data.get("active_model")
    if not model_id:
        raise HTTPException(status_code=400, detail="No active model configured")

    model_config = next((m for m in data.get("models", []) if m["id"] == model_id), None)
    if not model_config:
        raise HTTPException(status_code=404, detail="Model not found")

    skills_data = load_json("skills.json")
    enabled_skills = [s for s in skills_data.get("skills", []) if s.get("enabled")]

    chat_data = load_json("chat_history.json")
    history = chat_data.get("history", [])
    history.append({"role": "user", "content": request.message})
    save_json("chat_history.json", {"history": history})

    async def generate():
        full_response = ""
        async for chunk in agent_service.stream_chat(
            message=request.message,
            model_config=model_config,
            skills=enabled_skills,
            history=history[:-1]
        ):
            if chunk.get("type") == "text":
                full_response += chunk.get("content", "")
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        history.append({"role": "assistant", "content": full_response})
        save_json("chat_history.json", {"history": history})

    return StreamingResponse(generate(), media_type="text/event-stream")
