#!/usr/bin/env python3
"""CyberFortress defensive controls — rate limits, bind guards, signatures, headers."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import threading
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple

logger = logging.getLogger("cf_defense")

_rl_lock = threading.Lock()
_rl_hits: Dict[str, Deque[float]] = defaultdict(deque)

MAX_BODY = int(os.getenv("CF_MAX_BODY_BYTES", str(256 * 1024)))
RL_WINDOW = float(os.getenv("CF_RATE_LIMIT_WINDOW", "60"))
RL_MAX = int(os.getenv("CF_RATE_LIMIT_MAX", "120"))
PUBLIC_BIND_OK = os.getenv("CF_ALLOW_PUBLIC_BIND", "false").lower() in ("1", "true", "yes")


def rate_limit_allow(key: str, limit: Optional[int] = None, window: Optional[float] = None) -> bool:
    lim = limit if limit is not None else RL_MAX
    win = window if window is not None else RL_WINDOW
    now = time.time()
    with _rl_lock:
        q = _rl_hits[key]
        while q and q[0] < now - win:
            q.popleft()
        if len(q) >= lim:
            return False
        q.append(now)
        return True


def assert_safe_bind(bind: str, service: str) -> str:
    b = (bind or "127.0.0.1").strip()
    public = b in ("0.0.0.0", "::", "[::]")
    if public and not PUBLIC_BIND_OK:
        logger.warning(
            "%s refused public bind %s — using 127.0.0.1 "
            "(set CF_ALLOW_PUBLIC_BIND=true only behind TLS reverse proxy)",
            service,
            b,
        )
        return "127.0.0.1"
    if public:
        logger.warning("%s listening on PUBLIC interface %s — ensure TLS / firewall", service, b)
    return b


def security_headers(handler) -> None:
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header(
        "Content-Security-Policy",
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:",
    )


def read_body_limited(handler, max_bytes: Optional[int] = None) -> Tuple[bytes, Optional[str]]:
    cap = max_bytes if max_bytes is not None else MAX_BODY
    try:
        length = int(handler.headers.get("Content-Length", 0))
    except ValueError:
        return b"", "bad content-length"
    if length < 0 or length > cap:
        return b"", f"body too large or invalid (max {cap})"
    return handler.rfile.read(length), None


def whatsapp_signature_required() -> bool:
    """Require Meta X-Hub-Signature-256 when WhatsApp is enabled or explicitly forced."""
    explicit = os.getenv("CF_WHATSAPP_REQUIRE_SIGNATURE", "").strip().lower()
    if explicit in ("1", "true", "yes"):
        return True
    if explicit in ("0", "false", "no"):
        return False
    return os.getenv("CF_WHATSAPP_ENABLED", "false").lower() in ("1", "true", "yes")


def verify_meta_signature(app_secret: str, body: bytes, signature_header: str) -> bool:
    require = whatsapp_signature_required()
    if not app_secret:
        if require:
            logger.warning("Signature required but CF_WHATSAPP_APP_SECRET not set")
            return False
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1].strip()
    digest = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def safe_under_dir(base: Path, user_path: str) -> Optional[Path]:
    """Canonical path containment — rejects traversal and symlink escapes outside base."""
    try:
        base_r = base.resolve()
        candidate = (base / user_path).resolve()
        candidate.relative_to(base_r)
        return candidate
    except Exception:
        return None


def sanitize_log_field(value: str, max_len: int = 200) -> str:
    s = str(value).replace("\n", " ").replace("\r", " ").replace("\0", "")
    return s[:max_len]


_E164 = re.compile(r"^\+?[1-9]\d{6,14}$")


def is_plausible_e164(num: str) -> bool:
    n = re.sub(r"[\s\-()]", "", str(num or ""))
    return bool(_E164.match(n))


def defense_status() -> dict:
    return {
        "max_body_bytes": MAX_BODY,
        "rate_limit_window_s": RL_WINDOW,
        "rate_limit_max": RL_MAX,
        "allow_public_bind": PUBLIC_BIND_OK,
        "whatsapp_require_signature": whatsapp_signature_required(),
        "containment_live_default_false": os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "false",
        "allow_force": os.getenv("CF_ALLOW_FORCE", "false").lower() in ("1", "true", "yes"),
    }
