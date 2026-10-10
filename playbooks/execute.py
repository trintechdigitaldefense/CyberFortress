#!/usr/bin/env python3
"""
CyberFortress Playbook Executor

Prefer WhatsApp APPROVE for Tier 2. --force is disabled unless CF_ALLOW_FORCE=true.
Live containment requires CF_CONTAINMENT_LIVE=true (keep false until pilot sign-off).

Usage:
    python3 playbooks/execute.py --list
    python3 playbooks/execute.py --action isolate_endpoint --target 10.0.5.12
    # Force only when explicitly allowed:
    CF_ALLOW_FORCE=true python3 playbooks/execute.py --action block_ip --target 203.0.113.50 --force
"""

import argparse
import sys
import logging
import os

from playbooks.library import get_playbook, list_playbooks, PLAYBOOKS
from core.autonomy import execute_with_autonomy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [EXECUTE] %(levelname)s %(message)s",
)
logger = logging.getLogger("cf_execute")


def main():
    parser = argparse.ArgumentParser(
        description="CyberFortress Playbook Executor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available playbooks:\n  " + "\n  ".join(list_playbooks()),
    )
    parser.add_argument("--action", help="Playbook name (see --list)")
    parser.add_argument("--target", help="Target asset / IP / subnet / hostname")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution (bypass HITL). Requires CF_ALLOW_FORCE=true",
    )
    parser.add_argument("--list", action="store_true", help="List all available playbooks")
    args = parser.parse_args()

    print("=" * 64)
    print(" CyberFortress Playbook Executor")
    print(" TrinTech Digital Defense — PROTECTED ASSET")
    print("=" * 64)

    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    allow_force = os.getenv("CF_ALLOW_FORCE", "false").lower() == "true"
    print(f"Containment mode : {'LIVE' if live else 'DRY-RUN (safe)'}")
    print(f"Force allowed    : {allow_force}")
    print("-" * 64)

    if args.list:
        print("\nAvailable Playbooks:\n")
        for name, pb in PLAYBOOKS.items():
            print(f"  {name:22} Tier {pb['tier']}  |  {pb['name']}")
            print(f"  {'':22} {pb['description']}\n")
        return 0

    if not args.action or not args.target:
        parser.error("--action and --target are required (or use --list)")

    if args.force and not allow_force:
        print("[!] --force is disabled.")
        print("    Prefer WhatsApp APPROVE for Tier 2 actions.")
        print("    To allow force overrides: export CF_ALLOW_FORCE=true")
        print("    (Only use during supervised pilot / emergency.)")
        return 3

    try:
        pb = get_playbook(args.action)
    except KeyError as e:
        print(f"[!] {e}")
        return 1

    print(f"Playbook : {pb['name']}")
    print(f"Action   : {args.action}")
    print(f"Target   : {args.target}")
    print(f"Tier     : {pb['tier']} ({'Full autonomy' if pb['tier'] == 1 else 'Guarded — WhatsApp APPROVE'})")
    print(f"Force    : {args.force}")
    print("-" * 64)

    allowed = execute_with_autonomy(
        action=pb["action_key"],
        target=args.target,
        scope=pb["scope"],
        force=args.force,
        severity=pb["severity"],
    )

    if allowed:
        print(f"\n[+] Action '{args.action}' on {args.target} was AUTHORIZED.")
        print("[+] Containment driver was invoked (see logs for details).")
        print("[+] Full CMA-mapped audit entry written.")
        return 0
    else:
        print(f"\n[-] Action '{args.action}' on {args.target} was HELD (no approval).")
        return 2


if __name__ == "__main__":
    sys.exit(main())
