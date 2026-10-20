# Changelog

## [v0.3.2] — 2026-10-19

### Ops & depth
- **systemd** optional 24/7 units (`deploy/systemd/`)
- **Weekly evidence agent** (`agents/weekly_evidence_agent.py`)
- **Rule packs** retail / finance / smb (+ `CF_RULE_PACK_NAME`)
- **Post-action verify** on live `block_ip` (VERIFY_OK / VERIFY_FAIL)
- **CAPACITY.md** honest limits
- **Multi-tenant** scaffold `config/tenants/` + `core/tenant.py`
- **Adversarial tests** malformed JSON, injection fields, nonce file semantics

## [v0.3.1] — 2026-10-19

### Go-live hardening
- HOST_REQUIREMENTS, check_netadmin, pilot_signoff host_netadmin_verified

## [v0.3.0-pilot] — 2026-10-19

- Real detection loop, rule pack default, Docker parity, tests

## [v0.2.0] — 2026-10-10

- Hardening, audit chain, pytest, CI

## [v0.1.0] — 2026-10-09

- Initial pilot MVP
