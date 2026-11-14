"""Annex figures: where the energy goes, on the track map and in one corner"""
from dataclasses import replace
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from scipy.signal import find_peaks

from track import load_track
from vehicle import G, RHO
from gen4 import GEN4, KITS
from energy import lift_coast_for_budget, coast_mask
from lapsim import simulate
import ocp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
E_MAX, F_ON = 2.6, 100.0
CORNERS = {540: "T1", 880: "T2", 1120: "T3", 1230: "T4", 1460: "T5", 2100: "T7",
           2810: "T9", 3200: "T10", 3420: "T11", 3770: "T12-13"}

# phase codes and colours (one per phase, fixed)
THROTTLE, COAST, REGEN, FRICTION = 0, 1, 2, 3
NAMES = ["throttle", "coast", "regen-only braking", "friction braking"]
COLS = ["#2a78d6", "#c9c8c3", "#1baf7a", "#eb6834"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.titleweight": "bold", "legend.frameon": False,
                     "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2})

kappa, ds, xy = load_track(with_xy=True)
car = replace(GEN4, P_drive=450e3, **KITS["low-DF"])
n = len(kappa)
s = np.arange(n) * ds


def phases_from_forces(Fd, Fr, Ff):
    """Optimal lap: the solver gives the forces directly."""
    p = np.full(n, COAST)
    p[Fr > F_ON] = REGEN
    p[Ff > F_ON] = FRICTION
    p[Fd > F_ON] = THROTTLE
    return p


def phases_from_qss(v, mask):
    """Fixed rule (QSS): rebuild the net tyre force from the speed trace, as in lapsim.py."""
    vn = np.roll(v, -1)
    vm = 0.5 * (v + vn)
    q = 0.5 * RHO * vm**2
    D = q * car.cdA + car.Crr * (car.m * G + q * car.clA)
    F = car.m * (vn**2 - v**2) / (2 * ds) + D             # net tyre force in each segment
    cap = (car.P_regen_f + car.P_regen_r) / car.eta_r      # regen power limit at the wheel
    p = np.full(n, THROTTLE)
    braking = F < -F_ON
    p[braking] = REGEN
    p[braking & (-F * vm > cap)] = FRICTION                # braking power above the regen limit
    p[mask & ~braking] = COAST
    return p


o = ocp.solve(car, kappa, ds, E_max=E_MAX)
ph_ocp = phases_from_forces(o["Fd"], o["Fr"], o["Ff"])
flat = simulate(car, kappa, ds)
fr, lc = lift_coast_for_budget(car, kappa, ds, E_MAX)
ph_lc = phases_from_qss(lc["v"], coast_mask(flat["v"], fr))

# ---- Figure A1: phase maps, optimal vs fixed rule ----------------------------------------------
cmap = ListedColormap(COLS)
norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)
pts = np.r_[xy, xy[:1]]
segs = np.stack([pts[:-1], pts[1:]], axis=1)
apex, _ = find_peaks(-np.r_[o["v"], o["v"]], prominence=10 / 3.6)
apex = np.unique(apex % n)

fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.4))
for ax, ph, title, T in ((axs[0], ph_ocp, "Optimal", o["lap_time"]),
                         (axs[1], ph_lc, "Fixed lift-and-coast rule", lc["lap_time"])):
    lc_col = LineCollection(segs, cmap=cmap, norm=norm, linewidths=4.0, capstyle="butt")
    lc_col.set_array(ph)
    ax.add_collection(lc_col)
    labelled = set()
    for i in apex:
        name = min(CORNERS, key=lambda c: abs(c - s[i]))
        if abs(name - s[i]) < 40 and name not in labelled:      # one label per corner
            labelled.add(name)
            ax.annotate(CORNERS[name], xy[i], xytext=(6, 6), textcoords="offset points",
                        fontsize=7.5, color=INK2)
    ax.annotate("start", xy[0], xytext=(-28, -12), textcoords="offset points", fontsize=7.5, color=INK2)
    ax.set_aspect("equal"); ax.autoscale(); ax.axis("off")
    share = [np.mean(ph == k) * 100 for k in range(4)]
    ax.set_title(f"{title}: {T:.2f} s\n" + " · ".join(f"{NAMES[k].split()[0]} {share[k]:.0f}%" for k in range(4)),
                 loc="left", fontsize=9)
fig.legend(handles=[Patch(color=c, label=l) for c, l in zip(COLS, NAMES)], loc="lower center",
           ncol=4, fontsize=8)
fig.suptitle(f"GEN4 low-DF, 450 kW, {E_MAX} kWh/lap: what the car does along the lap",
             x=0.02, ha="left", fontweight="bold", fontsize=10)
fig.tight_layout(rect=(0, 0.06, 1, 0.95))
fig.savefig(OUT / "figA1_phase_map.png", dpi=250)
plt.close(fig)
print("wrote", OUT / "figA1_phase_map.png")

# ---- Figure A2: T2 in detail on the optimal lap -------------------------------------------------
a, b = 740, 960
z = (s >= a) & (s <= b)
v = o["v"] * 3.6
fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.2, 4.4), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1]))
for i in np.where(z)[0]:
    for x in (ax, bx):
        x.axvspan(s[i], s[i] + ds, color=COLS[ph_ocp[i]], alpha=0.18, lw=0)
ax.plot(s[z], v[z], color=INK, lw=1.8)
i_min = np.where(z)[0][np.argmin(v[z])]
ax.annotate(f"apex {v[i_min]:.0f} km/h", (s[i_min], v[i_min]), xytext=(10, 4),
            textcoords="offset points", fontsize=8, color=INK2)
ax.set_ylabel("speed [km/h]")
ax.set_title(f"T2 on the optimal lap: coast, regen braking that eases off into the corner, throttle at the apex",
             loc="left", fontsize=9)
bx.plot(s[z], o["Fd"][z] / 1e3, color=COLS[THROTTLE], lw=1.6, label="drive force")
bx.plot(s[z], -o["Fr"][z] / 1e3, color=COLS[REGEN], lw=1.6, label="regen braking force")
bx.axhline(0, color=INK2, lw=0.8)
bx.set_ylabel("force [kN]"); bx.set_xlabel("distance [m]"); bx.set_xlim(a, b)
bx.legend(loc="lower left", fontsize=7.5)
for x in (ax, bx):
    x.grid(True, color=GRID); x.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "figA2_T2_detail.png", dpi=250)
plt.close(fig)
print("wrote", OUT / "figA2_T2_detail.png")