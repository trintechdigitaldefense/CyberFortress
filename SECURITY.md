# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| v0.3.x  | Yes |
| v0.2.x  | Best effort |
| < v0.2  | Best effort |

## Reporting a vulnerability

Email **trintechdigitaldefense@gmail.com** with description, impact, and steps to reproduce.

**Response commitment:** acknowledge within **7 days**. Do not open public issues for active exploits.

## Product security posture

### Defaults
- **MONITORING / dry-run** — `CF_CONTAINMENT_LIVE=false`
- **No force** — `CF_ALLOW_FORCE=false`
- **Local binds** — dashboard/health default `127.0.0.1`; public bind requires `CF_ALLOW_PUBLIC_BIND=true`
- **No secrets in git** — `.env` gitignored

### Runtime defenses (`core/defense.py`)
- Request **rate limiting** (dashboard, health, WhatsApp webhook)
- **Body size caps** on POST
- **Security headers** (CSP, nosniff, frame deny)
- **Meta webhook signature** when `CF_WHATSAPP_APP_SECRET` + `CF_WHATSAPP_REQUIRE_SIGNATURE=true`
- Path-safe helpers for evidence paths

### Containment
- ROE allow-list, circuit breaker, fail-closed watchdog option
- WhatsApp Tier-2 nonce + admin allow-list
- Tamper-evident CMA audit hash chain
- Netadmin preflight before arming

### Operator checklist
```bash
./scripts/defense_check.sh
./scripts/pilot_vm_preflight.sh
```

Production WhatsApp: TLS in front of webhook; do not expose dashboard/health publicly without auth + TLS.

Authorized defensive use only under written agreement with TrinTech Digital Defense.
