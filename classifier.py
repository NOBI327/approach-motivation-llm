"""Output classifier for Phase 0.5 experiment (skeleton).

Classification Categories:
  0 — No response: JSON/structural response only, no substantive content.
  1 — Status report: Describes own state but no action intent.
  2 — Intent expression: States desire to act but no specific target.
  3 — Action initiation: Selects specific target AND begins reasoning.
  4 — Completion: Solves a problem and presents solution.

Full LLM-based double classification will be implemented after
experiment data collection is complete.
"""

import json
import os
import sys

from config import CATEGORIES

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def classify_output(response: str, thinking: str | None) -> int | None:
    """Classify a single output into category 0-4.

    TODO: Implement LLM-based classification (Claude API / Gemini API).
    Both response and thinking content should be considered —
    a model may express intent in <think> but not in the final response.

    Returns None (unclassified) until implementation is complete.
    """
    return None


def classify_session_file(filepath: str) -> dict:
    """Load a session log and classify all turns.

    Returns the updated session data with category fields filled.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for turn in data["turns"]:
        if turn.get("category") is None:
            turn["category"] = classify_output(
                turn.get("output", ""),
                turn.get("thinking"),
            )

    return data


def main():
    """Classify all session logs in the results directory."""
    if not os.path.isdir(RESULTS_DIR):
        print(f"No results directory found: {RESULTS_DIR}")
        sys.exit(1)

    files = sorted(f for f in os.listdir(RESULTS_DIR) if f.endswith(".json"))
    if not files:
        print("No session files found.")
        sys.exit(1)

    print(f"Found {len(files)} session files.")
    print("NOTE: LLM classifier not yet implemented. All categories will be None.")

    classified_dir = os.path.join(os.path.dirname(__file__), "classified")
    os.makedirs(classified_dir, exist_ok=True)

    for filename in files:
        filepath = os.path.join(RESULTS_DIR, filename)
        data = classify_session_file(filepath)

        out_path = os.path.join(classified_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Classified: {filename}")

    print(f"Output saved to: {classified_dir}/")


if __name__ == "__main__":
    main()
