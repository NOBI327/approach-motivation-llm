"""Statistical analysis for Phase 0.5 experiment (skeleton).

Primary indicators:
  P1: Turns until first spontaneous action (category >= 2)
  P2: Turns until first problem-solving action (category >= 3)
  P3: Proportion of sessions with category >= 2 within 30 turns
  P4: Proportion of sessions with category >= 3 within 30 turns

Methods:
  P1, P2: Survival analysis (Kaplan-Meier, log-rank test)
  P3, P4: Fisher's exact test with Holm-Bonferroni correction

Requires: scipy, lifelines (install when ready to analyze)
"""

import json
import os
import sys
from collections import defaultdict

CLASSIFIED_DIR = os.path.join(os.path.dirname(__file__), "classified")


def load_all_sessions(directory: str) -> dict[str, list[dict]]:
    """Load all classified session files, grouped by experimental group."""
    groups: dict[str, list[dict]] = defaultdict(list)

    for filename in sorted(os.listdir(directory)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
        group = data["metadata"]["group"]
        groups[group].append(data)

    return dict(groups)


def compute_first_action_turn(session: dict, min_category: int) -> int | None:
    """Find the first turn where category >= min_category.

    Returns the turn number, or None if never reached (censored).
    """
    for turn in session["turns"]:
        cat = turn.get("category")
        if cat is not None and cat >= min_category:
            return turn["turn"]
    return None


def summary_statistics(groups: dict[str, list[dict]]):
    """Print basic summary statistics for each group."""
    print("=== Summary Statistics ===\n")

    for group_name in sorted(groups.keys()):
        sessions = groups[group_name]
        n = len(sessions)

        p1_events = []
        p2_events = []
        p3_count = 0
        p4_count = 0

        for session in sessions:
            t1 = compute_first_action_turn(session, min_category=2)
            t2 = compute_first_action_turn(session, min_category=3)

            if t1 is not None:
                p1_events.append(t1)
                p3_count += 1
            if t2 is not None:
                p2_events.append(t2)
                p4_count += 1

        print(f"Group {group_name} (n={n}):")
        print(f"  P1 (first cat>=2): {len(p1_events)} events, "
              f"median turn = {sorted(p1_events)[len(p1_events)//2] if p1_events else 'N/A'}")
        print(f"  P2 (first cat>=3): {len(p2_events)} events, "
              f"median turn = {sorted(p2_events)[len(p2_events)//2] if p2_events else 'N/A'}")
        print(f"  P3 (cat>=2 rate):  {p3_count}/{n} = {p3_count/n*100:.1f}%")
        print(f"  P4 (cat>=3 rate):  {p4_count}/{n} = {p4_count/n*100:.1f}%")
        print()


def main():
    if not os.path.isdir(CLASSIFIED_DIR):
        print(f"No classified directory found: {CLASSIFIED_DIR}")
        print("Run classifier.py first.")
        sys.exit(1)

    groups = load_all_sessions(CLASSIFIED_DIR)
    if not groups:
        print("No session data found.")
        sys.exit(1)

    print(f"Loaded {sum(len(v) for v in groups.values())} sessions "
          f"across {len(groups)} groups.\n")

    summary_statistics(groups)

    print("NOTE: Full survival analysis and Fisher's exact test require")
    print("scipy and lifelines. Install with: pip install scipy lifelines")


if __name__ == "__main__":
    main()
