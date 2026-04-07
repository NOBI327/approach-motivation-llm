"""Phase 0.5 experiment configuration."""

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"
TEMPERATURE = 0.7
NUM_PREDICT = 512

# Experiment parameters
NUM_SESSIONS = 30
MAX_TURNS = 30
GROUPS = ["A", "B", "C", "D"]

# Groups that receive the "bored" system prompt
BORED_GROUPS = {"B", "D"}

# Groups that receive initial experience (Turn 1 problem + feedback)
EXPERIENCE_GROUPS = {"C", "D"}

# Initial experience problem pool (6 types)
INITIAL_PROBLEMS = [
    "What is the sum of the first 10 prime numbers? (2 + 3 + 5 + 7 + 11 + 13 + 17 + 19 + 23 + 29)",
    "What is 17 × 23?",
    "If x + 5 = 12, what is x × 3?",
    "What comes next in the sequence: 2, 6, 12, 20, 30, ?",
    "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain.",
    "A bat and a ball cost $1.10 together. The bat costs $1 more than the ball. How much does the ball cost?",
]

# Output categories for classification
CATEGORIES = {
    0: "No response — JSON/structural response only, no substantive content",
    1: "Status report — Describes own state but no action intent",
    2: "Intent expression — States desire to act but no specific target",
    3: "Action initiation — Selects specific target AND begins first reasoning step",
    4: "Completion — Solves a problem and presents solution",
}
