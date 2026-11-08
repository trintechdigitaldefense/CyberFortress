# CyberFortress — Native Linux VM pilot

**Status: candidate deployment profile; not client-approved or ready to arm.**

Live `CF_BLOCK` containment is supported only as a candidate on a native Ubuntu/Debian VM with effective `CAP_NET_ADMIN`, after the client-specific checks and legal sign-off pass.

## Supported profiles

- Native Ubuntu/Debian VM: candidate for monitoring and later approved live containment.
- Android Termux / Ubuntu proot: monitoring-only. `start.sh` forces LIVE=false and firewall auto-start off.
- Standard Docker Compose: monitoring-only. The compose profile has no NET_ADMIN capability and forces LIVE=false.

## Host preflight

```bash
./scripts/check_netadmin.sh
./scripts/pilot_vm_preflight.sh
```

The netadmin check creates an unreferenced temporary chain, inserts one TEST DROP rule, verifies it, removes it, verifies absence and deletes the chain. It does not hook INPUT/OUTPUT/FORWARD or alter `CF_BLOCK`. A failed probe records `netadmin_ok=false`; keep the host monitoring-only.

A CI network-namespace pass proves the script works in an isolated runner; it is not proof that a specific client VM has the required kernel, firewall backend or capabilities.

## Deployment sequence

1. Provision a dedicated native Linux VM with console/out-of-band recovery and a tested VM snapshot.
2. Install requirements using `./install.sh`; secure `.env` with mode 0600.
3. Keep `CF_CONTAINMENT_LIVE=false` and `CF_FIREWALL_AUTO_START=false`.
4. Start `./start.sh local`, then run `scripts/check_client_ready.sh`, `scripts/readiness_check.sh` and this preflight.
5. Complete a minimum seven-day monitoring soak and service-health/failure drills.
6. Complete client-specific allowlist, signed NDA/ROE, attorney review, E&O confirmation, operator acknowledgement and approved change window.
7. Populate `config/pilot_signoff.json` from real signed engagement records. The example file intentionally has no authorized actions or WhatsApp admin numbers.
8. Run `./scripts/enable_live_mode.sh --check`; live arming requires an authorised lead operator and typed confirmation.

## Recovery

```bash
./scripts/disable_live_mode.sh
./stop.sh
./start.sh local
iptables -S CF_BLOCK
```

Disarm writes LIVE=false, flushes only the dedicated `CF_BLOCK` chain and verifies it is empty. It exits non-zero if firewall state cannot be inspected or verified. Never run a broad host `iptables -F`.

Backup and staged restore procedures: [PILOT_DEPLOYMENT.md](PILOT_DEPLOYMENT.md).

## Hard rules

1. Failed or unavailable netfilter probe means monitoring-only.
2. A client-specific VM test is mandatory before live containment.
3. Docker, Termux and proot remain monitoring-only in this release.
4. Do not arm until signed ROE, counsel review, E&O and all sign-off checks are complete.
