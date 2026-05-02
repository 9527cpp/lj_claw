"""
iLink (ClawBot) Router for lj_claw.

Provides management endpoints for the iLink bridge service including QR code login.
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
from services.ilink_client import (
    ILinkClient,
    start_qr_login,
    check_qr_status,
    get_qr_state,
)

router = APIRouter(prefix="/api/ilink", tags=["ilink"])


class ILinkStatusResponse(BaseModel):
    running: bool
    token_exists: bool
    state_dir: str
    sessions_file_exists: bool


class ILinkQRStatusResponse(BaseModel):
    qrcode_id: Optional[str]
    login_url: Optional[str]
    status: Optional[str]
    has_token: bool


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


@router.get("/qr", response_model=ILinkQRStatusResponse)
def get_qr():
    """
    Get current QR code login state.
    If no QR is in progress, returns status='no_qr'.
    Frontend should poll this endpoint every 2-3 seconds.
    """
    state = asyncio.run(get_qr_state())
    return ILinkQRStatusResponse(
        qrcode_id=state.get("qrcode_id"),
        login_url=state.get("login_url"),
        status=state.get("status"),
        has_token=state.get("has_token", False),
    )


@router.post("/qr/start")
async def qr_start():
    """
    Start QR code login flow.
    Returns the QR code content (login URL) for the frontend to render.
    """
    client = ILinkClient()
    try:
        result = await start_qr_login(client)
        return {
            "status": "pending",
            "qrcode_id": result["qrcode_id"],
            "login_url": result["login_url"],
            "message": "QR code generated. Please scan with WeChat.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.aclose()


@router.get("/qr/status")
async def qr_status():
    """
    Check QR code scan status.
    Returns current status: pending, confirmed, expired.
    When status='confirmed', login is complete and token is saved.
    """
    client = ILinkClient()
    try:
        result = await check_qr_status(client)
        return {
            "status": result.get("status"),
            "detail": result.get("detail", {}),
            "message": "Login confirmed" if result.get("status") == "confirmed" else "Waiting for scan...",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await client.aclose()


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