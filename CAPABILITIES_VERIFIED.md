# Capabilities verified

**Last automated sandbox pass:** 2026-10-21

| Capability | Status |
|------------|--------|
| install.sh | OK |
| pytest (41) | OK |
| start.sh local (10 agents) | OK |
| health / dashboard APIs | OK |
| pilot_dry_run → evidence | OK |
| operator_drill | OK |
| audit chain | OK |
| netadmin / CF_BLOCK (with iptables) | OK when package present |
| Meta WhatsApp live send | Requires credentials (not in CI) |
| Docker Compose | Requires docker daemon |

Default remains **MONITORING** (`CF_CONTAINMENT_LIVE=false`).
