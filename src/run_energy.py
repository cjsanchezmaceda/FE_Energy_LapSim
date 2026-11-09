'''Energy study: Gen3 sanity check vs Madrid race, GEN4 kit choice vs energy budget.'''

import json
from dataclasses import replace
from pathlib import Path
 
import numpy as np
 
from track import load_track
from vehicle import GEN3_EVO, mode
from gen4 import GEN4, KITS, mu_Gen3
from lapsim import simulate
from energy import lift_coast_for_budget, power_cap_for_budget
 
ROOT = Path(__file__).resolve().parents[1]
E_G3_RACE = (38.5 + 3.85) / 23   # kWh/lap: usable energy + PIT BOOST, 23 green laps (Madrid 2026)
RACE_MEDIAN = 98.2               # s, median of 80 normal race laps (5 drivers, excl. lap 1, pit, ATTACK MODE)
E_GRID = np.arange(2.6, 3.81, 0.2)
 
kappa, ds = load_track()
out = {}
 
# 1) Gen3 Evo: energy-limited race lap vs reality
g3 = mode(GEN3_EVO, 300)
flat3 = simulate(g3, kappa, ds)
fr, r_lc = lift_coast_for_budget(g3, kappa, ds, E_G3_RACE)
P, r_cap = power_cap_for_budget(g3, kappa, ds, E_G3_RACE)
out["gen3_energy"] = dict(E_budget=E_G3_RACE, T_flat=flat3["lap_time"], E_flat=flat3["E_net"],
                          T_lc=r_lc["lap_time"], coast=fr, T_cap=r_cap["lap_time"], P_cap_kW=P / 1e3,
                          race_median=RACE_MEDIAN)
print(f"Gen3 budget {E_G3_RACE:.2f} kWh/lap | flat-out {flat3['lap_time']:.2f} s ({flat3['E_net']:.2f} kWh) | "
      f"lift-and-coast {r_lc['lap_time']:.2f} s (coast {fr:.0%}) | power cap {r_cap['lap_time']:.2f} s "
      f"({P/1e3:.0f} kW) | race median {RACE_MEDIAN} s")
 
# 2) Speed traces for figure 1: Gen3 Evo 350 kW + front motor vs GEN4 600 kW high-DF
r3 = simulate(mode(GEN3_EVO, 350, awd=True, mu=mu_Gen3), kappa, ds)
r4 = simulate(replace(GEN4, P_drive=600e3, **KITS["high-DF"]), kappa, ds)
out.update(s=(np.arange(len(kappa)) * ds).tolist(),
           v_gen3=(r3["v"] * 3.6).tolist(), v_gen4=(r4["v"] * 3.6).tolist(),
           T_gen3=r3["lap_time"], T_gen4=r4["lap_time"])
 
# 3) GEN4 at 450 kW: lap time vs energy per lap, per aero kit and strategy
out["gen4"] = {}
for kit, aero in KITS.items():
    car = replace(GEN4, P_drive=450e3, **aero)
    flat = simulate(car, kappa, ds)
    T_lc, T_cap = [], []
    for E in E_GRID:
        _, lc = lift_coast_for_budget(car, kappa, ds, E)
        _, cap = power_cap_for_budget(car, kappa, ds, E)
        T_lc.append(lc["lap_time"]); T_cap.append(cap["lap_time"])
        print(f"GEN4 {kit:7} E {E:.1f} kWh | lift-and-coast {lc['lap_time']:.2f} s | power cap {cap['lap_time']:.2f} s")
    out["gen4"][kit] = dict(E=E_GRID.tolist(), T_lc=T_lc, T_cap=T_cap,
                            E_flat=flat["E_net"], T_flat=flat["lap_time"])
 
(ROOT / "results").mkdir(exist_ok=True)
json.dump(out, open(ROOT / "results" / "results.json", "w"), indent=1, default=float)
print("wrote", ROOT / "results" / "results.json")