# Live Meta WhatsApp + HTTPS Webhook

**TrinTech Digital Defense — CyberFortress**

Meta WhatsApp Cloud API requires **HTTPS** for webhooks.  
CyberFortress keeps the webhook on **`127.0.0.1:8089`**; TLS terminates at a reverse proxy or tunnel.

> This document only enables **Tier-2 human approval**.  
> It does **not** turn on live containment. That still needs NDA + ROE + `pilot_signoff.json` + `enable_live_mode.sh`.

---

## Quick path

```bash
./install.sh
./start.sh
./scripts/setup_whatsapp_live.sh   # interactive: tokens, admins, timeout
# Point public HTTPS → 127.0.0.1:8089 (Caddy / Cloudflare Tunnel / ngrok)
# Verify in Meta Console, then:
#   set CF_WHATSAPP_ENABLED=true in .env
./stop.sh && ./start.sh
./scripts/verify_whatsapp.sh
```

---

## Hardened Tier 2 approval flow

1. Platform texts every number in `CF_WHATSAPP_ADMINS` with a **one-time nonce**.
2. Approver replies **exactly**: `APPROVE <nonce>` or `DENY <nonce>`.
3. Webhook checks:
   - Sender is on the admin allow-list (else **DENY-UNKNOWN-SENDER**)
   - Nonce matches (else **DENY-BAD-NONCE**)
4. No valid reply within `CF_APPROVAL_TIMEOUT` (default **900 s / 15 min**) → **TIMEOUT-DENY**.
5. Outcome logged to CMA audit with `sender_hash`, action, target, nonce, result.

### Demo without Meta

```bash
CF_WHATSAPP_MOCK=true
CF_WHATSAPP_ADMINS=+18680000000
```

Use `record_decision(...)` from the mock hint under `logs/whatsapp_pending/`.

---

## 1. Meta Developer Console

1. Create or open a Meta app with the **WhatsApp** product.
2. Add a phone number; copy:
   - **Phone number ID** → `CF_WHATSAPP_PHONE_NUMBER_ID`
   - **Permanent access token** → `CF_WHATSAPP_TOKEN`
3. Webhook callback URL: your public HTTPS endpoint, e.g. `https://webhook.clientdomain.tt/`
4. **Verify token** = same value as `CF_WHATSAPP_VERIFY_TOKEN` in `.env`
5. Subscribe to the **`messages`** field.

---

## 2. Configure `.env`

Prefer `./scripts/setup_whatsapp_live.sh`, or set manually:

```bash
CF_WHATSAPP_ENABLED=true          # only after Meta shows Verified
CF_WHATSAPP_MOCK=false
CF_WHATSAPP_TOKEN=EAAB...
CF_WHATSAPP_PHONE_NUMBER_ID=1234567890
CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
CF_WHATSAPP_VERIFY_TOKEN=long_random_string_not_default
CF_APPROVAL_TIMEOUT=900
```

`chmod 600 .env` — never commit `.env`.

---

## 3. HTTPS options

### A) Caddy (recommended with public DNS)

1. DNS: `webhook.clientdomain.tt` → host public IP  
2. Install Caddy  
3. Use `docker/caddy.whatsapp.example` as `/etc/caddy/Caddyfile`  
4. `sudo systemctl reload caddy`  
5. Ensure webhook is running (`./start.sh`)

### B) Cloudflare Tunnel (no open inbound ports)

```bash
cloudflared tunnel create cf-whatsapp
cloudflared tunnel route dns cf-whatsapp webhook.clientdomain.tt
# ingress → http://127.0.0.1:8089
cloudflared tunnel run cf-whatsapp
```

### C) ngrok (supervised pilot only)

```bash
ngrok http 8089
# Paste https://….ngrok.io into Meta webhook settings
```

---

## 4. Verification checklist

- [ ] `./scripts/verify_whatsapp.sh` passes  
- [ ] Meta Console webhook status **Verified**  
- [ ] Tier 2 message includes nonce  
- [ ] `APPROVE <nonce>` from registered admin works  
- [ ] Unknown number → DENY-UNKNOWN-SENDER  
- [ ] Wrong nonce → DENY-BAD-NONCE  
- [ ] No reply → TIMEOUT-DENY in `logs/cma_audit.jsonl`  
- [ ] Set `whatsapp_tls_verified: true` in `config/pilot_signoff.json`

---

## Security rules

- Webhook bound to **127.0.0.1:8089** only  
- Public surface = TLS proxy only  
- Only ROE-named numbers in `CF_WHATSAPP_ADMINS`  
- Do not expose dashboard (`:8091`) or health (`:8090`) publicly  

---

*See also: docs/templates/ROE_TEMPLATE.md · docs/GO_LIVE.md · docs/OPERATOR_RUNBOOK.md*
