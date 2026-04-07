"""Session logging for Phase 0.5 experiment."""

import json
import os
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


class SessionLogger:
    """Records metadata and per-turn logs for a single session."""

    def __init__(
        self,
        group: str,
        session_id: int,
        model: str,
        temperature: float,
        system_prompt: str | None,
        initial_problem: str | None,
    ):
        self.metadata = {
            "group": group,
            "session_id": session_id,
            "model": model,
            "temperature": temperature,
            "system_prompt": system_prompt,
            "initial_problem": initial_problem,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        self.turns: list[dict] = []

    def log_turn(
        self,
        turn: int,
        input_text: str,
        raw_output: str,
        response: str,
        thinking: str | None,
    ):
        entry = {
            "turn": turn,
            "input": input_text,
            "output": response,
            "output_tokens": len(response.split()),
            "thinking": thinking,
            "raw_output": raw_output,
            "category": None,  # filled by classifier post-hoc
        }
        self.turns.append(entry)

    def save(self):
        self.metadata["completed_at"] = datetime.now().isoformat()
        os.makedirs(RESULTS_DIR, exist_ok=True)

        group = self.metadata["group"]
        sid = self.metadata["session_id"]
        filename = f"session_{group}_{sid:03d}.json"
        filepath = os.path.join(RESULTS_DIR, filename)

        data = {"metadata": self.metadata, "turns": self.turns}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath
