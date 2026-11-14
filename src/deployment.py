"""Energy deployment map: what the optimal lap does into each corner.

GEN4 low-DF at race power (450 kW) on a given energy budget"""
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks

from track import load_track
from gen4 import GEN4, KITS
import ocp

ROOT = Path(__file__).resolve().parents[1]
E_MAX = 2.6          # kWh/lap (about a 20-lap race on 51.25 kWh)
F_ON = 100.0         # N: a force below this counts as zero
# approximate apex positions on the model's distance axis (s = 0 at the exit of the FE loop)
CORNERS = {540: "T1", 880: "T2", 1120: "T3", 1230: "T4", 1460: "T5", 2100: "T7",
           2640: "T8", 2810: "T9", 3200: "T10", 3420: "T11", 3760: "T12", 3790: "T13"}

kappa, ds = load_track()
car = replace(GEN4, P_drive=450e3, **KITS["low-DF"])
o = ocp.solve(car, kappa, ds, E_max=E_MAX)
v = o["v"] * 3.6
n = len(v)
s = np.arange(n) * ds

# corners = speed minima; search on two laps so a minimum near s = 0 is not missed
apex, _ = find_peaks(-np.r_[v, v], prominence=10)
apex = np.unique(apex % n)

rows = []
for i in apex:
    j = i
    while v[(j - 1) % n] >= v[j] and (i - j) % n < 600:
        j = (j - 1) % n
    seg = (np.arange(j, j + (i - j) % n) % n)          # points from the speed peak to the apex
    Fd, Fr, Ff = o["Fd"][seg], o["Fr"][seg], o["Ff"][seg]
    friction = ds * np.sum(Ff > F_ON)
    regen = ds * np.sum((Fr > F_ON) & (Ff <= F_ON))
    throttle = ds * np.sum((Fd > F_ON) & (Fr <= F_ON) & (Ff <= F_ON))   # part throttle near the apex
    coast = len(seg) * ds - friction - regen - throttle
    name = min(CORNERS, key=lambda c: abs(c - s[i]))
    rows.append(dict(corner=CORNERS[name] if abs(name - s[i]) < 40 else f"s={s[i]:.0f}",
                     apex_s=float(s[i]), v_apex=float(v[i]), v_lift=float(v[j]),
                     lift_before_apex=float(len(seg) * ds), coast=float(coast), regen=float(regen),
                     friction=float(friction), throttle=float(throttle)))

print(f"GEN4 low-DF, 450 kW, {E_MAX} kWh/lap: optimal lap {o['lap_time']:.2f} s")
print(f"{'corner':7} {'v lift':>7} {'lift [m before apex]':>21} {'coast':>6} {'regen':>6} {'friction':>9} "
      f"{'throttle':>9} {'v apex':>7}")
for r in rows:
    print(f"{r['corner']:7} {r['v_lift']:7.0f} {r['lift_before_apex']:21.0f} {r['coast']:6.0f} "
          f"{r['regen']:6.0f} {r['friction']:9.0f} {r['throttle']:9.0f} {r['v_apex']:7.0f}")

(ROOT / "results").mkdir(exist_ok=True)
json.dump(dict(E_max=E_MAX, lap_time=o["lap_time"], rows=rows),
          open(ROOT / "results" / "deployment.json", "w"), indent=1)