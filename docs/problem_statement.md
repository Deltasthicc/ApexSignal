# Official problem statement

Source: GrandPrix Hackathon problem statement document, verbatim extraction.

## Problem Statement 1: The Silent Co-Driver — Reading Driver Stress from Radio Calls

**The challenge.** During a race, the team talks to the driver over radio.
Sometimes the driver sounds tired, frustrated, or stressed, but the
engineers are too busy watching numbers to notice the tone of voice.
Important warning signs get missed simply because no one has time to
listen carefully while also watching the data.

**The solution.**

- Play or upload a radio audio clip.
- The system converts the speech to text.
- The system also studies the tone of voice and shows if the driver
  seems calm, stressed, or tired.
- This is shown alongside basic lap-time information, so the team can
  see if stress is matching up with slower laps.

**Frontend.** A clean screen where you upload or play the audio, and see
the text, the detected mood, and a simple chart of lap times.

**Backend.** Where the audio is processed and the AI models do the
thinking.

**Input.** Audio clips of driver radio messages, lap time data.

**Output.** Text version of what was said, a mood or stress label (Calm,
Stressed, or Tired), and a simple visual showing if mood is affecting
lap performance.

## General rules, mandatory for all teams

- The solution must combine a frontend and a backend. A backend-only or
  notebook-only submission is not accepted.
- Aim for balanced difficulty: not solvable by calling one ready-made
  tool, but not requiring a model built entirely from scratch either.
- Every team member needs an individual Hugging Face account. The
  solution must use something from the Hugging Face Hub (model,
  dataset, Space, or other tool). No restriction on which one.

## How ApexSignal maps to this

The mandatory baseline (transcript + tone label + lap-time correlation)
is the floor, not the ceiling, of what ApexSignal ships. `tone_label`,
`tone_score`, and `tone_confidence` in `RadioAnalysisOutput` are the
direct implementation of the required mood/stress output. Everything
else in the charter (complaint taxonomy, incident memory, lead-time
engine, recurrence monitor) is scope built on top of this floor to make
the submission distinct from a plain transcribe-and-tag tool. See
[`docs/PROJECT_CHARTER.md`](PROJECT_CHARTER.md) for the full design and
[`../README.md`](../README.md) for what is actually shipping.

Problem Statements 2 (Weather Whiplash) and 3 (Crowd Flow Optimiser) are
out of scope. ApexSignal is a single-problem-statement submission by
design; see the charter's scope lock.
