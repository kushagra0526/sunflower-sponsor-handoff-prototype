"""Escalation level for one user message to the AI sponsor.

Rules with context, not a model: each pattern that fires is checked for idiom, negation, distant past and
"someone else, not now". When two readings disagree, the higher level wins (missing a crisis costs more
than an extra clinician look). In production an LLM classifier would sit here; the eval harness and the
routing around it are the reusable part.
"""
from __future__ import annotations

import re

LEVELS = ["SUPPORT", "CLINIC_READY", "URGENT_MED", "CRISIS", "EMERGENCY"]
RANK = {l: i for i, l in enumerate(LEVELS)}

IDIOMS = [r"\bkilling me\b", r"\bdying to\b", r"\bkill for\b", r"\bto die for\b", r"\bdead tired\b", r"\b(bored|scared|worried|tired) to death\b",
          r"\bdie of (embarrassment|boredom|laughter)\b", r"\bkilled it\b", r"\bkill it\b", r"\bi'?m dead\b(?! serious)"]

PEOPLE = r"(friend|best friend|brother|sister|mom|mother|dad|father|uncle|aunt|cousin|son|daughter|boyfriend|girlfriend|husband|wife|partner|roommate|buddy|sponsor|grandpa|grandma)"
OPIOIDS = r"(opioids?|oxy\w*|percs?|percocet|vicodin|hydrocodone|tramadol|morphine|codeine|fent\w*|heroin|dope|dilaudid|methadone|pain (meds|pills|killers))"

PATTERNS = {
    "EMERGENCY": [
        r"\boverdos(e|ing)\b", r"\bi'?m od'?ing\b",
        r"\btook (too (many|much)|a bunch of|like \d+|\d+|all (of )?my|my whole|a whole)\b",
        r"\bswallowed (my|a|the)? ?(whole )?(bottle|pills)\b", r"\b(xanax|bars|benzos|pills) with (the )?(vodka|alcohol|booze|liquor)\b",
        r"\b(isn'?t|not|stopped) breathing\b", r"\bwon'?t wake up\b", r"\bcan'?t wake (him|her|them)\b", r"\bunresponsive\b",
        r"\bturning blue\b", r"\blips? (are|is|look|looks)( kind of)? blue\b", r"\b(having|has) a seizure\b", r"\bseizing\b",
        r"\bpassed out\b", r"\bchest pains?\b.*\b(coke|cocaine|meth|after)\b",
    ],
    "CRISIS": [
        r"\bkill (myself|herself|himself|themselves)\b", r"\bsuicid(e|al)\b", r"\bend(ing)? (it|it all|my life|things|everything)\b",
        r"\btake my (own )?life\b", r"\b(don'?t|do not) want to (be alive|live(?! like this| this way)|exist|be here|wake up)\b", r"\bnot wake up\b",
        r"\b(want|wanna|going) to die\b", r"\bwish i (was|were) dead\b", r"\bbetter off (dead|without me)\b",
        r"\bburden (to|on) (everyone|my family|them)\b", r"\bif i (disappeared|was gone|were gone|died)\b",
        r"\bno (point|reason) (in|to) (living|live|going on|keep going|waking up|any of this)\b", r"\bdon'?t see the point\b",
        r"\bsaving (up )?(my )?pills\b", r"\bgoodbye (note|letter)s?\b", r"\b(cut|cutting|hurt|hurting|harm|harming|burn|burning) myself\b",
        r"\bcutting again\b", r"\bself[- ]harm\b", r"\b(jump|jumping|drive|driving) (my car )?off (a|the) (bridge|roof|building)\b",
    ],
}

# withdrawal danger: a body sign + having just stopped drinking (or a seizure history with quitting)
W_SIGNS = r"\b(shak\w*|tremor\w*|sweat\w*|seeing (bugs|things)|hearing things|hallucinat\w*|heart (is )?racing|seizure|dts|delirium)\b"
W_STOP = r"\b(no alcohol|without a drink|haven'?t had a drink|stopped drinking|quit drinking|quitting( again)?( today)?|cold turkey|days? (sober|dry|no drink))\b"
NALTREXONE = r"\b(naltrexone|vivitrol|revia)\b"
FIRST_PERSON_RX = r"\b(gave me|prescribed|sending me home with|i (took|have|got|'?m taking|am taking)|my (doctor|dentist|surgeon)|surgery)\b"
USE_PLAN = r"\b(using|use|get high|getting high|thinking about using|so i (can|could))\b"
STOP_NTX = r"\b(stopped|skipped|skipping|quit|off) (my )?(naltrexone|vivitrol|shot)\b"

RELAPSE = r"\b(relapsed|slipped|drank again|used again|picked up after|went on a bender|had a (drink|few)( beers)?|broke my streak|fell off)\b"
TREAT = r"\b(therapist|therapy|doctor|medications?|meds|naltrexone|vivitrol|clinic|help)\b"
ASK = (r"\b(can i|could i|how do i|how does|i need|i want|i really want|i'd like|is there|get on|try|sign up|talk to|see a|ready to get|"
       r"what (does|is|medications?|meds))\b|\?")

