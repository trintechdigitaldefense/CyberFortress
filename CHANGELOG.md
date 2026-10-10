# Changelog

## [v0.2.0] — 2026-10-10

### Brief 1 (hardening)
- Removed unverifiable AI/ML claims; rules-driven wording only
- Proprietary LICENSE (All Rights Reserved)
- Hardened WhatsApp Tier 2: allow-list, `APPROVE <nonce>`, TIMEOUT-DENY
- One-command `install.sh` / `start.sh` / `stop.sh`
- NDA + ROE templates; pilot_signoff gate before live mode
- Pricing removed from docs (still building)

### Brief 2 (capability & accuracy) — this release
- **Tamper-evident CMA audit chain** (`prev_hash` + `entry_hash`); `scripts/verify_audit_chain.py`
- **Automated test suite** (`tests/unit`, `tests/integration`); `scripts/run_tests.sh` — 25 tests
- **CI workflow** (`.github/workflows/ci.yml`): pytest + lint hooks
- Pinned core dependency versions in `requirements.txt`
- SECURITY.md added

### Notes
- Dry-run remains default; safety controls unchanged
- Live Meta WhatsApp credentials still human-provided
- GitHub repo description should be updated in UI if still showing AI wording

## [v0.1.0] — 2026-10-09

- Initial pilot MVP: autonomy, fusion, containment drivers, evidence pack, dashboard, watchdog
