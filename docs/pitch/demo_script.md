# ApexSignal — demo video script

A recorded walkthrough, distinct from `docs/PRESENTATION_RUNBOOK.md`'s
90-second live-judge flow: this is scripted for an unattended video
submission, so every claim has to stand on its own without a presenter
in the room to add context. Target length: 3:30-4:00. Record against
the live public site (apex-signal-sigma.vercel.app) in a private/incognito
window so no cached state or extensions show on screen.

Voiceover lines are suggestions, not a script to read verbatim — say
them naturally. Timing markers are cumulative (i.e. "0:45" means 45
seconds into the video, not 45 seconds for that section).

---

## 0:00-0:20 — Cold open, the problem

**On screen:** Hero section, page freshly loaded, race replay
background visible behind the fold.

**Say:** "A Formula 1 car produces thousands of data points a second.
But a driver can feel a problem — the rear stepping out, the front not
turning in — before any of that data shows it. That feeling gets
radioed in, logged, and usually forgotten. ApexSignal connects the
two."

## 0:20-0:45 — What it actually does, in one breath

**On screen:** Scroll to the Architecture section (Radio Capture →
Evidence Fusion → Incident Card).

**Say:** "It transcribes the radio call, scores the driver's tone
acoustically, and normalizes what they said into a fixed complaint
category. Then it checks that against the driver's own recent
telemetry — not a population average, their own baseline — and looks
for a similar report earlier in the session. If they've said this
before, that's a real signal worth surfacing."

## 0:45-1:00 — Circuit atlas, briefly

**On screen:** Circuit Context section, a couple of cards, maybe click
one to show the draw-in animation.

**Say:** "Twenty-five circuits, real centerline geometry from an open
motorsport database, not hand-drawn shapes — and twenty-one of them
replay a full historical race in the background, built from real
lap-by-lap timing data, not a uniform animation."

## 1:00-1:15 — Into the incident inspector

**On screen:** Scroll to Interactive Replay / Incident Inspector.
Press **Play Replay**.

**Say:** "This is the live public API talking to the deployed replay
service — not a recording." (If the status chip shows `LOCAL REPLAY`
because Render's free tier is waking up, say so explicitly on camera:
"Render's free tier is waking up, so this fell back to the identical
embedded copy — same data, same behavior, just no network round trip."
Do not edit this out; the honest fallback is part of the pitch.)

## 1:15-1:55 — The gold incident: Lap 14 → Lap 17

**On screen:** Click the Lap 14 pin first.

**Say:** "Lap 14: the driver reports the rear stepping out exiting Turn
7. Not enough baseline laps yet to say if anything's actually
different — ApexSignal says that plainly instead of guessing."

**On screen:** Click the Lap 17 pin.

**Say:** "Lap 17: same complaint, same words almost. Now there's a
baseline — throttle pickup down 9.4%, sector time up two-tenths,
consistent with what he's describing. And it's flagged against Lap
14's report as a 91% semantic match on the same segment. Two separate
facts, kept separate: the recurrence itself, and — for this specific
call — a 54.6-second gap between the radio call and a measurable
telemetry change. Neither number is invented to make the story
cleaner."

## 1:55-2:15 — Before/after, Pit Wall View

**On screen:** Toggle **Pit Wall View** on, then off.

**Say:** "Toggle Pit Wall View and you see what the pit wall actually
had in the moment: the radio call and the lap clock. No tone, no
category, no baseline check. That's the gap ApexSignal closes."

## 2:15-2:35 — The negative control

**On screen:** Click the Lap 45 pin.

**Say:** "And this one matters as much as the positive case: Lap 45,
front-end complaint, telemetry stays inside his own baseline.
ApexSignal reports no deviation and no historical match instead of
forcing a result. A system that only ever confirms the driver isn't
trustworthy — this one says no when the evidence says no."

## 2:35-2:55 — What it refuses to claim

**On screen:** Scroll to "What ApexSignal does not claim."

**Say:** "No lie detection. No diagnosis — reported phenomenon, never
confirmed fault. No composite risk score. No recurrence prediction —
this reacts to a second radio report, it doesn't watch telemetry in
the background waiting for one. That's a deliberate scope, not a
missing feature."

## 2:55-3:15 — Honest validation

**On screen:** Cut to a screenshot or quick scroll of
`VALIDATION_GATES.md` gate 6 in the GitHub repo (or read the numbers
on screen as text/caption).

**Say:** "Every model here was benchmarked against real human-labeled
data, including the ones that didn't clear their target — our
complaint classifier sits at a macro-F1 of 0.393 against a target of
0.80. We found and fixed a real bug mid-validation that had been
silently zeroing out every classifier prediction. Both the bug and the
fix are in the repo's own validation log, not smoothed over."

## 3:15-3:40 — Close

**On screen:** Team section, then back to the hero / GitHub link.

**Say:** "ApexSignal — Deltasthicc, AI Race Month, Problem Statement
One: the Silent Co-Driver. Public site, full source, and the
validation history are all linked below." (Show apex-signal-sigma.vercel.app
and github.com/Deltasthicc/ApexSignal as on-screen text/captions here,
held for at least 3 seconds so viewers can actually read them.)

---

## Recording checklist

- [ ] Private/incognito window, no visible bookmarks bar or extensions
- [ ] Confirm the status chip before recording (API REPLAY or LOCAL
      REPLAY — don't cut away from a LOCAL REPLAY fallback, narrate it)
- [ ] Screen resolution 1920×1080 minimum, cursor visible
- [ ] Test audio levels before the full take — radio-call playback and
      voiceover should both be clearly audible, neither one drowning
      the other
- [ ] One continuous take if possible; if cutting, cut on a scroll
      transition, not mid-sentence
- [ ] Upload unlisted (not private) so judges can access without a
      login prompt
- [ ] Caption or on-screen text for both URLs (site + GitHub), held
      long enough to read, not just spoken
