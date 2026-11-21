'''Inverse calibration: what grip / downforce each power-kit hypothesis needs to match the test laps.'''

import json
from dataclasses import replace
from pathlib import Path
from scipy.optimize import brentq
from track import load_track
from gen4 import GEN4, KITS
from lapsim import simulate

ROOT = Path(__file__).resolve().parents[1]
kappa, ds = load_track()
rows = []
TARGETS = {"Maloney": 83.838, "Drugovich": 84.544, "Mortara": 84.344}
V_TRAP = 277.2                       # km/h, Mortara's lap
MU_GEN3 = 1.689

def lap(car):
    return simulate(car, kappa, ds)["lap_time"]

def vmax(car):
    return simulate(car, kappa, ds)["v"].max() * 3.6

for P in (450e3, 600e3):
    for kit, aero in KITS.items():
        base = replace(GEN4, P_drive=P, **aero)
        # drag area at which the model's top speed equals the trap speed
        cdA_trap = brentq(lambda c: vmax(replace(base, cdA=c)) - V_TRAP, 0.3, 2.5)
        print(f"\n{P/1e3:.0f} kW {kit}: model {lap(base):.2f} s, vmax {vmax(base):.1f} km/h,"
              f" CdA for vmax = {V_TRAP}: {cdA_trap:.2f} m2 (assumed {aero['cdA']})")
        for who, T in TARGETS.items():
            mu = brentq(lambda m: lap(replace(base, mu=m)) - T, 0.8, 3.0)
            clA = brentq(lambda c: lap(replace(base, clA=c)) - T, 0.0, 10.0)
            rows.append(dict(P=P/1e3, kit=kit, who=who, T=T, mu=mu, clA=clA,
                             cdA_trap=cdA_trap, cdA=aero["cdA"], clA_assumed=aero["clA"]))
            print(f"   {who:9} {T:.3f}  mu {mu:.3f} ({mu/MU_GEN3-1:+.0%} vs Gen3)"
                  f"  clA {clA:.2f} (assumed {aero['clA']}, Gen3 1.6)")

(ROOT / "results").mkdir(exist_ok=True)
json.dump(rows, open(ROOT / "results" / "inverse_calibration.json", "w"), indent=1)
print("wrote", ROOT / "results" / "inverse_calibration.json")