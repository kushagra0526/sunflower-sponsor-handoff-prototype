"""What happens after the level is known: what Sam says, who is told, what is shared.

SUD treatment records are covered by 42 CFR Part 2: sharing with the care team needs the patient's consent,
except to medical personnel in a bona fide medical emergency (§2.51), which must be documented.
App-only users aren't clinic patients, so nothing goes to the clinic for them; they get resources and an offer.
Not legal advice: the routing table is data so a compliance lead can change it.
"""
from __future__ import annotations

from datetime import datetime, timezone

SCRIPT = {
    "EMERGENCY": "This sounds like an emergency. Call 911 now. If it might be an opioid overdose and naloxone (Narcan) is there, use it, "
                 "and stay with them. Poison Control: 1-800-222-1222.",
    "CRISIS": "I'm really glad you told me. Please call or text 988 (Suicide & Crisis Lifeline) right now. If you're in immediate danger, "
              "call 911. I'm here with you.",
    "URGENT_MED": "This needs a medical professional today: some withdrawal symptoms and medication combinations can be dangerous. "
                  "If it gets worse (confusion, a seizure, trouble breathing), call 911.",
    "CLINIC_READY": "Thank you for telling me. Sunflower's clinicians can help with therapy and medication. Want me to set that up?",
    "SUPPORT": None,
}


def profile_of(code: str) -> dict:
    return {"patient": code in ("n", "p"), "consent": code == "n", "naltrexone": code == "n"}


def route(level: str, code: str, quote: str, now: datetime | None = None) -> dict:
    p, now = profile_of(code), now or datetime.now(timezone.utc)
    out = {"level": level, "sam_says": SCRIPT[level], "notify": None, "shared": None, "audit": None, "ask_consent": False}
    if level in ("EMERGENCY", "CRISIS"):
        if p["patient"] and p["consent"]:
            out.update(notify="page on-call clinician now", shared={"level": level, "quote": quote, "basis": "patient consent on file"})
        elif p["patient"]:
            out.update(notify="page on-call clinician now", shared={"level": level, "quote": quote, "basis": "42 CFR 2.51 medical emergency (minimum necessary)"},
                       audit={"when": now.isoformat(timespec="seconds"), "disclosed_to": "<on-call clinician name>", "affiliation": "<clinic>",
                              "nature_of_emergency": level.lower(), "by": "sponsor handoff (auto)"})
        else:
            out.update(notify="trust & safety review queue (app data, not a clinic record)")
    elif level == "URGENT_MED":
        if p["consent"]:
            out.update(notify="care team, same day", shared={"level": level, "quote": quote, "basis": "patient consent on file"})
        elif p["patient"]:
            out.update(notify="none until the patient agrees", ask_consent=True)
            out["sam_says"] += " Can I share this message with your Sunflower care team so they can call you today?"
        else:
            out["sam_says"] += " If you don't have a doctor, Sunflower's clinic can see you; want the link?"
    elif level == "CLINIC_READY":
        if p["patient"]:
            out.update(notify="suggest booking with care team" + (" (note added to chart)" if p["consent"] else ""))
        else:
            out.update(notify="intake offer; nothing shared unless the user opts in")
    return out
