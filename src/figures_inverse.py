import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
rows = json.load(open(ROOT / "results" / "inverse_calibration.json"))
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE = "#2a78d6", "#eb6834"          # same colours as the other reports: low-DF, high-DF
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelcolor": INK,
    "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
})
KIT_COL = {"low-DF": BLUE, "high-DF": ORANGE}
CASES = [(450, "low-DF"), (450, "high-DF"), (600, "low-DF"), (600, "high-DF")]
LABELS = [f"{P} kW\n{kit}" for P, kit in CASES]
MARK = {"Maloney": "o", "Drugovich": "s", "Mortara": "^"}
LAP = {"Maloney": "83.838 (best, Fri)", "Drugovich": "84.544 (Andretti, Fri)", "Mortara": "84.344 (Mon, trap lap)"}
x = np.arange(len(CASES))

fig, (ax, bx) = plt.subplots(1, 2, figsize=(8.6, 3.6))

# ---- left: grip needed ----
for who, mk in MARK.items():
    for i, (P, kit) in enumerate(CASES):
        r = next(r for r in rows if r["P"] == P and r["kit"] == kit and r["who"] == who)
        ax.plot(i + (list(MARK).index(who) - 1) * 0.12, r["mu"], mk, ms=5, color=KIT_COL[kit],
                mec=INK, mew=0.5, label=LAP[who] if i == 0 else None)
ax.axhline(1.689, color=INK2, lw=1, ls="--")
ax.axhline(1.689 * 1.05, color=INK2, lw=1, ls=":")
ax.text(3.45, 1.689, "Gen3 (calibrated)", fontsize=7, va="bottom", ha="right", color=INK2)
ax.text(3.45, 1.689 * 1.05, "GEN4 assumed", fontsize=7, va="bottom", ha="right", color=INK2)
ax.set_xticks(x, LABELS); ax.set_xlim(-0.5, 3.5)
ax.set_ylabel("tyre grip needed, $\\mu$ [-]")
ax.set_title("Grip needed to match the test laps", loc="left")
leg = ax.legend(loc="upper right", fontsize=7, handletextpad=0.3)
for h in leg.legend_handles:
    h.set_color(INK2)

# ---- right: drag area allowed by the trap speed ----
for i, (P, kit) in enumerate(CASES):
    r = next(r for r in rows if r["P"] == P and r["kit"] == kit)
    bx.bar(i, r["cdA_trap"], width=0.55, color=KIT_COL[kit], alpha=0.35, edgecolor=KIT_COL[kit])
    bx.plot([i - 0.32, i + 0.32], [r["cdA"]] * 2, color=INK, lw=2)
    ok = r["cdA"] <= r["cdA_trap"]
    bx.text(i, max(r["cdA_trap"], r["cdA"]) + 0.05, "passes" if ok else f"needs {r['cdA_trap']/r['cdA']-1:+.0%} drag",
            ha="center", fontsize=7.5, color=INK)
bx.plot([], [], color=INK, lw=2, label="assumed $c_dA$")
bx.set_xticks(x, LABELS); bx.set_ylim(0, 2.0)
bx.set_ylabel("drag area, $c_dA$ [m$^2$]")
bx.set_title("Speed trap (Mortara, Mon PM)", loc="left")
h, l = bx.get_legend_handles_labels()
h.append(Patch(facecolor=INK2, alpha=0.35, edgecolor=INK2)); l.append("largest $c_dA$ that reaches 277.2 km/h")
bx.legend(h, l, loc="upper left", fontsize=7)

fig.tight_layout()
fig.savefig(OUT / "fig5_jarama_inverse.png", dpi=250)
print("wrote", OUT / "fig5_jarama_inverse.png")