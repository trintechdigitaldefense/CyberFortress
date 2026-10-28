#!/usr/bin/env python3
"""IR case state machine — valid transitions and idempotent helpers."""

from __future__ import annotations

from typing import Dict, FrozenSet, Set

TRANSITIONS: Dict[str, FrozenSet[str]] = {
    "open": frozenset({"investigating", "awaiting_approval", "contained", "closed", "reported"}),
    "investigating": frozenset(
        {"awaiting_approval", "contained", "closed", "reported", "open"}
    ),
    "awaiting_approval": frozenset({"investigating", "contained", "closed", "reported"}),
    "contained": frozenset({"reported", "closed", "investigating"}),
    "reported": frozenset({"closed"}),
    "closed": frozenset(),
}

TERMINAL = frozenset({"closed"})


def can_transition(current: str, new_status: str) -> bool:
    return new_status in TRANSITIONS.get(current or "", frozenset())


def assert_transition(current: str, new_status: str) -> None:
    if not can_transition(current, new_status):
        raise ValueError(f"invalid IR transition {current!r} → {new_status!r}")


def is_terminal(status: str) -> bool:
    return status in TERMINAL


def is_openish(status: str) -> bool:
    return status in ("open", "investigating", "awaiting_approval", "contained")


def next_states(current: str) -> Set[str]:
    return set(TRANSITIONS.get(current or "", frozenset()))
