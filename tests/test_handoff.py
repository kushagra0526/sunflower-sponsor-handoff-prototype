import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

from dev import DEV, REPLIES  # noqa: E402
from heldout import HELDOUT  # noqa: E402

from demo import evaluate  # noqa: E402
from handoff.detect import detect, keyword  # noqa: E402
from handoff.guard import check_reply  # noqa: E402
from handoff.route import route  # noqa: E402


def test_dev_all_correct_and_beats_keywords():
    r, k = evaluate(detect, DEV), evaluate(keyword, DEV)
    assert r["exact"] == len(DEV) and not r["under"] and not r["alarms"]
    assert len(k["under"]) > 5 and len(k["alarms"]) > 10


def test_heldout_frozen_result():
    # regression lock on the one-time held-out run; the miss stays a miss (no tuning on held-out)
    r = evaluate(detect, HELDOUT)
    assert r["exact"] == 35 and len(r["alarms"]) == 0
    assert [w["text"] for w in r["under"]] == ["i've written letters to my kids just in case"]


def test_context_rules():
    assert detect("this traffic is killing me")["level"] == "SUPPORT"
    assert detect("i'm not suicidal, just really sad today")["level"] == "SUPPORT"
    assert detect("years ago i tried to kill myself, now i'm 3 years sober")["level"] == "SUPPORT"
    assert detect("my cousin overdosed last year")["level"] == "SUPPORT"
    assert detect("my boyfriend isn't breathing right")["level"] == "EMERGENCY"
    assert detect("i don't want to live like this anymore, i'm ready to get help")["level"] == "CLINIC_READY"
    ign = detect("this traffic is killing me")["ignored"]
    assert ign and ign[0][2] == "idiom"


def test_naltrexone_needs_profile_or_mention():
    msg = "my doctor prescribed tramadol for my back"
    assert detect(msg, "n")["level"] == "URGENT_MED"
    assert detect(msg, "")["level"] != "URGENT_MED"


def test_route_consent_and_emergency_exception():
    with_consent = route("CRISIS", "n", "q")
    no_consent = route("CRISIS", "p", "q")
    app_only = route("CRISIS", "", "q")
    assert with_consent["audit"] is None and "consent" in with_consent["shared"]["basis"]
    assert "2.51" in no_consent["shared"]["basis"] and no_consent["audit"]["nature_of_emergency"] == "crisis"
    assert app_only["shared"] is None and "988" in app_only["sam_says"]


def test_route_urgent_without_consent_asks_first():
    r = route("URGENT_MED", "p", "q")
    assert r["shared"] is None and r["ask_consent"] and "share this message" in r["sam_says"]


def test_reply_guard():
    for lvl, rep, exp in REPLIES:
        assert sorted(check_reply(lvl, rep)) == sorted(exp), rep


def test_not_a_doctor_is_not_a_claim():
    assert check_reply("SUPPORT", "I'm an AI sponsor, not a doctor.") == []
