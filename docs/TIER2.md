# Tier-2 guarded response

High-impact actions **never auto-execute** without an operator APPROVE.

## Actions

| Action | Risk |
|--------|------|
| isolate_endpoint | HIGH |
| subnet_isolation | CRITICAL |
| credential_rotation | HIGH |
| halt_operations | CRITICAL |

## Flow

1. Propose Tier-2 action
2. ROE allow-list + circuit breaker
3. WhatsApp to **admin numbers** only: `APPROVE <nonce>` / `DENY <nonce>`
4. Mid-timeout **reminder**
5. APPROVE → execute + confirm; DENY/timeout → hold + notify

## APIs

- `GET /api/soc/tier2` (8092)
- `GET /api/tier2` (8091 dashboard)

## Config

```bash
export CF_WHATSAPP_ADMINS=+1868...
export CF_APPROVAL_TIMEOUT=900
export CF_ALLOW_FORCE=false
```

Report numbers cannot approve — admins only.
