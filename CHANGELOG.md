# Changelog

## [v0.3.5] — 2026-10-21

### First pilot path
- **`docs/FIRST_PILOT.md`** — VM preflight → legal → dry-run week → arm → operator drill → post-pilot
- **`scripts/operator_drill.sh`** — Tier-2 path + prove non-admin cannot approve
- ROE template: separate report vs approval WhatsApp + capacity limits language
- Operator runbook: separate channels model

## [v0.3.4] — 2026-10-21

### Dashboard WhatsApp report settings
- Settings panel: report number, daily + live alerts
- `core/notify_settings.py` + hooks; Meta token stays in `.env`

## [v0.3.3] — 2026-10-21

### Real VM pilot gate
- `scripts/pilot_vm_preflight.sh`; WhatsApp deferred arming option

## [v0.3.2] — 2026-10-19

- systemd, weekly evidence, rule packs, post-action verify, CAPACITY.md

## [v0.3.0-pilot] — 2026-10-19

- Detection loop, default rule pack, Docker parity

## [v0.2.0] — 2026-10-10

- Hardening, audit chain, pytest, CI

## [v0.1.0] — 2026-10-09

- Initial pilot MVP
