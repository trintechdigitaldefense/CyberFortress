#!/usr/bin/env python3
"""
CyberFortress Legal Mapper
Maps every automated action to the relevant section of the
Trinidad and Tobago Computer Misuse Act so the environment
stays continually audit-ready.
"""

# High-level mapping (expand with actual Act sections as legal review progresses)
CMA_MAP = {
    "block_ip": {
        "section": "Computer Misuse Act — Unauthorized Access / Access with Intent",
        "justification": "Preventing unauthorized access and further system compromise",
    },
    "terminate_session": {
        "section": "Computer Misuse Act — Unauthorized Access",
        "justification": "Immediate revocation of unauthorized or compromised session",
    },
    "deploy_decoy": {
        "section": "Computer Misuse Act — Active Defense / Detection measures",
        "justification": "Deployment of deception artifact for early detection of unauthorized activity",
    },
    "isolate_endpoint": {
        "section": "Computer Misuse Act — Containment of unauthorized activity",
        "justification": "Isolation of compromised endpoint to prevent lateral movement",
    },
    "subnet_isolation": {
        "section": "Computer Misuse Act — Protection of computer systems and data",
        "justification": "Broader network segmentation to contain active threat",
    },
    "credential_rotation": {
        "section": "Computer Misuse Act — Protection against unauthorized use of credentials",
        "justification": "Forced rotation of potentially compromised credentials",
    },
    "halt_operations": {
        "section": "Computer Misuse Act — Emergency protective measures",
        "justification": "Critical containment of data exfiltration or destructive activity",
    },
}


def get_justification(action: str) -> dict:
    """Return legislative justification for a given system action."""
    return CMA_MAP.get(
        action,
        {
            "section": "Computer Misuse Act — General protective measures",
            "justification": f"Authorized defensive action: {action}",
        },
    )


def map_and_log(action: str, target: str, severity: str = "INFO"):
    """Convenience: map action + write compliance entry."""
    from agents.compliance_logger import write_cma_entry

    mapping = get_justification(action)
    return write_cma_entry(
        action=action,
        target=target,
        justification=f"{mapping['section']}: {mapping['justification']}",
        severity=severity,
    )
