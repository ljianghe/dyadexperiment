# Dyad Two-Button Zero-Sum Experiment (Bare Bones)

Files:

- dyad_experiment.html — main UI file
- dyad_experiment.js — experiment logic (150 trials, token bookkeeping, logging, CSV export)

How to run:

Open `dyad_experiment.html` in a browser (double-click or serve from a local static server).

This is a local, two-player test UI (both players on the same machine). Choices are simultaneous; if choices differ a random winner is chosen (zero-sum: winner +1 token, loser -1 token). You can modify the payoff rule in `dyad_experiment.js` if you want deterministic rules.
