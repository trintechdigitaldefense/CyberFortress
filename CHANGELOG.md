# Changelog

## [v0.3.3] — 2026-10-21

### Real VM pilot gate
- **`scripts/pilot_vm_preflight.sh`** — end-to-end VM pilot check; netadmin must be green
- **`check_netadmin.sh`** writes `config/host_capability.json`; stamps `host_netadmin_verified` on success
- **WhatsApp deferred** — `whatsapp_deferred: true` in pilot_signoff allows arming before Meta credentials
- **`docs/PILOT_VM.md`** — operator sequence for real VM pilots
- Live arming still **refuses** if runtime netadmin check fails

## [v0.3.2] — 2026-10-19

### Ops & depth
- systemd, weekly evidence, rule packs, post-action verify, CAPACITY.md, multi-tenant scaffold, adversarial tests

## [v0.3.1] — 2026-10-19

- HOST_REQUIREMENTS, check_netadmin, pilot_signoff host gate

## [v0.3.0-pilot] — 2026-10-19

- Detection loop, default rule pack, Docker parity

## [v0.2.0] — 2026-10-10

- Hardening, audit chain, pytest, CI

## [v0.1.0] — 2026-10-09

- Initial pilot MVP
