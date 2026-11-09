"""Does the GEN4 kit conclusion survive the assumptions?

For each case, one assumption is changed and the lap-time gap high-DF - low-DF is computed
  - flat-out at 450 kW (no energy limit)
  - with 3.0 kWh/lap (lift-and-coast)
Negative = high-DF faster.  Run from the repo root:  python src/sensitivity.py
"""
from dataclasses import replace

from track import load_track
from lapsim import simulate
from gen4 import GEN4, KITS, mu_Gen3, TYRE
from energy import lift_coast_for_budget

E_REF = 3.0  # kWh/lap
LOW, HIGH = KITS["low-DF"], KITS["high-DF"]

# (label, tyre factor, high-DF aero)   -- low-DF aero stays nominal
CASES = [
    ("Nominal",            TYRE, HIGH),
    ("Tyre factor 1.00",   1.00, HIGH),
    ("Tyre factor 1.10",   1.10, HIGH),
    ("High-DF ClA -15 %",  TYRE, dict(HIGH, clA=HIGH["clA"] * 0.85)),
    ("High-DF ClA +15 %",  TYRE, dict(HIGH, clA=HIGH["clA"] * 1.15)),
    ("High-DF CdA -10 %",  TYRE, dict(HIGH, cdA=HIGH["cdA"] * 0.90)),
    ("High-DF CdA +10 %",  TYRE, dict(HIGH, cdA=HIGH["cdA"] * 1.10)),
]


def gap(tyre, high, kappa, ds):
    lo = replace(GEN4, P_drive=450e3, mu=mu_Gen3 * tyre, **LOW)
    hi = replace(GEN4, P_drive=450e3, mu=mu_Gen3 * tyre, **high)
    d_flat = simulate(hi, kappa, ds)["lap_time"] - simulate(lo, kappa, ds)["lap_time"]
    d_E = (lift_coast_for_budget(hi, kappa, ds, E_REF)[1]["lap_time"]
           - lift_coast_for_budget(lo, kappa, ds, E_REF)[1]["lap_time"])
    return d_flat, d_E


if __name__ == "__main__":
    kappa, ds = load_track()
    print(f"{'case':20} {'flat-out':>9} {f'{E_REF} kWh/lap':>13}")
    for label, tyre, high in CASES:
        d_flat, d_E = gap(tyre, high, kappa, ds)
        print(f"{label:20} {d_flat:+9.2f} {d_E:+13.2f}")