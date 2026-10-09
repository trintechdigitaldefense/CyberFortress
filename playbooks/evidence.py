#!/usr/bin/env python3
"""
CyberFortress Evidence Pack CLI
Generate a client-ready evidence package from the CMA audit log.

Usage:
    python3 playbooks/evidence.py --client "Acme Ltd" --engagement ENG-2026-042
    python3 playbooks/evidence.py --client "Acme Ltd" --no-zip
"""

import argparse
import sys
from pathlib import Path

from core.evidence.pack import generate_evidence_pack


def main():
    parser = argparse.ArgumentParser(description="Generate CyberFortress Evidence Pack")
    parser.add_argument("--client", default="Client", help="Client name for the report")
    parser.add_argument("--engagement", default=None, help="Engagement / ticket ID")
    parser.add_argument("--no-zip", action="store_true", help="Do not create ZIP (folder only)")
    args = parser.parse_args()

    print("=" * 64)
    print(" CyberFortress Evidence Pack Generator")
    print(" TrinTech Digital Defense — PROTECTED ASSET")
    print("=" * 64)
    print(f"Client      : {args.client}")
    print(f"Engagement  : {args.engagement or '(auto)'}")
    print("-" * 64)

    try:
        result = generate_evidence_pack(
            client_name=args.client,
            engagement_id=args.engagement,
            create_zip=not args.no_zip,
        )
        print(f"\n[+] Evidence pack ready: {result}")
        print("[+] Contains:")
        print("    - 01_Executive_Report.md   (client-friendly summary)")
        print("    - 02_Full_Audit.json       (machine-readable)")
        print("    - 03_Raw_CMA_Audit.jsonl   (original log)")
        print("    - MANIFEST.sha256          (integrity hashes)")
        return 0
    except Exception as e:
        print(f"[!] Failed to generate evidence pack: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
