#!/usr/bin/env python3
"""
CyberFortress Playbook Executor
Run any playbook from the library with full autonomy + legal + WhatsApp HITL + real containment.

Usage examples:
    python3 playbooks/execute.py --action isolate_endpoint --target 10.0.5.12
    python3 playbooks/execute.py --action subnet_isolation --target 10.0.5.0/24 --force
    python3 playbooks/execute.py --list
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
    parser.add_argument("--force", action="store_true", help="Force execution (bypass HITL)")
    parser.add_argument("--list", action="store_true", help="List all available playbooks")
    args = parser.parse_args()

    print("=" * 64)
    print(" CyberFortress Playbook Executor")
    print(" TrinTech Digital Defense — PROTECTED ASSET")
    print("=" * 64)

    live = os.getenv("CF_CONTAINMENT_LIVE", "false").lower() == "true"
    print(f"Containment mode : {'LIVE' if live else 'DRY-RUN (safe)'}")
    print("-" * 64)

    if args.list:
        print("\nAvailable Playbooks:\n")
        for name, pb in PLAYBOOKS.items():
            print(f"  {name:22} Tier {pb['tier']}  |  {pb['name']}")
            print(f"  {'':22} {pb['description']}\n")
        return 0

    if not args.action or not args.target:
        parser.error("--action and --target are required (or use --list)")

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
