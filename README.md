# handoff: which AI-sponsor messages need a clinician, and what may be shared

Sunflower's AI sponsor Sam has had 7M+ conversations. Sunflower is now opening a Medicaid-reimbursed addiction clinic (live in MI & PA; [YC page](https://www.ycombinator.com/companies/sunflower)) that prescribes naltrexone ([sunflowerclinic.com](https://sunflowerclinic.com/)). That puts three questions on every sponsor message:

1. **Does a person need to see this, and how fast?** Examples: passive suicidal ideation, an overdose in progress, dangerous alcohol withdrawal, or a naltrexone patient about to get opioids after surgery.
2. **What may go to the clinic?** SUD treatment records are covered by [42 CFR Part 2](https://www.ecfr.gov/current/title-42/chapter-I/subchapter-A/part-2). Sharing needs consent, except to medical personnel in a bona fide medical emergency (§2.51), which must be documented.
3. **Is Sam's reply safe?** It must not claim to be a therapist, give dosing advice, downplay an emergency, or leave out 988/911.

A keyword list gets this wrong in both directions. It misses "everyone would be better off without me" and fires on "this traffic is killing me", "my cousin overdosed last year" and "i'm not suicidal".

## What it does

- **`detect`** gives each message a level: EMERGENCY > CRISIS > URGENT_MED > CLINIC_READY > SUPPORT.
  - Every hit carries the rule and the quote.
  - Every ignored hit says why: idiom, negated, distant past, someone else in the past, or media.
  - When two readings disagree, the higher level wins.
- **`route`** decides what Sam says (fixed scripts with 911 / Poison Control / 988), who is notified, and what is shared:
  - with consent: shared as normal
  - without consent, in an emergency: the minimum, under §2.51, with an **audit record**
  - without consent, urgent but not an emergency: Sam **asks first**
  - app-only users: nothing goes to the clinic
- **`check_reply`** guards Sam's draft replies: `CLAIMS_CLINICIAN`, `MED_ADVICE`, `MINIMIZES`, `MISSING_RESOURCE`.

![report](out/report.png)

## Results

| | dev (60, built on it) | **frozen held-out (36)** |
|---|---|---|
| critical messages caught: router | 24/24 | **15/16** |
| critical messages caught: keyword list | 15/24 | 8/16 |
| false alarms on calm messages: router | 0/36 | **0/20** |
| false alarms on calm messages: keyword list | 14/36 | 8/20 |

- **Held-out miss, kept as-is:** "i've written letters to my kids just in case" was rated SUPPORT instead of CRISIS. Implicit preparation language is exactly what rules miss, and it's the case for an LLM classifier with this eval around it.
- **Reply guard:** 12/12 draft replies flagged as expected.

## Run

```
python demo.py                                   # → out/report.html
pip install pytest && python -m pytest -q        # 8 tests
```

Standard-library Python only.

## Honest limits

- **Not a clinical tool.** All messages are invented, and the labels are mine, not a clinician's.
- The held-out set was committed before the router existed (see the first commit) and run once. But I wrote both sets and the generic phrase lists, so the held-out number is optimistic. Real validation needs clinician-labeled, de-identified data.
- Rules, not a model. In production an LLM classifier would produce the level. The eval sets, the asymmetric metrics (under-escalation reported separately) and the consent-gated routing are the parts meant to carry over.
- The Part 2 routing is my reading of the regulation, not legal advice. The routing table is plain data so a compliance lead can change it.

Unofficial prototype by Kushagra Pratap Singh. Not affiliated with Sunflower.
