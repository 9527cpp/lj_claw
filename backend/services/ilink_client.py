"""
iLink (ClawBot) protocol client for WeChat.
Based on reverse-engineered protocol from https://github.com/andyleimc-source/wx-cc-bridge
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
import uuid
from pathlib import Path
from typing import Any, Optional, AsyncGenerator

import httpx

BASE_URL_DEFAULT = "https://ilinkai.weixin.qq.com"
CHANNEL_VERSION = "1.0.2"
LONGPOLL_TIMEOUT = 45.0  # server holds 35s, give HTTP a bit more

# Global state for QR code login flow (used by router + login function)
_qr_state: dict[str, Any] = {
    "qrcode_id": None,
    "login_url": None,
    "status": None,  # None, "pending", "confirmed", "expired", "cancelled"
    "bot_token": None,
    "baseurl": None,
}


async def start_qr_login(client: ILinkClient) -> dict:
    """Initiate QR login, return qrcode data for frontend."""
    global _qr_state
    qr = await client.get_qrcode()
    qrcode_id = qr.get("qrcode") or qr.get("qrcode_str")
    login_url = qr.get("qrcode_img_content") or qr.get("qrcode_img")
    if not qrcode_id:
        raise RuntimeError(f"no qrcode in response: {qr}")

    _qr_state["qrcode_id"] = qrcode_id
    _qr_state["login_url"] = login_url or qrcode_id
    _qr_state["status"] = "pending"
    _qr_state["bot_token"] = None
    _qr_state["baseurl"] = None

    return {
        "qrcode_id": qrcode_id,
        "login_url": _qr_state["login_url"],
        "status": "pending",
    }


async def check_qr_status(client: ILinkClient) -> dict:
    """Check current QR code scan status (call repeatedly from frontend)."""
    global _qr_state
    if not _qr_state["qrcode_id"]:
        return {"status": "no_qr", "message": "No QR code in progress"}

    status = await client.get_qrcode_status(_qr_state["qrcode_id"])
    st = status.get("status")

    if st == "confirmed" and status.get("bot_token"):
        _qr_state["status"] = "confirmed"
        _qr_state["bot_token"] = status["bot_token"]
        _qr_state["baseurl"] = status.get("baseurl", "")
        # Persist token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(
            json.dumps(
                {"bot_token": _qr_state["bot_token"], "baseurl": _qr_state["baseurl"]},
                ensure_ascii=False,
            )
        )
        client.bot_token = _qr_state["bot_token"]
        if _qr_state["baseurl"]:
            client.base_url = _qr_state["baseurl"].rstrip("/")

    elif st in ("expired", "timeout", "cancelled"):
        _qr_state["status"] = "expired"

    return {
        "status": _qr_state["status"],
        "detail": status,
    }


async def get_qr_state() -> dict:
    """Return current QR login state (for frontend polling)."""
    return {
        "qrcode_id": _qr_state.get("qrcode_id"),
        "login_url": _qr_state.get("login_url"),
        "status": _qr_state.get("status"),
        "has_token": bool(_qr_state.get("bot_token")),
    }



def _uin_header() -> str:
    """random uint32 → decimal string → base64 (matches openclaw-weixin 1.0.2 source)"""
    n = struct.unpack(">I", os.urandom(4))[0]
    return base64.b64encode(str(n).encode()).decode()


class ILinkClient:
    def __init__(
        self,
        bot_token: str | None = None,
        base_url: str = BASE_URL_DEFAULT,
    ):
        self.bot_token = bot_token
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=LONGPOLL_TIMEOUT)

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        h = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "X-WECHAT-UIN": _uin_header(),
        }
        if self.bot_token:
            h["Authorization"] = f"Bearer {self.bot_token}"
        return h

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        r = await self._client.get(
            f"{self.base_url}/{path}", params=params, headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    async def _post(self, path: str, body: dict[str, Any]) -> dict:
        r = await self._client.post(
            f"{self.base_url}/{path}", json=body, headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    async def get_qrcode(self, bot_type: int = 3) -> dict:
        return await self._get("ilink/bot/get_bot_qrcode", {"bot_type": bot_type})

    async def get_qrcode_status(self, qrcode: str) -> dict:
        return await self._get("ilink/bot/get_qrcode_status", {"qrcode": qrcode})

    async def getupdates(self, cursor: str = "") -> dict:
        return await self._post(
            "ilink/bot/getupdates",
            {
                "get_updates_buf": cursor,
                "base_info": {"channel_version": CHANNEL_VERSION},
            },
        )

    async def send_text(
        self,
        to_user_id: str,
        context_token: str,
        text: str,
        from_user_id: str = "",
    ) -> dict:
        """Send text message. from_user_id="" and client_id are required for actual delivery."""
        return await self._post(
            "ilink/bot/sendmessage",
            {
                "msg": {
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "client_id": f"lj-claw-{uuid.uuid4()}",
                    "message_type": 2,
                    "message_state": 2,
                    "context_token": context_token,
                    "item_list": [{"type": 1, "text_item": {"text": text}}],
                },
                "base_info": {"channel_version": CHANNEL_VERSION},
            },
        )

    async def send_image(
        self,
        to_user_id: str,
        context_token: str,
        md5: str,
        aes_key: str,
        filesize: int,
        rawsize: int,
        aeskey_base64: str,
        download_param: str,
        from_user_id: str = "",
    ) -> dict:
        """Send image message via encrypted upload."""
        return await self._post(
            "ilink/bot/sendmessage",
            {
                "msg": {
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "client_id": f"lj-claw-{uuid.uuid4()}",
                    "message_type": 2,
                    "message_state": 2,
                    "context_token": context_token,
                    "item_list": [
                        {
                            "type": 2,
                            "image_item": {
                                "md5": md5,
                                "aes_key": aes_key,
                                "filesize": filesize,
                                "rawsize": rawsize,
                                "aeskey_base64": aeskey_base64,
                                "download_param": download_param,
                            },
                        }
                    ],
                },
                "base_info": {"channel_version": CHANNEL_VERSION},
            },
        )

    async def get_typing_ticket(self, to_user_id: str, context_token: str) -> Optional[str]:
        """Get typing ticket for typing indicator."""
        try:
            # Note: This endpoint may not exist in all ilink deployments
            resp = await self._post(
                "ilink/bot/typing",
                {
                    "to_user_id": to_user_id,
                    "context_token": context_token,
                    "base_info": {"channel_version": CHANNEL_VERSION},
                },
            )
            return resp.get("ticket")
        except Exception:
            return None

    async def send_typing(
        self, to_user_id: str, ticket: str, status: int = 1
    ) -> dict:
        """Send typing indicator (status 1=start, 2=stop)."""
        return await self._post(
            "ilink/bot/typing",
            {
                "to_user_id": to_user_id,
                "ticket": ticket,
                "status": status,
                "base_info": {"channel_version": CHANNEL_VERSION},
            },
        )


async def login(
    client: ILinkClient,
    token_path: Path,
) -> bool:
    """Load cached token or run QR-code login flow. Returns True if logged in."""
    if token_path.exists():
        try:
            data = json.loads(token_path.read_text())
            client.bot_token = data["bot_token"]
            if data.get("baseurl"):
                client.base_url = data["baseurl"].rstrip("/")
            print(f"[ilink] reuse token from {token_path}")
            return True
        except (json.JSONDecodeError, KeyError):
            pass

    print("[ilink] No cached token, starting QR login flow...")
    qr = await client.get_qrcode()
    qrcode_id = qr.get("qrcode") or qr.get("qrcode_str")
    login_url = qr.get("qrcode_img_content") or qr.get("qrcode_img")
    if not qrcode_id:
        raise RuntimeError(f"no qrcode in response: {qr}")

    # qrcode_img_content is actually the login URL, not image bytes
    qr_content = login_url or qrcode_id

    try:
        import qrcode as qrlib
        q = qrlib.QRCode(border=1)
        q.add_data(qr_content)
        q.make()
        q.print_ascii(invert=True)
    except ImportError:
        print(f"[ilink] QR code library not installed, showing URL instead")
        print(f"[ilink] Login URL: {qr_content}")

    print(f"[ilink] Please scan QR code above with WeChat to login ClawBot")

    last_dump = None
    while True:
        status = await client.get_qrcode_status(qrcode_id)
        st = status.get("status")
        dump = json.dumps(status, ensure_ascii=False)
        if dump != last_dump:
            print(f"[ilink] QR status → {dump}")
            last_dump = dump
        if st == "confirmed" and status.get("bot_token"):
            client.bot_token = status["bot_token"]
            if status.get("baseurl"):
                client.base_url = status["baseurl"].rstrip("/")
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(
                json.dumps(
                    {"bot_token": client.bot_token, "baseurl": client.base_url},
                    ensure_ascii=False,
                )
            )
            print(f"[ilink] Login success, token saved to {token_path}")
            return True
        await asyncio.sleep(2)


def extract_text(msg: dict) -> str | None:
    """Best-effort text extraction from ilink message."""
    body = msg.get("msg") if isinstance(msg.get("msg"), dict) else msg
    for item in body.get("item_list") or []:
        if item.get("type") == 1:
            return (item.get("text_item") or {}).get("text")
    return None


def extract_meta(msg: dict) -> tuple[str | None, str | None]:
    """Return (from_user_id, context_token) from ilink message."""
    body = msg.get("msg") if isinstance(msg.get("msg"), dict) else msg
    return body.get("from_user_id"), body.get("context_token")