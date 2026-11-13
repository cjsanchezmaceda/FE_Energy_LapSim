"""Step 1: with no energy limit, the OCP must reproduce the QSS lap"""
from dataclasses import replace

import numpy as np

from track import load_track
from vehicle import GEN3_EVO, mode
from gen4 import GEN4, KITS
from lapsim import simulate
import ocp

kappa, ds = load_track()

cases = {
    "Gen3 Evo 300 kW":       mode(GEN3_EVO, 300),
    "Gen3 Evo 350 kW + AWD": mode(GEN3_EVO, 350, awd=True),
    "GEN4 low-DF 450 kW":    replace(GEN4, P_drive=450e3, **KITS["low-DF"]),
    "GEN4 high-DF 600 kW":   replace(GEN4, P_drive=600e3, **KITS["high-DF"]),
}

print(f"{'case':24} {'QSS [s]':>8} {'OCP [s]':>8} {'diff':>7} {'max |dv| [km/h]':>16} {'cpu [s]':>8}")
for name, car in cases.items():
    q = simulate(car, kappa, ds)
    o = ocp.solve(car, kappa, ds)
    dv = np.abs(o["v"] - q["v"]).max() * 3.6
    print(f"{name:24} {q['lap_time']:8.2f} {o['lap_time']:8.2f} {o['lap_time'] - q['lap_time']:+7.2f} "
          f"{dv:16.1f} {o['cpu']:8.1f}")