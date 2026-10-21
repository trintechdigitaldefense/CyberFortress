# Changelog

## [v0.3.4] — 2026-10-21

### Dashboard WhatsApp report settings
- Settings panel: register report number, toggle **daily** + **live alerts**
- `core/notify_settings.py` + `POST /api/settings/whatsapp` (number stored in `config/whatsapp_notify.json`)
- Daily agent respects `daily_enabled`; live path uses `send_live_alert` (HIGH+)
- Meta token remains in `.env` only

## [v0.3.3] — 2026-10-21

### Real VM pilot gate
- `scripts/pilot_vm_preflight.sh` — netadmin must be green
- WhatsApp deferred — `whatsapp_deferred: true` allows arming before Meta credentials
- `docs/PILOT_VM.md`

## [v0.3.2] — 2026-10-19

- systemd, weekly evidence, rule packs, post-action verify, CAPACITY.md, multi-tenant scaffold, adversarial tests

## [v0.3.1] — 2026-10-19

- HOST_REQUIREMENTS, check_netadmin, pilot_signoff host gate

## [v0.3.0-pilot] — 2026-10-19

- Detection loop, default rule pack, Docker parity

## [v0.2.0] — 2026-10-10

- Hardening, audit chain, pytest, CI

## [v0.1.0] — 2026-10-09

- Initial pilot MVP
