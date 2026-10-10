# FIXES_VERIFIED — CyberFortress pilot MVP

**Date:** 2026-10-10  
**Repo:** github.com/trintechdigitaldefense/CyberFortress  
**Verifier:** automated hardening pass (Tasks 1–5)

---

## Demo flow results (fresh clone)

| Step | Result | Notes |
|------|--------|-------|
| 1. `./install.sh` | PASS | After splitting core deps from optional `ldap3`/`msal` (PyPI 502 on optional packages no longer fails install) |
| 2. `./start.sh local` | PASS | All 7 local processes UP |
| 3. Dashboard `:8091` / Health `:8090` | PASS | HTTP 200; `containment_live: false` |
| 4. Sample Sentinel/Mirage fusion | PASS | `reverse_shell_detected` → **HIGH** → `block_ip`; `decoy_trigger` → **HIGH** → `isolate_endpoint` |
| 5. Tier 1 `block_ip` dry-run + CMA log | PASS | iptables dry-run lines + `TT_CMA_TAG` audit entry |
| 6. Evidence Pack ZIP | PASS | Report, Full_Audit.json, Raw CMA jsonl, MANIFEST.sha256 |
| 7. Tier 2 WhatsApp hardened path | PASS (mock) | Unknown sender denied; valid admin + nonce → APPROVE; no reply → **TIMEOUT-DENY** logged |
| 8. `./stop.sh` + status | PASS | All PIDs stopped |

---

## What was broken and what changed

### 1. AI / ML overclaims (Task 1)
- **Broken:** `agents/threat_hunting_agent.py`, `docs/PLAYBOOK.md`, `requirements.txt` claimed AI-driven hunting.
- **Fix:** Rewrote as rules-driven telemetry / automation. README had no AI claim. HOW_TO_SELL explicitly lists AI as something **not** to promise.
- **GitHub description:** attempted via `gh repo edit` (see human follow-up if auth limited).

### 2. LICENSE missing (Task 2)
- **Fix:** Added root `LICENSE` — proprietary All Rights Reserved, TrinTech Digital Defense 2026.

### 3. WhatsApp Tier 2 too weak (Task 3)
- **Broken:** Button-only APPROVE; no sender allow-list enforcement; no nonce; timeout was 300s and not logged as TIMEOUT-DENY.
- **Fix:**
  - Approver must be in `CF_WHATSAPP_ADMINS`
  - Reply format: `APPROVE <nonce>` / `DENY <nonce>`
  - Default timeout **900s (15 min)** → audit `TIMEOUT-DENY`
  - Decisions store `sender_hash` + `nonce_ok`
  - `CF_WHATSAPP_MOCK=true` for demos without Meta credentials

### 4. Escalation under-classified reverse shell (demo)
- **Broken:** `reverse_shell_detected` escalated to LOW.
- **Fix:** High keywords include `reverse_shell` / `shell` → HIGH + recommend `block_ip`.

### 5. `./install.sh` failed when optional PyPI packages 502 (demo)
- **Broken:** Full `requirements.txt` install failed on `ldap3` network errors.
- **Fix:** Core-only requirements; optional ldap3/msal best-effort in `install.sh`.

### 6. Pricing anchors missing (Task 5)
- **Fix:** Pilot **$2,000** fixed; Managed **$3,000/mo** USD; TT$ on request.

---

## Still needs a human

1. **Live Meta WhatsApp credentials** + public HTTPS webhook for production HITL (mock path verified only).
2. Confirm **GitHub repository description** text if `gh` auth was unavailable:  
   `Automated threat detection and tiered response for Caribbean enterprises — TrinTech Digital Defense (Trinidad & Tobago)`
3. Client **ROE / NDA / pilot_signoff.json** before any live containment.
4. Optional: install `ldap3` / `msal` when directory identity is required.

---

## Safety controls preserved

- `CF_CONTAINMENT_LIVE=false` default  
- Force gate, ROE allow-list, circuit breaker, watchdog fail-closed, go-live sign-off gate  
- No secrets committed  