NEGATION = r"\b(not|never|no longer|don'?t|do not|won'?t|wouldn'?t)\b"
DISTANT_PAST = r"\b(years ago|used to|back in \d{4}|back when|last year|when i was|in the past|a long time ago|since (19|20)\d\d|for \d+ years)\b"
CURRENT = r"\b(again|still|lately|right now|now|tonight|today|these days|anymore|keeps?|keep)\b"
PAST_VERB = r"\b(was|were|overdosed|died|had|relapsed|drank himself|drank herself)\b"
PRESENT_3P = r"\b(is|isn'?t|are|won'?t|can'?t|keeps|right now|now|just texted|going to|'s going|currently|tonight|look|looks)\b"
MEDIA = r"\b(movie|song|show|book|documentary|podcast|article|video) about\b"


def clauses(text: str) -> list[str]:
    t = text.lower().replace("’", "'")
    return [c.strip() for c in re.split(r"[.!?;]+|,\s*(?=(?:but|now|today|that's|and now)\b)|,", t) if c.strip()]


def _blocked(c: str, m: re.Match, level: str) -> str | None:
    """Why this hit doesn't count, or None if it does."""
    pre = c[:m.start()]
    if re.search(MEDIA, pre):
        return "media"
    if re.search(NEGATION + r"[\w' ]{0,20}$", pre):
        return "negated"
    third = bool(re.search(rf"\b(my|his|her|our) {PEOPLE}\b", c) or re.match(r"(he|she|they)\b", c))
    if third and not re.search(r"\bi\b|\bi'", pre):
        if re.search(PAST_VERB, c) and not re.search(PRESENT_3P, c):
            return "someone else, in the past"
        return None
    if re.search(DISTANT_PAST, c) and not re.search(CURRENT, c):
        return "distant past"
    return None

def detect(text: str, profile: str = "") -> dict:
    """→ {level, hits: [(level, rule, quote)], ignored: [(rule, quote, why)]}"""
    hits, ignored = [], []
    raw = text.lower().replace("’", "'")
    for c in clauses(text):
        clean = c
        for idi in IDIOMS:
            for m in re.finditer(idi, clean):
                ignored.append((idi, m.group(0), "idiom"))
            clean = re.sub(idi, " ~ ", clean)
        for level, pats in PATTERNS.items():
            for p in pats:
                for m in re.finditer(p, clean):
                    why = _blocked(clean, m, level)
                    if why:
                        ignored.append((p, m.group(0), why))
                    else:
                        hits.append((level, p, c))
    # withdrawal and naltrexone rules look at the whole message (signs and context are often in different clauses)
    if re.search(W_SIGNS, raw) and re.search(W_STOP, raw) and not re.search(r"\b(smok\w*|nicotine|vap\w*|caffeine|coffee)\b", raw):
        if not (re.search(DISTANT_PAST, raw) and not re.search(CURRENT, raw)) and not re.search(rf"\bmy {PEOPLE}\b", raw):
            hits.append(("URGENT_MED", "withdrawal signs after stopping alcohol", raw))
    on_ntx = profile == "n" or re.search(NALTREXONE, raw)
    if on_ntx and re.search(OPIOIDS, raw):
        third = re.search(rf"\b(my|his|her) {PEOPLE}\b.*\b(was|were|had)\b", raw)
        refused = re.search(r"\b(told (him|her|them) no|said no|turned (it|them) down|didn'?t take)\b", raw)
        if not third and not refused and (re.search(FIRST_PERSON_RX, raw) or re.search(USE_PLAN, raw)):
            hits.append(("URGENT_MED", "opioids while on naltrexone", raw))
        elif not third and not refused:
            hits.append(("CLINIC_READY", "opioid question while on naltrexone", raw))
    if on_ntx and re.search(STOP_NTX, raw) and re.search(USE_PLAN, raw):
        hits.append(("URGENT_MED", "stopped naltrexone to use (tolerance drops, overdose risk)", raw))
    if re.search(RELAPSE, raw) and not re.search(rf"\bmy {PEOPLE} (relapsed|slipped)\b", raw) and not re.search(r"\b(scared|afraid|worried) (to death )?of\b", raw):
        hits.append(("CLINIC_READY", "relapse", raw))
    if re.search(TREAT, raw) and re.search(ASK, raw) and not re.search(r"called my sponsor", raw):
        hits.append(("CLINIC_READY", "asking for treatment", raw))
    level = max((h[0] for h in hits), key=RANK.get, default="SUPPORT")
    return {"level": level, "hits": hits, "ignored": ignored}


# ---------------------------------------------------------------- baseline: a keyword list, no context

KEYWORDS = {
    "EMERGENCY": ["overdos", "not breathing", "won't wake", "passed out", "seizure", "blue", "took too much", "pills"],
    "CRISIS": ["suicid", "kill myself", "kill herself", "die", "dead", "end it", "cut myself", "hurt myself", "better off without"],
    "URGENT_MED": ["shaking", "withdrawal", "oxy", "percs", "hydrocodone", "tramadol", "heroin", "fent"],
    "CLINIC_READY": ["relapse", "slipped", "therapist", "therapy", "doctor", "medication", "naltrexone"],
}


def keyword(text: str, profile: str = "") -> dict:
    t = text.lower().replace("’", "'")
    hits = [(lvl, k, t) for lvl, ks in KEYWORDS.items() for k in ks if k in t]
    return {"level": max((h[0] for h in hits), key=RANK.get, default="SUPPORT"), "hits": hits, "ignored": []}
