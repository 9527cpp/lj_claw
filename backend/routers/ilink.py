"""
iLink (ClawBot) Router for lj_claw.

Provides management endpoints for the iLink bridge service.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from services.ilink_bridge import (
    start_bridge,
    stop_bridge,
    get_bridge,
    STATE_DIR,
    TOKEN_PATH,
    SESSIONS_PATH,
    DEFAULT_WS_ROOT,
)

router = APIRouter(prefix="/api/ilink", tags=["ilink"])


class ILinkStatusResponse(BaseModel):
    running: bool
    token_exists: bool
    state_dir: str
    sessions_file_exists: bool


class ILinkLoginResponse(BaseModel):
    message: str
    token_path: str


class ILinkSessionResponse(BaseModel):
    chat_id: str
    session_id: Optional[str]
    cwd: str


@router.get("/status", response_model=ILinkStatusResponse)
def get_status():
    """Get iLink bridge status."""
    import asyncio

    bridge = None
    try:
        loop = asyncio.get_running_loop()
        bridge = loop.run_until_complete(get_bridge())
    except RuntimeError:
        pass

    return ILinkStatusResponse(
        running=bridge._running if bridge else False,
        token_exists=TOKEN_PATH.exists(),
        state_dir=str(STATE_DIR),
        sessions_file_exists=SESSIONS_PATH.exists(),
    )


@router.post("/start")
async def start():
    """Start the iLink bridge service (long-poll loop)."""
    try:
        await start_bridge()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop():
    """Stop the iLink bridge service."""
    try:
        await stop_bridge()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
def list_sessions():
    """List all WeChat chat sessions."""
    if not SESSIONS_PATH.exists():
        return {"sessions": []}

    import json
    try:
        data = json.loads(SESSIONS_PATH.read_text())
        sessions = []
        for chat_id, state in data.items():
            sessions.append({
                "chat_id": chat_id,
                "session_id": state.get("session_id"),
                "cwd": state.get("cwd"),
            })
        return {"sessions": sessions}
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{chat_id}")
def delete_session(chat_id: str):
    """Delete session state for a chat_id."""
    import json

    if not SESSIONS_PATH.exists():
        raise HTTPException(status_code=404, detail="Session not found")

    data = json.loads(SESSIONS_PATH.read_text())
    if chat_id not in data:
        raise HTTPException(status_code=404, detail="Session not found")

    del data[chat_id]
    SESSIONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return {"status": "deleted", "chat_id": chat_id}


@router.get("/workspaces")
def list_workspaces():
    """List all workspace directories for WeChat chats."""
    if not DEFAULT_WS_ROOT.exists():
        return {"workspaces": []}

    workspaces = []
    for d in DEFAULT_WS_ROOT.iterdir():
        if d.is_dir():
            workspaces.append({
                "name": d.name,
                "path": str(d),
                "exists": True,
            })
    return {"workspaces": workspaces}


@router.get("/token")
def check_token():
    """Check if ilink token exists (not the actual token value)."""
    return {
        "exists": TOKEN_PATH.exists(),
        "path": str(TOKEN_PATH),
        "message": "Token exists - bridge can connect" if TOKEN_PATH.exists() else "No token - need to login via QR code",
    }


@router.post("/token/clear")
def clear_token():
    """Clear the stored token (requires re-login via QR code)."""
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
        return {"status": "token_cleared"}
    return {"status": "no_token_existed"}