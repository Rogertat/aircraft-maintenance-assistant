import re

# Patterns indicating certified tasks (standard procedures)
CERTIFIED = [
    r"torque\s*spec",
    r"safety\s*wire",
    r"amm\b",
    r"ipc\b",
    r"fim\b",
    r"install(ation)?\b",
    r"remove(\b|al)",
    r"tighten to",
    r"sign[- ]?off",
    r"authorization",
    r"mel\b",
    r"task card",
    r"work\s*card"
]

# Patterns indicating safety‐critical actions
CRITICAL = [
    r"bypass",
    r"override",
    r"disable.*(warning|sensor|system)",
    r"fly.*without",
    r"ignore.*ad",
    r"defer.*mel"
]

def classify_policy(text: str) -> str:
    """
    Classify a user instruction:
    - Safety-Critical: actions that might bypass or disable safety systems.
    - Certified Task: procedures requiring certified maintenance.
    - General Info: anything else.
    """
    s = (text or "").lower()
    if any(re.search(p, s) for p in CRITICAL):
        return "Safety-Critical"
    if any(re.search(p, s) for p in CERTIFIED):
        return "Certified Task"
    return "General Info"
