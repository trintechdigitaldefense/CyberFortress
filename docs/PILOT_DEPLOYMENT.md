# CyberFortress Pilot Deployment Checklist

**TrinTech Digital Defense — Protected Asset**

Use this checklist before placing CyberFortress on any client network.

---

## 1. Legal & Authorization

- [ ] Signed NDA in place
- [ ] Signed Rules of Engagement (ROE) that explicitly authorizes:
  - Network monitoring
  - Automated containment actions (list which ones)
  - Credential rotation if used
  - Out-of-band WhatsApp notifications/approvals
- [ ] Client has designated primary + secondary WhatsApp admin numbers
- [ ] Written confirmation that TT Computer Misuse Act justifications are acceptable to the client

---

## 2. Environment Preparation

- [ ] Linux host (Ubuntu 22.04+ recommended) with Docker
- [ ] Network placement allows visibility of target assets
- [ ] Firewall rules permit CyberFortress outbound to WhatsApp Cloud API (if used)
- [ ] Time synchronized (NTP)

---

## 3. Configuration

```bash
# Mandatory safety
export CF_CONTAINMENT_LIVE=false          # keep dry-run until ready

# WhatsApp (production)
export CF_WHATSAPP_ENABLED=true
export CF_WHATSAPP_TOKEN=...
export CF_WHATSAPP_PHONE_NUMBER_ID=...
export CF_WHATSAPP_ADMINS=+1868xxxxxxxx,+1868yyyyyyyy
export CF_WHATSAPP_VERIFY_TOKEN=your_verify_token

# Identity (choose one)
export CF_IDENTITY_PROVIDER=local_linux   # or ldap / azure_ad

# Optional live telemetry
export CF_SENTINEL_API_URL=http://sentinel:port/api/alerts
export CF_MIRAGE_API_URL=http://mirage:port/api/events
```

- [ ] All secrets stored outside the repo (env file or secrets manager)
- [ ] `.env` or equivalent is **not** committed

---

## 4. Pre-Flight Tests (Dry-Run)

```bash
# Health
python3 -m agents.healthcheck

# List playbooks
python3 playbooks/execute.py --list

# Safe dry-run actions
python3 playbooks/execute.py --action block_ip --target 203.0.113.50 --force
python3 playbooks/execute.py --action isolate_endpoint --target 10.0.5.12 --force

# Circuit breaker
python3 playbooks/breaker.py status

# Evidence pack
python3 playbooks/evidence.py --client "PILOT-CLIENT" --engagement ENG-PILOT-001
```

- [ ] All dry-run commands succeed
- [ ] Evidence pack generated cleanly
- [ ] Circuit breaker remains CLOSED

---

## 5. WhatsApp Webhook (if using live HITL)

- [ ] Public HTTPS endpoint (ngrok, Cloudflare Tunnel, or reverse proxy)
- [ ] Meta Developer Console webhook points to `https://your-host/webhook`
- [ ] Verify token matches `CF_WHATSAPP_VERIFY_TOKEN`
- [ ] Test APPROVE / DENY buttons received and recorded

```bash
python3 -m agents.whatsapp_webhook
```

---

## 6. Go-Live Decision

Only after the above:

```bash
export CF_CONTAINMENT_LIVE=true
```

- [ ] Operator is monitoring for the first 24–48 hours
- [ ] Client contacts are briefed on what WhatsApp messages mean
- [ ] Rollback plan agreed (set `CF_CONTAINMENT_LIVE=false` + breaker trip)

---

## 7. Ongoing

- [ ] Daily or on-demand Evidence Pack generation
- [ ] Weekly review of circuit-breaker trips and held actions
- [ ] Keep ROE and admin numbers up to date

---

*Defend. Detect. Dominate.*  
TrinTech Digital Defense
