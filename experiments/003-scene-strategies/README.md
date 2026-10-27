# 003 scene strategies

**Goal:** fill three intent files (frames, inversion, skyline) into class maps with one histogram, and measure the scene-level carry-over (`fill.py`).
**Result:** inversion passes the scene gates (2x2 window reuse 0.10 to 0.17, plain). Skyline fails the same-position gate (27.5 to 30.0%, limit 25%) and frames fail the 2x2 window-reuse gate (33.8 to 42.9%, limit 30%). Metrics only, no solver run; design note `docs/design/07-scene-strategies.md` recommends inversion.

Files: `inversion/`, `skyline/` and `frames/` each hold `intent.txt`, `scenes.txt` and `scene-metrics.txt`.
