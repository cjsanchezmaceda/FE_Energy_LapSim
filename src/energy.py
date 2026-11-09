'''Energy management: fastest lap for a given battery energy per lap.
Two ways to save energy:
  - lift-and-coast: lift off before each braking point (no drive, no regen)
  - power cap: lower the maximum drive power everywhere'''
import numpy as np
from dataclasses import replace
from scipy.optimize import brentq

from lapsim import simulate

def coast_mask(v, frac):
    '''Coast over the last 'frac' of every acceleration phase of a flat-out lap.
    Acceleration phase = consecutive points where speed rises (closed lap)'''
    n = len(v)
    up = np.roll(v, -1) > v + 1e-9           # speed rises from i to i+1
    mask = np.zeros(n, dtype=bool)
    start = np.argmin(up)                     # start the walk at a point that is NOT accelerating
    run = []
    for j in (np.arange(n + 1) + start) % n:  # n+1 steps: ends back at `start`, closing the last run
        if up[j]:
            run.append(j)
        elif run:
            k = int(round(frac * len(run)))
            if k:
                mask[run[-k:]] = True         # last k points before the braking point
            run = []
    return mask

def lift_coast_for_budget(car, kappa, ds, E_target):
    """Coast fraction that makes the lap use E_target kWh, and that lap."""
    flat = simulate(car, kappa, ds)
    if flat["E_net"] <= E_target:
        return 0.0, flat
    run = lambda fr: simulate(car, kappa, ds, coast_mask(flat["v"], fr))
    fr = brentq(lambda fr: run(fr)["E_net"] - E_target, 0.0, 0.95, xtol=1e-3)
    return fr, run(fr)

def power_cap_for_budget(car, kappa, ds, E_target):
    """Drive-power cap [W] that makes the lap use E_target kWh, and that lap."""
    run = lambda P: simulate(replace(car, P_drive=P), kappa, ds)
    if run(car.P_drive)["E_net"] <= E_target:
        return car.P_drive, run(car.P_drive)
    P = brentq(lambda P: run(P)["E_net"] - E_target, 50e3, car.P_drive, xtol=200)
    return P, run(P)