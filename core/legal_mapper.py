#!/usr/bin/env python3
"""CyberFortress Legal Mapper — TT Computer Misuse Act justifications."""

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
    "unblock_ip": {
        "section": "Computer Misuse Act — Restoration of legitimate access",
        "justification": "Authorized rollback of IP block after threat cleared",
    },
    "restore_endpoint": {
        "section": "Computer Misuse Act — Restoration of legitimate access",
        "justification": "Authorized rollback of endpoint isolation after containment complete",
    },
    "restore_subnet": {
        "section": "Computer Misuse Act — Restoration of legitimate network operations",
        "justification": "Authorized rollback of subnet isolation after threat cleared",
    },
}


def get_justification(action: str) -> dict:
    return CMA_MAP.get(
        action,
        {
            "section": "Computer Misuse Act — General protective measures",
            "justification": f"Authorized defensive action: {action}",
        },
    )


def map_and_log(action: str, target: str, severity: str = "INFO"):
    from agents.compliance_logger import write_cma_entry

    mapping = get_justification(action)
    return write_cma_entry(
        action=action,
        target=target,
        justification=f"{mapping['section']}: {mapping['justification']}",
        severity=severity,
    )
