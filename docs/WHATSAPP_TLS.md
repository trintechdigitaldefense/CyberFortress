# Live WhatsApp HITL + TLS Setup

**TrinTech Digital Defense — CyberFortress**

Meta WhatsApp Cloud API requires **HTTPS** for webhooks.  
CyberFortress keeps the webhook on `127.0.0.1:8089`; TLS terminates at a reverse proxy or tunnel.

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
    │
    ▼
logs/whatsapp_pending/*.decision
    │
    ▼
core/whatsapp_gateway.py (polls decisions for Tier 2 APPROVE/DENY)
```

Dashboard and health stay on localhost only — never put them behind public TLS.

---

## 1. Meta Developer Console

1. Create / open a Meta app with **WhatsApp** product.
2. Add a phone number; note:
   - **Phone number ID** → `CF_WHATSAPP_PHONE_NUMBER_ID`
   - **Permanent access token** → `CF_WHATSAPP_TOKEN`
3. Set webhook callback URL to your public HTTPS endpoint, e.g.  
   `https://webhook.clientdomain.tt/`
4. Set **Verify token** to the same value as `CF_WHATSAPP_VERIFY_TOKEN` in `.env`.
5. Subscribe to `messages` field.

---

## 2. Configure `.env`

```bash
CF_WHATSAPP_ENABLED=true
CF_WHATSAPP_TOKEN=EAAB...
CF_WHATSAPP_PHONE_NUMBER_ID=1234567890
CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
CF_WHATSAPP_VERIFY_TOKEN=long_random_string_not_default
CF_APPROVAL_TIMEOUT=300
```

Never commit `.env`. Use `chmod 600 .env`.

---

## 3. Option A — Caddy (recommended for production DNS)

1. Point DNS: `webhook.clientdomain.tt` → server public IP.
2. Install [Caddy](https://caddyserver.com/).
3. Copy `docker/caddy.whatsapp.example` to `/etc/caddy/Caddyfile` and replace the hostname.
4. `sudo systemctl reload caddy`
5. Start webhook:  
   `docker compose -f docker/docker-compose.yml up -d whatsapp_webhook`

Caddy obtains and renews TLS certificates automatically.

---

## 4. Option B — Cloudflare Tunnel (no open inbound ports)

```bash
cloudflared tunnel create cf-whatsapp
cloudflared tunnel route dns cf-whatsapp webhook.clientdomain.tt
# config.yml ingress → http://127.0.0.1:8089
cloudflared tunnel run cf-whatsapp
```

Use the resulting `https://webhook.clientdomain.tt` in Meta Console.

---

## 5. Option C — Pilot only (ngrok)

```bash
ngrok http 8089
# Paste the https://….ngrok.io URL into Meta webhook settings
```

Acceptable for short supervised pilots only — not for ongoing client production.

---

## 6. Verification checklist

- [ ] `curl -s http://127.0.0.1:8089/` responds (or Meta verify challenge succeeds)
- [ ] Meta webhook shows **Verified**
- [ ] Send a test Tier 2 playbook; admin receives interactive APPROVE / DENY
- [ ] Tapping APPROVE creates `logs/whatsapp_pending/<id>.decision` with `APPROVE`
- [ ] Action proceeds only after APPROVE (or times out to DENY)
- [ ] Dashboard (SSH tunnel) shows pending approvals clearing

---

## 7. Security rules

- Webhook container **must** stay on `127.0.0.1:8089`
- Public surface = TLS proxy only
- Rotate `CF_WHATSAPP_TOKEN` if leaked
- Limit `CF_WHATSAPP_ADMINS` to named operators on the ROE
- Do not expose `:8090` / `:8091` publicly

---

## Rollback

```bash
# Disable WhatsApp path
# In .env:
CF_WHATSAPP_ENABLED=false
# Restart services
docker compose -f docker/docker-compose.yml up -d
```

Tier 2 actions will hold/deny until WhatsApp is restored (safe default).

---

*See also: docs/PILOT_DEPLOYMENT.md · docs/OPERATOR_RUNBOOK.md · docs/GO_LIVE.md*
