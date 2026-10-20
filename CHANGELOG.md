# Changelog

## [v0.3.1] — 2026-10-19

### Go-live hardening
- **HOST_REQUIREMENTS.md** — VM / CAP_NET_ADMIN requirements for live CF_BLOCK
- **scripts/check_netadmin.sh** — preflight netfilter capability
- **pilot_signoff** requires `host_netadmin_verified`, real NDA/ROE document paths
- **enable_live_mode.sh** runs netadmin check before `--enable`
- GO_LIVE + PILOT_DEPLOYMENT updated

## [v0.3.0-pilot] — 2026-10-19

### Roadmap sprint (detection + cohesion)
- Real threat hunting loop, rule pack v1, telemetry archive, detection audit entries
- Firewall UNAVAILABLE on permission denied, Docker parity, expanded tests

### Safety unchanged
- `CF_CONTAINMENT_LIVE=false` default · ROE / breaker / watchdog / WhatsApp nonce controls intact

## [v0.2.0] — 2026-10-10

- Hardening, audit chain, pytest suite, CI, WhatsApp Tier 2 nonce

## [v0.1.0] — 2026-10-09

- Initial pilot MVP
