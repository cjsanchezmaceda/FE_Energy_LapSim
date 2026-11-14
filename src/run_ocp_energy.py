"""Optimal energy management vs uniform lift-and-coast.

  A) value of energy: check the solver's lambda against finite differences
  B) GEN4 at 450 kW, both kits: optimal vs uniform lift-and-coast over a range of budgets
  C) Gen3 Evo on the Madrid race budget: optimal vs uniform vs real race laps"""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from track import load_track
from vehicle import GEN3_EVO, mode
from gen4 import GEN4, KITS
from energy import lift_coast_for_budget
from lapsim import simulate
import ocp

ROOT = Path(__file__).resolve().parents[1]
E_GRID = np.arange(2.6, 3.81, 0.2)        # kWh/lap, same grid as run_energy.py
E_G3_RACE = (38.5 + 3.85) / 23            # Madrid 2026 race budget [kWh/lap]

kappa, ds = load_track()
out = {}

#Lambda variation with Gen4 Race mode
car = replace(GEN4, P_drive=450e3, **KITS["low-DF"])
guess = ocp.initial_guess(car, kappa, ds)
E0, d = 2.6, 0.01                         # small step: lambda changes quickly with E
r0 = ocp.solve(car, kappa, ds, E_max=E0, guess=guess)
r_lo = ocp.solve(car, kappa, ds, E_max=E0 - d, guess=guess)
r_hi = ocp.solve(car, kappa, ds, E_max=E0 + d, guess=guess)
lam_fd = (r_lo["lap_time"] - r_hi["lap_time"]) / (2 * d)
print(f"A) GEN4 low-DF, {E0} kWh/lap: lambda solver {r0['lam']:.2f} s/kWh | finite differences {lam_fd:.2f} s/kWh")
out["lambda_check"] = dict(E=E0, lam_solver=r0["lam"], lam_fd=lam_fd)

#GEN4: optimal vs uniform lift-and-coast
out["gen4"] = {}
for kit, aero in KITS.items():
    car = replace(GEN4, P_drive=450e3, **aero)
    guess = ocp.initial_guess(car, kappa, ds)
    # flat-out reference of each method: the comparison is on the COST of saving energy,
    # so the ~0.2 s discretisation offset between QSS and OCP (step 1) cancels out
    T0_ocp = ocp.solve(car, kappa, ds, guess=guess)["lap_time"]
    T0_qss = simulate(car, kappa, ds)["lap_time"]
    rows = []
    for E in E_GRID:
        o = ocp.solve(car, kappa, ds, E_max=E, guess=guess)
        _, lc = lift_coast_for_budget(car, kappa, ds, E)
        cost_ocp, cost_lc = o["lap_time"] - T0_ocp, lc["lap_time"] - T0_qss
        rows.append(dict(E=float(E), T_ocp=o["lap_time"], T_lc=lc["lap_time"], lam=o["lam"],
                         cost_ocp=cost_ocp, cost_lc=cost_lc))
        print(f"B) GEN4 {kit:7} E {E:.1f} | time cost of saving: optimal {cost_ocp:5.2f} s, "
              f"uniform L&C {cost_lc:5.2f} s -> gain {cost_lc - cost_ocp:4.2f} s | lambda {o['lam']:.2f} s/kWh")
    out["gen4"][kit] = dict(T0_ocp=T0_ocp, T0_qss=T0_qss, rows=rows)

#Gen3 Evo on the Madrid race budget
g3 = mode(GEN3_EVO, 300)
T0_ocp = ocp.solve(g3, kappa, ds)["lap_time"]
o = ocp.solve(g3, kappa, ds, E_max=E_G3_RACE)
_, lc = lift_coast_for_budget(g3, kappa, ds, E_G3_RACE)
print(f"C) Gen3 {E_G3_RACE:.2f} kWh/lap | optimal {o['lap_time']:.2f} s (flat {T0_ocp:.2f}) | uniform L&C "
      f"{lc['lap_time']:.2f} s | best normal race laps 94.8-95.7 s | lambda {o['lam']:.2f} s/kWh")
out["gen3"] = dict(E=E_G3_RACE, T0_ocp=T0_ocp, T_ocp=o["lap_time"], T_lc=lc["lap_time"], lam=o["lam"],
                   v_ocp=(o["v"] * 3.6).tolist(), v_lc=(lc["v"] * 3.6).tolist())

(ROOT / "results").mkdir(exist_ok=True)
json.dump(out, open(ROOT / "results" / "ocp_results.json", "w"), indent=1)
print("wrote", ROOT / "results" / "ocp_results.json")