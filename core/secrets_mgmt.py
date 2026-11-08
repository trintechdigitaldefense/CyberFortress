#!/usr/bin/env python3
"""Local secret generation, rotation and permission checks."""

from __future__ import annotations

import os
import re
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Dict, Iterable, Tuple


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    if not isinstance(length, int) or length < 16 or length > 4096:
        raise ValueError("token length must be between 16 and 4096 bytes")
    return secrets.token_urlsafe(length)


def redact(value: object) -> str:
    """Return a non-reversible display mask for a secret."""
    if value is None:
        return "***"
    text = str(value)
    if not text:
        return "***"
    if len(text) <= 8:
        return "***"
    return f"{text[:3]}…{text[-3:]}"


def check_env_permissions(path: Path) -> Tuple[bool, str]:
    """Require an existing secret file to be owner-readable/writable only."""
    target = Path(path)
    try:
        mode = stat.S_IMODE(target.stat().st_mode)
    except OSError as exc:
        return False, f"cannot stat secret file: {exc}"
    if mode & 0o077:
        return False, f"secret file permissions too broad: {mode:o}"
    return True, "secret file permissions are restricted"


def _atomic_private_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        os.chmod(path, 0o600)
    finally:
        temp.unlink(missing_ok=True)


def write_secret_file(name: str, value: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", str(name)):
        raise ValueError("invalid secret name")
    if not isinstance(value, str) or not value:
        raise ValueError("secret value must be a non-empty string")
    directory = Path(os.getenv("CF_SECRETS_DIR", "./secrets")).resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    target = directory / f"{name}.secret"
    _atomic_private_write(target, value + "\\n")
    return target


def rotate_env_keys(path: Path, names: Iterable[str]) -> Dict[str, str]:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    requested = list(dict.fromkeys(str(name) for name in names))
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", name) for name in requested):
        raise ValueError("invalid environment key name")
    rotated = {name: generate_token(32) for name in requested}
    original = target.read_text(encoding="utf-8")
    backup = target.with_name(target.name + ".bak")
    if not backup.exists():
        _atomic_private_write(backup, original)
    lines = original.splitlines()
    seen = set()
    output = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in rotated:
                output.append(f"{key}={rotated[key]}")
                seen.add(key)
                continue
        output.append(line)
    for name, value in rotated.items():
        if name not in seen:
            output.append(f"{name}={value}")
    _atomic_private_write(target, "\\n".join(output) + "\\n")
    return rotated
