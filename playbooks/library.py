#!/usr/bin/env python3
"""
CyberFortress Playbook Library
Central registry of all supported containment actions.
"""

from typing import Dict, Any

# Canonical playbook definitions
PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "block_ip": {
        "name": "Block Single IP",
        "description": "Immediately block a single anomalous IP address",
        "tier": 1,
        "scope": "single",
        "severity": "HIGH",
        "action_key": "block_ip",
    },
    "terminate_session": {
        "name": "Terminate User Session",
        "description": "Force-kill an active user or service session",
        "tier": 1,
        "scope": "single",
        "severity": "HIGH",
        "action_key": "terminate_session",
    },
    "deploy_decoy": {
        "name": "Deploy Active Decoy",
        "description": "Place a new deception artifact (canary / honey token)",
        "tier": 1,
        "scope": "single",
        "severity": "MEDIUM",
        "action_key": "deploy_decoy",
    },
    "isolate_endpoint": {
        "name": "Isolate Endpoint",
        "description": "Network-isolate a single compromised host",
        "tier": 2,
        "scope": "single",
        "severity": "HIGH",
        "action_key": "isolate_endpoint",
    },
    "subnet_isolation": {
        "name": "Subnet Isolation / Lockdown",
        "description": "Isolate an entire subnet or VLAN",
        "tier": 2,
        "scope": "subnet",
        "severity": "CRITICAL",
        "action_key": "subnet_isolation",
    },
    "credential_rotation": {
        "name": "Widespread Credential Rotation",
        "description": "Force rotation of multiple potentially compromised credentials",
        "tier": 2,
        "scope": "fleet",
        "severity": "HIGH",
        "action_key": "credential_rotation",
    },
    "halt_operations": {
        "name": "Emergency Halt",
        "description": "Stage full operational halt / critical containment",
        "tier": 2,
        "scope": "fleet",
        "severity": "CRITICAL",
        "action_key": "halt_operations",
    },
}


def get_playbook(name: str) -> Dict[str, Any]:
    """Return playbook definition or raise KeyError."""
    if name not in PLAYBOOKS:
        raise KeyError(f"Unknown playbook: {name}. Available: {list(PLAYBOOKS.keys())}")
    return PLAYBOOKS[name]


def list_playbooks() -> list:
    """Return list of available playbook names."""
    return list(PLAYBOOKS.keys())
