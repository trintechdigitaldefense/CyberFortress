# CyberFortress client deployment and recovery profile

**Status: P2 hardening instructions. This document is not client acceptance or permission to arm containment.**

## Supported deployment profiles

| Profile | Supported use | Live firewall containment |
|---|---|---|
| Native Ubuntu/Debian Linux VM with effective \`CAP_NET_ADMIN\` | Monitoring and, after every legal/technical gate, approved containment | Candidate profile; must pass the host probe and client VM acceptance |
| Android Termux / Ubuntu proot | Local monitoring, analysis and dry-run workflows | **Not supported. Forced monitoring-only by \`start.sh\`.** |
| Standard Docker Compose profile | Isolated application services and monitoring | **Monitoring-only. Compose intentionally grants no NET_ADMIN and forces LIVE=false.** |
| Privileged/host-network container | Not an accepted client profile in this release | Do not enable; requires a separately designed and reviewed host-network profile |

Do not infer host firewall control from root UID, a successful read-only \`iptables -L\`, or a running container. The host probe must successfully create, verify, delete and clean up a temporary unreferenced firewall chain and rule.

## Native Linux VM deployment

1. Provision a dedicated Ubuntu 22.04+ or supported Debian VM. Confirm console/out-of-band recovery and snapshot availability before testing.
2. Create a non-root service/operator account. Install Python 3.10+, Git, iptables, rsync and the repository's Python requirements.
3. Obtain the approved release candidate branch and verify the commit SHA with the deployment record. Do not deploy an unreviewed working tree.
4. Run \`./install.sh\`; keep \`.env\` mode 0600 and populate only required secrets using the approved secret-handling process.
5. Keep \`CF_CONTAINMENT_LIVE=false\` and \`CF_FIREWALL_AUTO_START=false\`. Start with \`./start.sh local\`.
6. Run:
   \`\`\`bash
   ./scripts/check_client_ready.sh
   ./scripts/readiness_check.sh
   ./scripts/pilot_vm_preflight.sh
   \`\`\`
7. Confirm health endpoints are bound to loopback, inspect service logs, verify all required agents are healthy, and complete a minimum seven-day monitoring soak before live acceptance.
8. Configure client-specific allowlists, scope, ROE and authorized actions only from signed engagement documents. The example sign-off intentionally contains no authorized actions and no phone numbers.
9. Before live containment, obtain signed NDA/ROE, counsel review, E&O confirmation, client approver, operator runbook acknowledgement and all required sign-off fields. WhatsApp may be deferred only if explicitly recorded as deferred.
10. Run \`./scripts/enable_live_mode.sh --check\`. Only an authorised lead operator may then run \`--enable\` after the client change window and typed confirmation.

## Host capability probe

\`scripts/check_netadmin.sh\` uses a uniquely named, unreferenced temporary chain. It adds one TEST DROP rule, checks it, removes it, confirms absence and deletes the temporary chain. It does not attach to INPUT, OUTPUT or FORWARD or alter the production \`CF_BLOCK\` chain. Any failure records \`netadmin_ok=false\`; treat the host as monitoring-only.

The probe must be rerun on the actual client VM immediately before arming. CI namespace evidence is not a substitute for this client-specific check.

## Emergency disarm and rollback

Run from the host with the same network namespace as the firewall agent:

\`\`\`bash
./scripts/disable_live_mode.sh
./stop.sh
./start.sh local
./scripts/check_netadmin.sh
iptables -S CF_BLOCK
\`\`\`

The disarm script:
- writes \`CF_CONTAINMENT_LIVE=false\` to \`.env\`;
- flushes only the dedicated \`CF_BLOCK\` chain (not unrelated firewall chains);
- verifies that the chain is empty; and
- exits non-zero if it cannot inspect or verify the firewall.

It intentionally leaves parent-chain jumps in place because an empty dedicated chain has no DROP rules. If disarm exits non-zero, stop CyberFortress services, preserve logs, and have the host/network administrator inspect the firewall before resuming. Never run a broad \`iptables -F\` against the host.

## Backup and recovery

Create an off-box backup of operational logs and evidence:

\`\`\`bash
export CF_BACKUP_DEST=/mnt/secure-offbox/cyberfortress
./scripts/backup_offbox.sh
\`\`\`

The script fails on copy/archive errors, verifies the tar archive, and writes a SHA-256 sidecar. It intentionally excludes \`.env\`, sign-off files, secrets and pending WhatsApp decisions. Store those sensitive configuration artifacts separately using the client's approved encrypted backup process.

Stage and verify a backup without overwriting live data:

\`\`\`bash
./scripts/restore_offbox.sh /path/to/cf_backup_YYYYMMDD_HHMMSS.tar.gz /secure/restore-staging
\`\`\`

Restore verifies the SHA-256 sidecar, rejects unsafe archive members and extracts into a new staging directory. It never overwrites live \`logs/\` or \`evidence/\`. Review the staged files, compare the manifest and evidence hashes, then perform any controlled recovery while services are stopped.

Run the disposable recovery acceptance before each release candidate:

\`\`\`bash
bash scripts/backup_restore_acceptance.sh
bash scripts/firewall_namespace_acceptance.sh
\`\`\`

## P2 acceptance evidence still required

- Actual client VM hostname/profile, OS/kernel, firewall backend and capability-probe output.
- Successful clean install and service-health evidence on that VM.
- Seven-day monitoring soak and incident/failure drill records.
- Backup transfer to the client's approved off-box destination and a witnessed staged restore.
- Client-specific allowlist, ROE scope, legal approval, E&O confirmation and signed change window.
- Client-approved containment apply, verification, emergency disarm and rollback evidence, performed only on explicitly authorised test targets.

Until those records are attached to the engagement, keep the client deployment in monitoring-only mode. P3 SOC telemetry acceptance must not be declared complete in their place.
