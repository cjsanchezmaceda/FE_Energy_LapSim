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
    up = np.roll(v, -1) > v + 1e-9
    mask = np.zeros(n, dtype=bool)
    start = np.where(up & ~np.roll(up, 1))[0][0]
    run, lifted = [], False
    for j in (np.arange(n) + start) % n:
        if up[j]:
            lifted = False
            run.append(j)
        else:
            if run:
                k = int(round(frac * len(run)))
                if k:
                    mask[run[-k:]] = True
                    lifted = True
                run = []
            if lifted:
                mask[j] = True                # no throttle again until the next acceleration phase
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