# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| v0.2.x  | Yes |
| < v0.2  | Best effort |

## Reporting a vulnerability

Email **trintechdigitaldefense@gmail.com** with:

- Description and impact
- Steps to reproduce
- Affected version / commit if known

**Response commitment:** acknowledge within **7 days**. Do not open public issues for active exploits.

## Product security posture

- Default dry-run containment
- No secrets in git (`.env` gitignored)
- ROE allow-list, circuit breaker, WhatsApp nonce + allow-list
- Tamper-evident audit hash chain

Authorized defensive use only under written agreement with TrinTech Digital Defense.
