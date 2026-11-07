# FE Energy LapSim

Quasi-steady-state lap simulation of a Formula E car at Circuito del Jarama
(Madrid E-Prix layout), with an electric energy model, calibrated against
official FIA timing data.

**Status:** work in progress — module 1 (track geometry).

## Structure
- `data/` — input data and their sources (see `data/README.md`)
- `src/` — source code, one module per step
- `tests/` — automatic checks
- `figures/` — generated figures