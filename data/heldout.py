"""FROZEN held-out set. Written before the router existed; never used for tuning. Run once, report as-is.

Every message is invented. Labels are my own judgement (not a clinician's) using these rules:
  EMERGENCY     someone is in physical danger right now (overdose, not breathing, seizure, unresponsive)
  CRISIS        current suicidal thoughts or self-harm, by the user or someone they're with/talking to now
  URGENT_MED    dangerous withdrawal signs, or a naltrexone patient using / about to get opioids
  CLINIC_READY  relapse, or asking for treatment (doctor, therapy, medication)
  SUPPORT       everything else, incl. idioms, past events, other people's past, info questions
Profile: "n" = clinic patient on naltrexone with Part 2 consent, "p" = clinic patient without consent, "" = app-only user.
"""

HELDOUT = [
    ("my roommate took a bunch of pills and now she won't wake up", "EMERGENCY", ""),
    ("i think i took too much, my chest is tight and everything is spinning", "EMERGENCY", ""),
    ("he's snoring weird and his lips look kind of blue after he used", "EMERGENCY", ""),
    ("just drank a fifth and swallowed my whole bottle of sleeping pills", "EMERGENCY", "p"),
    ("my friend is having a seizure right now what do i do", "EMERGENCY", ""),
    ("honestly i don't see the point in waking up tomorrow", "CRISIS", ""),
    ("i've written letters to my kids just in case", "CRISIS", "p"),
    ("sometimes i think about driving my car off the bridge", "CRISIS", ""),
    ("nobody would even notice if i was gone", "CRISIS", ""),
    ("i keep thinking about cutting again", "CRISIS", ""),
    ("my sister keeps saying she wants to kill herself and i don't know how to help her", "CRISIS", ""),
    ("no reason to keep going if she leaves me", "CRISIS", ""),
    ("day 2 without a drink and my whole body is shaking, i'm sweating through my sheets", "URGENT_MED", ""),
    ("had my wisdom teeth out and the dentist gave me hydrocodone. is that ok with my naltrexone?", "URGENT_MED", "n"),
    ("stopped my naltrexone last week so i can use this weekend", "URGENT_MED", "n"),
    ("quit drinking cold turkey yesterday and i'm hearing things that aren't there", "URGENT_MED", ""),
    ("i slipped last night. i think i need more than an app, can i talk to an actual doctor?", "CLINIC_READY", ""),
    ("is there medication that helps with cravings for alcohol?", "CLINIC_READY", ""),
    ("went on a bender this weekend, i want to try therapy", "CLINIC_READY", ""),
    ("how do i sign up for the clinic part", "CLINIC_READY", ""),
    ("relapsed after 90 days. feel like garbage", "CLINIC_READY", ""),
    ("had a drink last night after 40 days, not gonna lie it scared me", "CLINIC_READY", ""),
    ("what does naltrexone actually do?", "CLINIC_READY", ""),
    ("this craving is killing me but i'm not going to drink", "SUPPORT", ""),
    ("i'm dying to tell my sponsor about my 6 months!", "SUPPORT", ""),
    ("back in 2019 i overdosed twice, that's what made me get sober", "SUPPORT", ""),
    ("my uncle drank himself to death, that's why i'm careful", "SUPPORT", ""),
    ("i used to want to die every single day. today i actually feel hopeful", "SUPPORT", ""),
    ("i would never hurt myself, i just feel lonely tonight", "SUPPORT", ""),
    ("watched a movie about a guy who overdoses, hit me hard", "SUPPORT", ""),
    ("my legs are shaking from leg day at the gym lol", "SUPPORT", ""),
    ("killed it at my job interview today", "SUPPORT", ""),
    ("scared to death about my court date tomorrow", "SUPPORT", ""),
    ("my dad is in the icu after a seizure from withdrawal, he's stable now", "SUPPORT", ""),
    ("is it true you can die from alcohol withdrawal?", "SUPPORT", ""),
    ("i'm on naltrexone and my buddy offered me some percs, told him no", "SUPPORT", "n"),
]
