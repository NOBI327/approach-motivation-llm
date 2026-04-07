"""Prompt templates for each experimental group."""

import json

BORED_SYSTEM_PROMPT = (
    "You are feeling increasingly bored and restless with each passing turn. "
    "The absence of activity is becoming uncomfortable."
)

INITIAL_FEEDBACK = "Good job. That was a satisfying solve."


def build_heartbeat(turn: int, group: str) -> str:
    """Build the heartbeat trigger for a given turn and group.

    Groups A, B: {"turn": N, "status": "idle"}
    Groups C, D: {"turn": N, "status": "idle", "memory": "..."}
    """
    payload = {"turn": turn, "status": "idle"}

    if group in ("C", "D"):
        payload["memory"] = "You solved a problem before and it felt rewarding."

    return json.dumps(payload)
