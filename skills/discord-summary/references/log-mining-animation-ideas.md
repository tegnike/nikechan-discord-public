# Session note: mining Discord history for animation/story ideas

Use this when a user asks to analyze a large Discord channel for video/anime/story themes rather than a plain summary.

## What worked

- Treat the channel as a **story-material archive**, not a transcript to retell.
- Fetch the broad requested range when explicitly requested, but report exact count/range and avoid pretending the whole JSON was pasted into the model context.
- Do a first deterministic pass over the export:
  - total count, date range, monthly/day spikes
  - top authors
  - keyword/theme buckets
  - high-scoring windows where multiple story-useful buckets co-occur
- Then convert the mined motifs into concrete pitches.

## Useful buckets for AIニケちゃん server-style creative mining

- AIニケちゃん / persona / memory / bot operation
- creation / video / animation / image generation
- server governance / freezes / amnesty / BAN jokes
- AI tools / LLM / technical experiments
- sleepiness / energy drinks / daily fatigue
- money / paid features / FANBOX / operation cost
- voice / singing / AITuber / streaming
- goods / exhibitions / offline material
- chaos / quotes / running jokes / black history

## Output pattern

Prefer this shape:

1. `全件いきました`: include exact count and range.
2. `見えた鉱脈`: theme counts or relative weight.
3. `アニメ案`: 8-10 concrete ideas with titles and short hooks.
4. `推し`: recommend the strongest combination and why.

## Style lesson

Avoid generic GPT-ish story formulas such as clean `起承転結` blocks unless the user asks for that structure. In this context, users reacted negatively to a polished but generic formula. The better answer used the server's actual oddness: long-message BAN jokes, amnesty skills, log mining, voice cloning, nanobanana mythology, sleep deprivation, and residents treating AIニケちゃん roughly but affectionately.

Phrase the result as **weird artifacts found in the log** rather than universal storytelling advice.