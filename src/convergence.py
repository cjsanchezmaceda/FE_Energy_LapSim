"""Discretisation check: QSS and OCP lap time vs step size (GEN4 low-DF, 450 kW, no energy limit)"""
from dataclasses import replace

from track import load_track
from gen4 import GEN4, KITS
from lapsim import simulate
import ocp

car = replace(GEN4, P_drive=450e3, **KITS["low-DF"])

print(f"{'ds [m]':>6} {'QSS [s]':>8} {'OCP [s]':>8} {'diff [s]':>9}")
for step in (4.0, 2.0, 1.0):
    kappa, ds = load_track(step)              # same track, resampled every `step` metres
    q = simulate(car, kappa, ds)["lap_time"]
    o = ocp.solve(car, kappa, ds)["lap_time"]
    print(f"{ds:6.0f} {q:8.2f} {o:8.2f} {o - q:+9.2f}")