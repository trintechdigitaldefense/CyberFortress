from core.defense import (
    rate_limit_allow,
    assert_safe_bind,
    verify_meta_signature,
    safe_under_dir,
    is_plausible_e164,
)
from pathlib import Path
import hmac, hashlib


def test_rate_limit_trips():
    key = "test-rl-unique-xyz"
    assert rate_limit_allow(key, limit=3, window=60)
    assert rate_limit_allow(key, limit=3, window=60)
    assert rate_limit_allow(key, limit=3, window=60)
    assert rate_limit_allow(key, limit=3, window=60) is False


def test_bind_guard():
    assert assert_safe_bind("127.0.0.1", "t") == "127.0.0.1"


def test_meta_sig():
    secret = "testsecret"
    body = b'{"ok":true}'
    dig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_meta_signature(secret, body, f"sha256={dig}")
    assert not verify_meta_signature(secret, body, "sha256=deadbeef")


def test_safe_path(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    assert safe_under_dir(tmp_path, "a.txt") is not None
    assert safe_under_dir(tmp_path, "../etc/passwd") is None


def test_e164():
    assert is_plausible_e164("+18683620679")
    assert not is_plausible_e164("not-a-number")
