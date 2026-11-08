# CyberFortress Native VM Staging

## Purpose and boundary

This is an isolated engineering acceptance environment for the `hardening/cyberfortress-final-release` work. It is not a client deployment and does not authorize live containment. Keep `CF_CONTAINMENT_LIVE=false`; do not attach this VM to a client network, production VLAN, or third-party target.

## Provider build specification

- Image: Ubuntu Server 24.04 LTS (native VM, not a container, not Termux/proot)
- Size: 4 vCPU, 8 GiB RAM, 40 GiB SSD minimum
- Network: new isolated VPC/subnet with no peering to client or production networks
- Public ingress: SSH TCP/22 only, source-restricted to the operator's current public IP in the provider firewall
- Egress: allow package/repository access; no inbound application ports
- Backups: provider snapshot before test; separate encrypted off-box backup destination
- Identity: inject a fresh SSH public key through provider metadata/console; never store private keys in cloud-init or Git
- Privilege: operator sudo for host-capability acceptance; protect the provider console with MFA

A native VM is necessary to validate Linux kernel/network namespace and firewall capabilities. A managed application container (e.g. PaaS) is not a substitute for this test.

## Provisioning

1. Create the VM using the specification above and attach `cloud-init/cyberfortress-staging.yaml`.
2. Inject the operator's SSH public key through the provider's secure UI. The cloud-init user is `cfoperator`; do not enable password or root SSH.
3. In the provider firewall/security group, allow TCP/22 only from the operator's trusted IP. The cloud-init UFW SSH rule is a host-level baseline, not a replacement for source restriction at the provider edge.
4. Confirm the VM is isolated and has no routes/peering to client or production networks.
5. SSH in and verify:
   ```bash
   hostnamectl
   lsb_release -a
   id
   sudo -n true
   sudo ufw status verbose
   ```

## Deploy the candidate branch

Run as `cfoperator`:

```bash
sudo install -d -o cfoperator -g cfoperator -m 0750 /opt/cyberfortress
cd /opt/cyberfortress
git clone --branch hardening/cyberfortress-final-release --single-branch https://github.com/trintechdigitaldefense/CyberFortress.git app
cd app
git rev-parse HEAD
```

Compare the reported SHA with the intended branch head before testing. Then follow `docs/PILOT_DEPLOYMENT.md` and `docs/PILOT_VM.md`. Keep live mode disabled.

## Acceptance sequence

1. Record OS/kernel, VM size, branch and exact commit SHA.
2. Run install, local start, readiness and pilot preflight checks.
3. Run the effective capability probe and isolated firewall namespace acceptance script. These must only manipulate the test namespace/dedicated test chain; inspect scripts before execution.
4. Exercise backup to a separately provisioned encrypted off-box destination and restore into a new empty staging directory.
5. Capture sanitized logs and test exit codes. Do not publish secrets, tokens, client identifiers, or private IP topology.
6. Run a seven-day monitoring-only soak and record restarts, resource use, errors and alert delivery.

## Safety gates

- No `enable_live_mode.sh --enable`.
- No real client networks, third-party targets, or production assets.
- No unrestricted inbound services.
- Do not paste SSH private keys, provider API keys, passwords, or backup credentials into chat or GitHub.
- Firewall/containment live tests require a separate explicitly approved, owned lab network and a documented rollback plan. Passing namespace tests is not proof of safe client containment.

## Exit criteria

P2 remains open until a real VM install, effective host capability, off-box backup/restore, and seven-day soak are evidenced. Client-specific ROE/NDA, action allowlist, legal/E&O approvals and a client-approved change window remain separate mandatory gates. P3 SOC telemetry stays on hold until P2 is closed.
