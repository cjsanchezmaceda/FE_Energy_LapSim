"""Report figures for the optimal-control study"""
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
R = json.load(open(ROOT / "results" / "ocp_results.json"))
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# same colours as figures.py: one per entity (low-DF blue, high-DF orange, Gen3 grey)
BLUE, ORANGE, GREY, AQUA = "#2a78d6", "#eb6834", "#8a8984", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelcolor": INK,
    "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.8,
})
KIT_COL = {"low-DF": BLUE, "high-DF": ORANGE}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=250)
    plt.close(fig)
    print("wrote", OUT / name)


def crossover(E, t_low, t_high):
    """Energy per lap where both kits have the same lap time (linear interpolation)."""
    d = np.asarray(t_high) - np.asarray(t_low)
    i = np.where(np.diff(np.sign(d)) != 0)[0]
    if len(i) == 0:
        return None
    i = i[0]
    return E[i] - d[i] * (E[i + 1] - E[i]) / (d[i + 1] - d[i])


# ---- Figure 3: lap time and value of energy vs budget, GEN4 450 kW ----------------------------
fig, (ax, bx) = plt.subplots(1, 2, figsize=(8.6, 3.5))
lap = {}
for kit, col in KIT_COL.items():
    rows = R["gen4"][kit]["rows"]
    E = np.array([r["E"] for r in rows])
    T_ocp = np.array([r["T_ocp"] for r in rows])
    T_lc = np.array([r["T_lc"] for r in rows])
    lap[kit] = (E, T_ocp, T_lc)
    ax.plot(E, T_ocp, color=col, marker="o", ms=3.5, label=f"{kit}, optimal")
    ax.plot(E, T_lc, color=col, ls="--", lw=1.3, label=f"{kit}, uniform lift-and-coast")
    bx.plot(E, [r["lam"] for r in rows], color=col, marker="o", ms=3.5, label=kit)

E = lap["low-DF"][0]
for k, (ls, name) in enumerate(((1, "optimal"), (2, "uniform"))):
    Ex = crossover(E, lap["low-DF"][ls], lap["high-DF"][ls])
    if Ex is not None:
        ax.axvline(Ex, color=INK2, lw=0.9, ls=":" if name == "optimal" else "-.")
        ax.text(Ex + 0.02, ax.get_ylim()[1] - 0.3 - 0.9 * k, f"kits cross ({name})\n{Ex:.2f} kWh/lap",
                fontsize=7.5, color=INK, va="top")
ax.set_xlabel("battery energy per lap [kWh]"); ax.set_ylabel("lap time [s]")
ax.set_title("GEN4, 450 kW: lap time on an energy budget", loc="left")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=7.5)
bx.set_xlabel("battery energy per lap [kWh]"); bx.set_ylabel("value of energy, $\\lambda$ [s per kWh]")
bx.set_title("Lap time gained per extra kWh", loc="left")
bx.legend(loc="upper right", fontsize=8)
save(fig, "fig3_ocp_energy_gen4.png")

# ---- Figure 4: Gen3 Evo into T1 on the Madrid race budget -------------------------------------
g = R["gen3"]
ds = g["ds"]
v_o, v_l = np.array(g["v_ocp"]), np.array(g["v_lc"])
Fd, Fr, Ff = np.array(g["Fd"]), np.array(g["Fr"]), np.array(g["Ff"])
s = np.arange(len(v_o)) * ds
z = (s >= 150) & (s <= 600)                     # main straight into T1

fig, ax = plt.subplots(figsize=(7.2, 3.0))
# shade what the optimal driver is doing: coast (no drive, no brakes) and regen-only braking
coast = (Fd < 100) & (Fr < 100) & (Ff < 100)
regen = (Fr > 100) & (Ff < 100)
for mask, col, lab in ((coast, GREY, "optimal: coast"), (regen, AQUA, "optimal: regen-only braking")):
    m = mask & z
    first = True
    for i in np.where(m)[0]:
        ax.axvspan(s[i], s[i] + ds, color=col, alpha=0.18, lw=0, label=lab if first else None)
        first = False
ax.plot(s[z], v_l[z], color=INK2, ls="--", lw=1.4, label=f"uniform lift-and-coast ({g['T_lc']:.2f} s/lap)")
ax.plot(s[z], v_o[z], color=INK, lw=1.8, label=f"optimal ({g['T_ocp']:.2f} s/lap)")
ax.set_xlim(150, 600); ax.set_ylim(0, None)
ax.set_xlabel("distance [m]"); ax.set_ylabel("speed [km/h]")
ax.set_title(f"Gen3 Evo into T1 on the Madrid race budget ({g['E']:.2f} kWh/lap)", loc="left")
ax.legend(loc="lower left", fontsize=7.5)
save(fig, "fig4_gen3_T1_strategy.png")