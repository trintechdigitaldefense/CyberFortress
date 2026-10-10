# Live WhatsApp HITL + TLS Setup

**TrinTech Digital Defense — CyberFortress**

Meta WhatsApp Cloud API requires **HTTPS** for webhooks.  
CyberFortress keeps the webhook on `127.0.0.1:8089`; TLS terminates at a reverse proxy or tunnel.

---

## Hardened Tier 2 approval flow

1. Platform sends a text message with a **one-time nonce** to every number in `CF_WHATSAPP_ADMINS`.
2. Approver replies **exactly**:
   - `APPROVE <nonce>` to allow, or
   - `DENY <nonce>` to refuse.
3. Webhook checks:
   - Sender is on the admin allow-list (else **DENY-UNKNOWN-SENDER**)
   - Nonce matches the pending request (else **DENY-BAD-NONCE**)
4. No valid reply within `CF_APPROVAL_TIMEOUT` seconds (default **900 = 15 minutes**) → **TIMEOUT-DENY**.
5. Every outcome is written to the CMA audit log with `sender_hash` (SHA-256 prefix), action, target, nonce, and result.

Plain `APPROVE` without a nonce is **rejected**.

### Demo / mock without live Meta credentials

```bash
# in .env
CF_WHATSAPP_MOCK=true
CF_WHATSAPP_ADMINS=+18680000000
CF_APPROVAL_TIMEOUT=120
```

When a Tier 2 action runs, a hint file is written under `logs/whatsapp_pending/`. Approve with:

```bash
python3 -c "from agents.whatsapp_webhook import record_decision; record_decision('REQUEST_ID', 'APPROVE', '+18680000000', 'NONCE')"
```

---

## Architecture

```
Meta Cloud API
    │  HTTPS
    ▼
Caddy / Cloudflare Tunnel / nginx (TLS)
    │  HTTP localhost
    ▼
cf_whatsapp_webhook  →  127.0.0.1:8089
    │  allow-list + nonce check
    ▼
logs/whatsapp_pending/*.decision  (JSON)
    │
    ▼
core/whatsapp_gateway.py (polls; TIMEOUT-DENY default)
```

---

## Configure `.env`

```bash
CF_WHATSAPP_ENABLED=true
CF_WHATSAPP_TOKEN=EAAB...
CF_WHATSAPP_PHONE_NUMBER_ID=1234567890
CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
CF_WHATSAPP_VERIFY_TOKEN=long_random_string_not_default
CF_APPROVAL_TIMEOUT=900
```

Never commit `.env`. Use `chmod 600 .env`.

---

## TLS options

See Caddy (`docker/caddy.whatsapp.example`), Cloudflare Tunnel, or ngrok (pilot only).

---

## Verification checklist

- [ ] Meta webhook verified over HTTPS
- [ ] Tier 2 message includes nonce
- [ ] `APPROVE <nonce>` from registered admin → action allowed
- [ ] Same text from unknown number → DENY-UNKNOWN-SENDER
- [ ] Wrong nonce → DENY-BAD-NONCE
- [ ] No reply → TIMEOUT-DENY in CMA audit log

---

## Security rules

- Webhook bound to `127.0.0.1:8089` only
- Only ROE-named numbers in `CF_WHATSAPP_ADMINS`
- Rotate token if leaked
- Do not expose dashboard/health publicly

---

*See also: docs/OPERATOR_RUNBOOK.md · docs/PILOT_DEPLOYMENT.md · docs/GO_LIVE.md*
