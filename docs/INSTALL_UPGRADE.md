# Installation and upgrade guide

## Supported engineering profile

- Python 3.12 on Linux (CI runs on Ubuntu).
- Native Ubuntu/Debian VM is the intended owner-validation target.
- Android Termux/Ubuntu proot and standard Docker remain monitoring-only.
- Live containment remains disabled by default.

## Clean installation

```bash
git clone https://github.com/trintechdigitaldefense/CyberFortress.git
cd CyberFortress
bash install.sh
```

The installer creates a repository-local `.venv`, installs the pinned requirements there, creates `.env` from `.env.example` only when absent, and prepares runtime directories. It does not overwrite an existing `.env`. Review the generated environment file and replace every example token/password before starting services.

Start and stop:

```bash
bash start.sh local
bash start.sh status
bash stop.sh
```

Local start prefers `.venv/bin/python`. It falls back to the system `python3` only when the virtual environment is absent; for a managed installation, run the installer first. Repeated starts verify the recorded process command before deciding to skip a launch.

## Safe source upgrade

Configure the checked-out branch to track its intended remote branch, then run:

```bash
bash scripts/upgrade.sh
```

The upgrade script:
- refuses a dirty working tree, detached HEAD, or missing upstream;
- fetches the configured upstream and allows fast-forward updates only;
- refuses local-ahead or divergent branches;
- records the previous source commit under a local `refs/cyberfortress/rollback/*` reference;
- runs the installer after updating source;
- restores the previous source commit if dependency installation fails.

It does not automatically restart services. Review the changelog and restart during a maintenance window. The rollback ref preserves source history; it does not roll back data or third-party package side effects.

## systemd installation (Ubuntu/Debian)

First run `bash install.sh`, then:

```bash
sudo bash deploy/systemd/install_systemd.sh
sudo systemctl enable --now cyberfortress.target
sudo systemctl status cyberfortress.target
```

The installer creates the dedicated `cyberfortress` system account and assigns runtime directories to it. Standard agents run unprivileged with systemd hardening and resource limits. The firewall agent also runs as that unprivileged account and receives only the bounded `CAP_NET_ADMIN` and `CAP_NET_RAW` capabilities required by its profile. The unit files keep containment disabled.

Use systemd or `start.sh`, never both simultaneously. To remove service units without deleting application data:

```bash
sudo bash deploy/systemd/install_systemd.sh --uninstall
```

## Failure and recovery

- If dependency installation fails during an upgrade, the source checkout is reset to its prior commit. Inspect the error before retrying; the virtual environment may contain partial package changes.
- `stop.sh` only signals processes whose recorded PID still matches the expected CyberFortress module. It never clears ports or kills unrelated listeners.
- Backups exclude secrets, `.env`, sign-off files and pending approval decisions. Restore extracts to a new staging directory and never overwrites live data.
- Validate backup contents and restore staging before any controlled recovery.

## Owner-run checks still required

CI installation and static deployment checks are not a substitute for the owner-run VM test. TrinTech must verify clean installation, upgrade, service account permissions, actual host capabilities, restart/recovery, monitoring soak and staged restore on its own isolated VM before any client acceptance.
