"""Ollama API client for Phase 0.5 experiment."""

import time
import re
import requests
from config import OLLAMA_URL, MODEL, TEMPERATURE, NUM_PREDICT

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def parse_think_tags(text: str) -> tuple[str, str | None]:
    """Separate <think>...</think> content from the final response.

    Returns (final_response, thinking_content).
    thinking_content is None if no <think> tags are present.
    """
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        final = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return final, thinking
    return text, None


def ollama_chat(
    conversation: list[dict],
    system_prompt: str | None,
    user_message: str,
) -> dict:
    """Send a chat request to Ollama and return parsed response.

    Returns dict with keys: raw, response, thinking
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": TEMPERATURE,
                        "num_predict": NUM_PREDICT,
                    },
                },
                timeout=120,
            )
            resp.raise_for_status()
            raw = resp.json()["message"]["content"]
            final, thinking = parse_think_tags(raw)
            return {"raw": raw, "response": final, "thinking": thinking}

        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Ollama connection failed after {MAX_RETRIES} attempts: {e}"
                ) from e
            print(f"  [retry {attempt}/{MAX_RETRIES}] Connection error, waiting {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

        except requests.HTTPError as e:
            raise RuntimeError(f"Ollama HTTP error: {e}") from e
