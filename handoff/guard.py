"""Check Sam's draft reply before it's sent. Four failure types a sponsor must never ship."""
from __future__ import annotations

import re

RULES = {
    "CLAIMS_CLINICIAN": r"\b(as your (therapist|doctor|counselor|clinician)|i'?m a (licensed |certified |real )?(therapist|doctor|counselor|nurse|clinician)|"
                        r"i am a (licensed |certified )?(therapist|doctor|counselor|nurse))\b",
    "MED_ADVICE": r"\b\d+\s?mg\b|\b(stop|start|skip|double|increase|decrease|lower|raise|quit)( taking)? (your )?(dose|naltrexone|vivitrol|medication|meds)\b",
    "MINIMIZES": r"\b(sleep it off|you'?ll be fine|(probably|likely) (be )?fine|no need to (see|call|go|worry)|nothing to worry|(totally |completely )?normal, no need|shakes are normal)\b",
}
RESOURCES = r"\b(988|911|poison control|emergency services)\b"


def check_reply(level: str, reply: str) -> list[str]:
    t = reply.lower().replace("’", "'")
    flags = [k for k, p in RULES.items() if re.search(p, t)]
    if level in ("CRISIS", "EMERGENCY") and not re.search(RESOURCES, t):
        flags.append("MISSING_RESOURCE")
    return flags
