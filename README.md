# FE_Energy_LapSim

Lap simulation of the Formula E layout at Jarama, calibrated on the 2026 Madrid E-Prix (FP1), used
to project the GEN4 car ahead of the 16–20 November 2026 pre-season test and to optimise its energy
deployment over a lap.

**Reports**
- **Test check, 23 Nov 2026:** [GEN4 at the Jarama test: what each power and kit hypothesis implies](report/GEN4_Jarama_Test_Note.pdf). The calibrated model run backwards against the public test times and speed trap.
- 15 Nov 2026: [Optimal energy deployment for GEN4 at Jarama](report/GEN4_Jarama_Energy_Deployment.pdf): minimum-time lap with an energy budget, solved as an optimal control problem ([formulation](docs/OCP_formulation.pdf)).
- 9 Nov 2026: [GEN4 at Jarama: lap time and energy projection](report/GEN4_Jarama_Projection.pdf). Its fixed lift-and-coast rule has since been corrected; the update supersedes its energy results.

## Key results

| | Result |
|---|---|
| Gen3 Evo calibration | One free parameter (tyre μ = 1.689) fitted on the best 350 kW FP1 lap (89.403 s); the 300 kW lap is predicted to within +0.14 s |
| GEN4, qualifying trim | 80.6 s (600 kW, high-DF), −8.8 s vs Gen3 Evo |
| Optimal energy deployment | At 2.6 kWh/lap the optimal GEN4 lap loses 0.64 s against flat-out, a fixed lift-and-coast rule 2.42 s: brake earlier and only on regen |
| GEN4, kit choice | High-DF faster on a free lap; low-DF faster below 2.9 kWh/lap with optimal deployment (3.5 with a fixed rule) |
| Gen3 Evo energy check | Madrid race budget (1.84 kWh/lap): optimum 92.80 s, fixed rule 94.22 s, best normal race laps 94.8–95.7 s |

GEN4 aero, tyre grip, efficiencies and regen split are **assumptions**; public and assumed inputs
are listed in the reports.

## Method

1. **Track:** track limits digitised from satellite imagery, FE loop spliced in;
   centreline 3933 m (official 3934 m); minimum-curvature racing line.
2. **Vehicle:** point mass with aero, longitudinal load transfer, friction circle,
   battery-side power and regen limits, drive/regen efficiencies; FIA minimum masses.
3. **QSS lap simulation:** cornering limit, backward braking pass and forward traction pass
   on a two-lap domain; lap energy from wheel power net of regen.
4. **Calibration:** tyre μ fitted with `brentq` on the FP1 lap; robustness to drag area,
   mass and front-motor use.
5. **Optimal control:** the same physics as constraints; at every 2 m the solver chooses drive,
   regen and friction-brake force for the fastest lap within an energy budget (CasADi + IPOPT).
   Validated against the QSS model, step-size convergence and finite differences.
6. **Studies:** GEN4 projection, optimal vs fixed-rule energy saving, value of energy,
   kit crossover, corner-by-corner deployment, sensitivity of the kit conclusion.

## How to run

```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python src/run_lap.py           # Gen3 Evo laps, 300 and 350 kW
python src/calibration.py       # fit μ, robustness table
python src/gen4.py              # GEN4 flat-out laps, two kits x two power levels
python src/run_energy.py        # fixed-rule energy study -> results/results.json
python src/sensitivity.py       # kit conclusion vs assumptions
python src/figures.py           # report 1 figures -> report/figures/

python src/validate_ocp.py      # optimal control vs QSS, no energy limit
python src/convergence.py       # step-size convergence
python src/run_ocp_energy.py    # optimal vs fixed rule, value of energy -> results/ocp_results.json
python src/figures_ocp.py       # report 2 figures
python src/deployment.py        # corner-by-corner deployment table
python src/annex_figures.py     # phase map on track and T2 detail
pytest                          # tests
python src/inverse_calibration.py   # grip / downforce each power-kit hypothesis needs to match the test laps
python src/figures_inverse.py       # test-check figure
```

## Repository

```
src/
  geo.py, check_alignment.py    KML reading, lon/lat -> local x-y, alignment checks
  track.py                      loop splice, centreline, racing line, curvature, load_track()
  vehicle.py                    Car parameters (Gen3 Evo), power modes
  lapsim.py                     QSS lap simulation and energy
  calibration.py                tyre μ calibration on FP1
  gen4.py                       GEN4 definition and projection
  energy.py                     fixed lift-and-coast and power-cap solvers
  ocp.py                        minimum-time lap with an energy budget (CasADi + IPOPT)
  run_*.py, validate_ocp.py, convergence.py, sensitivity.py, deployment.py, inverse_calibration.py
  figures.py, figures_ocp.py, annex_figures.py, figures_inverse.py
test/                           pytest
data/                           track KMLs and sources (see data/README.md)
docs/                           optimal control formulation
report/                         reports (PDF) and figures
```

## Data

Track geometry and timing sources are listed in [`data/README.md`](data/README.md).
FIA timing documents are copyright of the FIA and are not included.

## Limitations

Point-mass physics (no transients or tyre temperature); single μ for both axles; GEN4 values
assumed until test data is available. The optimal-control study keeps the racing line fixed,
optimises one lap at a time and assumes the GEN4 regen split (350/350 kW).

Carlos Sánchez Maceda