"""
iLink (ClawBot) Bridge Service for lj_claw.

Receives messages from WeChat via iLink protocol and forwards to the agent.
Each chat_id gets its own session and workspace.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Optional

from services.agent import AgentService
from services.ilink_client import (
    ILinkClient,
    extract_meta,
    extract_text,
    login,
)

# Configuration paths
DATA_DIR = Path(__file__).parent.parent / "data"
STATE_DIR = DATA_DIR / "ilink"
TOKEN_PATH = STATE_DIR / "token.json"
CURSOR_PATH = STATE_DIR / "cursor.txt"
SESSIONS_PATH = STATE_DIR / "sessions.json"

# Default workspace root for per-chat Claude sessions
DEFAULT_WS_ROOT = DATA_DIR / "ilink_sessions"

# Timing constants
TYPING_HEARTBEAT_SEC = 3.0
SOFT_NOTICE_SEC = 90.0  # Send "still thinking" if response takes longer than this


def _safe_chat_id(chat_id: str) -> str:
    """Make chat_id safe for use as a directory name."""
    return chat_id.replace("@", "_at_").replace("/", "_").replace(" ", "_").replace("\\", "_")


def default_cwd_for(chat_id: str) -> str:
    """Get default workspace directory for a chat."""
    safe = _safe_chat_id(chat_id)
    return str(DEFAULT_WS_ROOT / safe)


def _load_cursor() -> str:
    return CURSOR_PATH.read_text().strip() if CURSOR_PATH.exists() else ""


def _save_cursor(c: str) -> None:
    CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURSOR_PATH.write_text(c)


class SessionStore:
    """Per-chat session state store."""

    def __init__(self, path: Path):
        self.path = path
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2))

    def get(self, chat_id: str) -> dict[str, Any]:
        return self._data.get(chat_id, {})

    def set(self, chat_id: str, data: dict[str, Any]) -> None:
        self._data[chat_id] = data
        self._save()

    def get_session(self, chat_id: str) -> Optional[str]:
        return self.get(chat_id).get("session_id")

    def set_session(self, chat_id: str, session_id: str) -> None:
        data = self.get(chat_id)
        data["session_id"] = session_id
        self.set(chat_id, data)

    def get_cwd(self, chat_id: str) -> str:
        return self.get(chat_id).get("cwd") or default_cwd_for(chat_id)

    def set_cwd(self, chat_id: str, cwd: str) -> None:
        data = self.get(chat_id)
        data["cwd"] = cwd
        self.set(chat_id, data)


class ILinkBridgeService:
    """iLink bridge service that connects WeChat messages to lj_claw agent."""

    def __init__(self):
        self.client = ILinkClient()
        self.agent = AgentService()
        self.store = SessionStore(SESSIONS_PATH)
        self.locks: dict[str, asyncio.Lock] = {}
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Login and start the bridge."""
        # Ensure we have a valid token
        logged_in = await login(self.client, TOKEN_PATH)
        if not logged_in:
            raise RuntimeError("iLink login failed")

        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_WS_ROOT.mkdir(parents=True, exist_ok=True)

        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        print(f"[ilink-bridge] Started, sessions dir: {DEFAULT_WS_ROOT}")

    async def stop(self) -> None:
        """Stop the bridge."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task
        await self.client.aclose()

    async def _poll_loop(self) -> None:
        """Main long-polling loop."""
        cursor = _load_cursor()
        print(f"[ilink-bridge] Starting poll, cursor={cursor!r}")

        while self._running:
            try:
                data = await self.client.getupdates(cursor)
            except Exception as e:
                print(f"[ilink-bridge] Poll error: {e!r}; retry in 2s")
                await asyncio.sleep(2)
                continue

            if "errcode" in data:
                print(f"[ilink-bridge] Server error: {data}; retry in 2s")
                await asyncio.sleep(2)
                continue

            new_cursor = data.get("get_updates_buf")
            if new_cursor and new_cursor != cursor:
                cursor = new_cursor
                _save_cursor(cursor)

            for msg in data.get("msgs") or []:
                sender, ctx_token = extract_meta(msg)
                text = extract_text(msg)
                if not (sender and ctx_token and text):
                    print(f"[ilink-bridge] Skipped msg: {json.dumps(msg, ensure_ascii=False)[:400]}")
                    continue

                print(f"[ilink-bridge] Msg from {sender}: {text[:120]}")
                # Dispatch without blocking poll loop; per-chat lock serializes
                asyncio.create_task(
                    self._handle_message(sender, ctx_token, text)
                )

    async def _handle_message(
        self,
        chat_id: str,
        ctx_token: str,
        text: str,
    ) -> None:
        """Handle a single message from WeChat."""
        # Handle slash commands
        cmd_reply = await self._handle_command(text, chat_id)
        if cmd_reply is not None:
            try:
                await self.client.send_text(chat_id, ctx_token, cmd_reply)
                print(f"[ilink-bridge] Sent cmd reply to {chat_id}")
            except Exception as e:
                print(f"[ilink-bridge] Send cmd reply error: {e!r}")
            return

        # Get per-chat lock to serialize messages for same chat
        lock = self.locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            state = self.store.get(chat_id)
            cwd = self.store.get_cwd(chat_id)
            session_id = self.store.get_session(chat_id)

            print(f"[ilink-bridge] → Agent {chat_id} cwd={cwd} sid={session_id}")
            t0 = asyncio.get_event_loop().time()

            # Soft notice task - sends "still thinking" if taking too long
            notice_task = asyncio.create_task(self._soft_notice(chat_id, ctx_token))

            try:
                # Collect response from agent
                response_text = ""
                async for chunk in self.agent.stream_chat(
                    message=text,
                    model_config=self._get_model_config(),
                    skills=self._get_enabled_skills(),
                    history=[],  # WeChat sessions are stateless per message for now
                ):
                    if chunk.get("type") == "text":
                        response_text += chunk.get("content", "")

                dt = asyncio.get_event_loop().time() - t0
                print(f"[ilink-bridge] ← Agent {chat_id} ({dt:.1f}s): {len(response_text)} chars")

                if not response_text:
                    response_text = "(empty response)"

                # Save session if new one was created
                # (for now we don't maintain per-chat history, just session_id tracking)

                await self.client.send_text(chat_id, ctx_token, response_text)
                print(f"[ilink-bridge] Sent reply to {chat_id}")

            except Exception as e:
                print(f"[ilink-bridge] Agent error: {e!r}")
                try:
                    await self.client.send_text(
                        chat_id, ctx_token, f"[lj_claw error] {str(e)[:500]}"
                    )
                except Exception:
                    pass
            finally:
                notice_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await notice_task

    async def _soft_notice(self, chat_id: str, ctx_token: str) -> None:
        """Send a 'still thinking' notice if the agent takes too long."""
        try:
            await asyncio.sleep(SOFT_NOTICE_SEC)
            await self.client.send_text(
                chat_id, ctx_token, "(正在思考中，请稍等…)"
            )
            print(f"[ilink-bridge] Sent soft notice to {chat_id}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[ilink-bridge] Soft notice error: {e!r}")

    async def _handle_command(
        self,
        text: str,
        chat_id: str,
    ) -> Optional[str]:
        """Handle slash commands. Returns reply text if command was handled."""
        if not text.startswith("/"):
            return None

        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/help",):
            return (
                "lj_claw Commands:\n"
                "/help - Show this help\n"
                "/new - Start new session\n"
                "/history - Show recent sessions\n"
                "/pwd - Show current workspace\n"
                "/cd <path> - Change workspace\n"
            )

        elif cmd in ("/new", "/clear"):
            state = self.store.get(chat_id)
            state["session_id"] = str(uuid.uuid4())
            self.store.set(chat_id, state)
            return "新会话已创建。"

        elif cmd == "/pwd":
            cwd = self.store.get_cwd(chat_id)
            return f"当前工作目录: {cwd}"

        elif cmd == "/history":
            # For now just show current session
            session_id = self.store.get_session(chat_id)
            cwd = self.store.get_cwd(chat_id)
            return f"Session: {session_id or 'none'}\nWorkspace: {cwd}"

        elif cmd == "/cd":
            if not arg:
                return "Usage: /cd <path>"
            # Make path absolute
            if not os.path.isabs(arg):
                cwd = self.store.get_cwd(chat_id)
                new_cwd = os.path.abspath(os.path.join(cwd, arg))
            else:
                new_cwd = os.path.abspath(arg)
            # Create dir if needed
            os.makedirs(new_cwd, exist_ok=True)
            self.store.set_cwd(chat_id, new_cwd)
            # Reset session for new workspace
            state = self.store.get(chat_id)
            state["session_id"] = str(uuid.uuid4())
            self.store.set(chat_id, state)
            return f"工作目录已切换到: {new_cwd}，新会话已创建。"

        else:
            return f"Unknown command: {cmd}. Type /help for available commands."

    def _get_model_config(self) -> dict[str, Any]:
        """Load active model config from data/models.json"""
        models_data = self._load_json("models.json")
        model_id = models_data.get("active_model")
        if not model_id:
            return {}
        return next(
            (m for m in models_data.get("models", []) if m["id"] == model_id),
            {},
        )

    def _get_enabled_skills(self) -> list[dict[str, Any]]:
        """Load enabled skills from data/skills.json"""
        skills_data = self._load_json("skills.json")
        return [s for s in skills_data.get("skills", []) if s.get("enabled")]

    @staticmethod
    def _load_json(filename: str) -> dict:
        path = DATA_DIR / filename
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, IOError):
            return {}


# Singleton instance
_bridge_service: Optional[ILinkBridgeService] = None


async def get_bridge() -> ILinkBridgeService:
    """Get or create the bridge service singleton."""
    global _bridge_service
    if _bridge_service is None:
        _bridge_service = ILinkBridgeService()
    return _bridge_service


async def start_bridge() -> None:
    """Start the iLink bridge service."""
    bridge = await get_bridge()
    if not bridge._running:
        await bridge.start()


async def stop_bridge() -> None:
    """Stop the iLink bridge service."""
    global _bridge_service
    if _bridge_service:
        await _bridge_service.stop()
        _bridge_service = None