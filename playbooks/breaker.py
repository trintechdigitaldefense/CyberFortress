#!/usr/bin/env python3
"""
CyberFortress Circuit Breaker CLI

Usage:
    python3 playbooks/breaker.py status
    python3 playbooks/breaker.py reset
    python3 playbooks/breaker.py trip --reason "Manual emergency stop"
"""

import argparse
import sys
import json

from core.circuit_breaker import breaker


def main():
    parser = argparse.ArgumentParser(description="CyberFortress Circuit Breaker Control")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show current breaker state")
    sub.add_parser("reset", help="Reset breaker to CLOSED (normal operation)")

    trip_parser = sub.add_parser("trip", help="Manually trip the breaker")
    trip_parser.add_argument("--reason", default="Manual trip by operator", help="Reason for tripping")

    args = parser.parse_args()

    print("=" * 60)
    print(" CyberFortress Circuit Breaker")
    print("=" * 60)

    if args.command == "status":
        status = breaker.status()
        print(json.dumps(status, indent=2))
        if status["state"] == "OPEN":
            print("\n[!] BREAKER IS OPEN — autonomous actions are blocked")
            print(f"    Reason: {status['reason']}")
        else:
            print("\n[+] Breaker is CLOSED — normal operation")

    elif args.command == "reset":
        breaker.reset(by="cli-operator")
        print("[+] Circuit breaker has been RESET to CLOSED")

    elif args.command == "trip":
        breaker.trip(args.reason)
        print(f"[!] Circuit breaker TRIPPED: {args.reason}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
