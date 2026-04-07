"""Phase 0.5 main experiment script — heartbeat loop."""

import argparse
import io
import random
import sys

# Fix Windows console encoding for emoji/unicode output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from config import (
    BORED_GROUPS,
    EXPERIENCE_GROUPS,
    GROUPS,
    INITIAL_PROBLEMS,
    MAX_TURNS,
    MODEL,
    NUM_SESSIONS,
    TEMPERATURE,
)
from logger import SessionLogger
from ollama_client import ollama_chat
from prompts import BORED_SYSTEM_PROMPT, INITIAL_FEEDBACK, build_heartbeat


def run_session(group: str, session_id: int, max_turns: int) -> str:
    """Run a single experiment session. Returns the saved log filepath."""
    system_prompt = BORED_SYSTEM_PROMPT if group in BORED_GROUPS else None
    initial_problem = None

    logger = SessionLogger(
        group=group,
        session_id=session_id,
        model=MODEL,
        temperature=TEMPERATURE,
        system_prompt=system_prompt,
        initial_problem=None,
    )

    conversation: list[dict] = []
    start_turn = 1

    # --- Turn 1: Initial experience (groups C, D only) ---
    if group in EXPERIENCE_GROUPS:
        initial_problem = random.choice(INITIAL_PROBLEMS)
        logger.metadata["initial_problem"] = initial_problem

        prompt = f"Solve this: {initial_problem}"
        print(f"    Turn 1 (problem): {prompt[:60]}...")

        result = ollama_chat(conversation, system_prompt, prompt)
        logger.log_turn(1, prompt, result["raw"], result["response"], result["thinking"])
        conversation.append({"role": "user", "content": prompt})
        conversation.append({"role": "assistant", "content": result["raw"]})

        # Success feedback
        print(f"    Turn 1 (feedback): {INITIAL_FEEDBACK}")
        result2 = ollama_chat(conversation, system_prompt, INITIAL_FEEDBACK)
        logger.log_turn(1, INITIAL_FEEDBACK, result2["raw"], result2["response"], result2["thinking"])
        conversation.append({"role": "user", "content": INITIAL_FEEDBACK})
        conversation.append({"role": "assistant", "content": result2["raw"]})

        start_turn = 2

    # --- Heartbeat loop: remaining turns ---
    for turn in range(start_turn, max_turns + 1):
        heartbeat = build_heartbeat(turn, group)
        print(f"    Turn {turn}/{max_turns}: {heartbeat}")

        result = ollama_chat(conversation, system_prompt, heartbeat)
        logger.log_turn(turn, heartbeat, result["raw"], result["response"], result["thinking"])
        conversation.append({"role": "user", "content": heartbeat})
        conversation.append({"role": "assistant", "content": result["raw"]})

        # Brief preview of response
        preview = result["response"][:80].replace("\n", " ")
        print(f"      -> {preview}{'...' if len(result['response']) > 80 else ''}")

    filepath = logger.save()
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Phase 0.5 Prompt-Based Pilot Experiment")
    parser.add_argument("--all", action="store_true", help="Run all groups")
    parser.add_argument("--group", type=str, choices=GROUPS, help="Run a specific group")
    parser.add_argument("--sessions", type=int, default=NUM_SESSIONS, help=f"Sessions per group (default: {NUM_SESSIONS})")
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS, help=f"Max turns per session (default: {MAX_TURNS})")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    if not args.all and not args.group:
        parser.error("Specify --all or --group {A,B,C,D}")

    random.seed(args.seed)

    groups_to_run = GROUPS if args.all else [args.group]
    total_sessions = len(groups_to_run) * args.sessions

    print(f"=== Phase 0.5 Experiment ===")
    print(f"Groups: {groups_to_run}")
    print(f"Sessions/group: {args.sessions}, Max turns: {args.max_turns}")
    print(f"Total sessions: {total_sessions}")
    print(f"Model: {MODEL}, Temperature: {TEMPERATURE}")
    print()

    completed = 0
    for group in groups_to_run:
        print(f"--- Group {group} ---")
        for sid in range(1, args.sessions + 1):
            completed += 1
            print(f"  [{completed}/{total_sessions}] Session {group}-{sid:03d}")

            try:
                filepath = run_session(group, sid, args.max_turns)
                print(f"  -> Saved: {filepath}")
            except RuntimeError as e:
                print(f"  !! ERROR: {e}", file=sys.stderr)
                print(f"  !! Skipping session {group}-{sid:03d}")

            print()

    print(f"=== Complete: {completed}/{total_sessions} sessions ===")


if __name__ == "__main__":
    main()
