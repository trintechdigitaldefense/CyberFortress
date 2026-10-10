from core.legal_mapper import CMA_MAP, get_justification

ACTIONS = [
    "block_ip", "terminate_session", "deploy_decoy", "isolate_endpoint",
    "subnet_isolation", "credential_rotation", "halt_operations",
    "unblock_ip", "restore_endpoint", "restore_subnet",
]


def test_every_containment_action_has_cma_section():
    for action in ACTIONS:
        m = get_justification(action)
        assert "section" in m and m["section"]
        assert "justification" in m and m["justification"]
        assert action in CMA_MAP
