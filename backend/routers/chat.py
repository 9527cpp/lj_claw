from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from config import load_json, save_json
from services.agent import AgentService
from datetime import datetime
import json
import uuid

router = APIRouter()
agent_service = AgentService()

class ChatRequest(BaseModel):
    message: str
    model_id: Optional[str] = None
    session_id: Optional[str] = None
    web_search: bool = False  # Enable web search for this message

class CreateSessionRequest(BaseModel):
    name: Optional[str] = None

class RenameSessionRequest(BaseModel):
    name: str

class SetActiveSessionRequest(BaseModel):
    session_id: str

def get_chat_data():
    return load_json("chat_sessions.json")

def save_chat_data(data):
    save_json("chat_sessions.json", data)

def init_chat_data():
    """Initialize chat data structure if not exists."""
    data = get_chat_data()
    if "sessions" not in data:
        # Migrate old format if exists
        old_data = load_json("chat_history.json")
        if "history" in old_data and old_data["history"]:
            # Create default session from old history
            default_session = {
                "id": str(uuid.uuid4()),
                "name": "默认对话",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": old_data.get("history", [])
            }
            data = {"sessions": [default_session], "active_session": default_session["id"]}
        else:
            data = {"sessions": [], "active_session": None}
        save_chat_data(data)
    return data

@router.get("/sessions")
def list_sessions():
    """List all chat sessions."""
    data = init_chat_data()
    sessions = []
    for s in data.get("sessions", []):
        sessions.append({
            "id": s["id"],
            "name": s["name"],
            "created_at": s["created_at"],
            "updated_at": s["updated_at"],
            "message_count": len(s.get("messages", []))
        })
    return {"sessions": sessions, "active_session": data.get("active_session")}

@router.post("/sessions")
def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    data = init_chat_data()
    session_id = str(uuid.uuid4())
    name = request.name or f"新对话 {len(data['sessions']) + 1}"
    now = datetime.now().isoformat()
    session = {
        "id": session_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    data["sessions"].insert(0, session)  # New sessions at top
    data["active_session"] = session_id
    save_chat_data(data)
    return {"session": {
        "id": session_id,
        "name": name,
        "created_at": now,
        "updated_at": now,
        "message_count": 0
    }, "active_session": session_id}

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Get messages for a specific session."""
    data = init_chat_data()
    session = next((s for s in data["sessions"] if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": {
        "id": session["id"],
        "name": session["name"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "messages": session.get("messages", [])
    }}

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a chat session."""
    data = init_chat_data()
    sessions = data["sessions"]
    session_idx = next((i for i, s in enumerate(sessions) if s["id"] == session_id), None)
    if session_idx is None:
        raise HTTPException(status_code=404, detail="Session not found")

    sessions.pop(session_idx)

    # If deleted session was active, switch to another
    if data.get("active_session") == session_id:
        data["active_session"] = sessions[0]["id"] if sessions else None

    save_chat_data(data)
    return {"success": True, "active_session": data.get("active_session")}

@router.put("/sessions/{session_id}")
def rename_session(session_id: str, request: RenameSessionRequest):
    """Rename a chat session."""
    data = init_chat_data()
    session = next((s for s in data["sessions"] if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session["name"] = request.name
    session["updated_at"] = datetime.now().isoformat()
    save_chat_data(data)
    return {"success": True, "name": request.name}

@router.put("/sessions/{session_id}/active")
def set_active_session(session_id: str):
    """Set a session as the active session."""
    data = init_chat_data()
    session = next((s for s in data["sessions"] if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    data["active_session"] = session_id
    save_chat_data(data)
    return {"success": True, "active_session": session_id}

@router.get("/history")
def get_history():
    """Get history for active session (backwards compatibility)."""
    data = init_chat_data()
    active_id = data.get("active_session")
    if not active_id:
        return {"history": []}

    session = next((s for s in data["sessions"] if s["id"] == active_id), None)
    if not session:
        return {"history": []}
    return {"history": session.get("messages", [])}

@router.delete("/history")
def clear_history():
    """Clear messages in active session."""
    data = init_chat_data()
    active_id = data.get("active_session")
    if active_id:
        session = next((s for s in data["sessions"] if s["id"] == active_id), None)
        if session:
            session["messages"] = []
            session["updated_at"] = datetime.now().isoformat()
            save_chat_data(data)
    return {"success": True}

@router.post("/")
async def chat(request: ChatRequest):
    """Send a message in a session."""
    data = init_chat_data()

    # Determine which session to use
    session_id = request.session_id or data.get("active_session")

    # If no session exists, create one
    if not session_id:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        data["sessions"].insert(0, {
            "id": session_id,
            "name": "新对话",
            "created_at": now,
            "updated_at": now,
            "messages": []
        })
        data["active_session"] = session_id

    session = next((s for s in data["sessions"] if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get model config
    models_data = load_json("models.json")
    model_id = request.model_id or models_data.get("active_model")
    if not model_id:
        raise HTTPException(status_code=400, detail="No active model configured")

    model_config = next((m for m in models_data.get("models", []) if m["id"] == model_id), None)
    if not model_config:
        raise HTTPException(status_code=404, detail="Model not found")

    # Get enabled skills
    skills_data = load_json("skills.json")
    enabled_skills = [s for s in skills_data.get("skills", []) if s.get("enabled")]

    # Get history for this session
    history = session.get("messages", [])

    # Add user message
    session["messages"].append({"role": "user", "content": request.message})
    session["updated_at"] = datetime.now().isoformat()
    save_chat_data(data)

    async def generate():
        nonlocal session
        full_response = ""
        async for chunk in agent_service.stream_chat(
            message=request.message,
            model_config=model_config,
            skills=enabled_skills,
            history=history,
            force_search=request.web_search,
        )::
            if chunk.get("type") == "text":
                full_response += chunk.get("content", "")
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        # Add assistant response
        session["messages"].append({"role": "assistant", "content": full_response})
        session["updated_at"] = datetime.now().isoformat()
        save_chat_data(data)

    return StreamingResponse(generate(), media_type="text/event-stream")
