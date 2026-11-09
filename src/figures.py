import json
from pathlib import Path
 
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
 
ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "results.json"
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
 
# colours: one per entity, fixed (low-DF / GEN4 = blue, high-DF = orange, Gen3 = grey)
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#8a8984"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelcolor": INK,
    "axes.edgecolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.8,
})
 
 
def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=250)
    plt.close(fig)
    print("wrote", OUT / name)
 
 
def fig_speed(R):
    """Speed vs distance, Gen3 Evo 350 kW vs GEN4 600 kW high-DF."""
    s = np.array(R["s"])
    v3, v4 = np.array(R["v_gen3"]), np.array(R["v_gen4"])
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.fill_between(s, v3, v4, where=v4 > v3, color=BLUE, alpha=0.12, lw=0)
    ax.plot(s, v3, color=GREY, label=f"Gen3 Evo, 350 kW + front motor ({R['T_gen3']:.2f} s, calibrated)")
    ax.plot(s, v4, color=BLUE, label=f"GEN4, 600 kW, high-DF ({R['T_gen4']:.2f} s)")
    ax.set_xlim(0, s[-1]); ax.set_ylim(0, None)
    ax.set_xlabel("distance [m]"); ax.set_ylabel("speed [km/h]")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=8)
    save(fig, "fig1_speed_gen3_gen4.png")
 
 
def extended(d):
    """Lift-and-coast curve plus the flat-out point (no saving needed beyond it)."""
    E = np.array(d["E"]); T = np.array(d["T_lc"])
    keep = E < d["E_flat"]
    return np.r_[E[keep], d["E_flat"]], np.r_[T[keep], d["T_flat"]]
 
 
def crossover(lo, hi):
    """Energy per lap where both kits have the same lift-and-coast lap time."""
    E = np.linspace(max(lo[0][0], hi[0][0]), hi[0][-1], 400)
    t_lo = np.interp(E, *lo, right=lo[1][-1])      # beyond its flat-out energy, low-DF stays flat-out
    t_hi = np.interp(E, *hi)
    d = t_hi - t_lo
    i = np.where(np.diff(np.sign(d)) != 0)[0]
    if len(i) == 0:
        return None
    i = i[0]
    return E[i] - d[i] * (E[i + 1] - E[i]) / (d[i + 1] - d[i])
 
 
def fig_energy(R):
    """GEN4 450 kW: lap time vs energy per lap, per kit and saving strategy."""
    g = R["gen4"]
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    curves = {}
    for kit, col in (("low-DF", BLUE), ("high-DF", ORANGE)):
        d = g[kit]
        E, T = extended(d)
        curves[kit] = (E, T)
        ax.plot(E, T, color=col, marker="o", ms=3.5, label=f"{kit}, lift-and-coast")
        Ec, Tc = np.array(d["E"]), np.array(d["T_cap"])
        keep = Ec < d["E_flat"]
        ax.plot(np.r_[Ec[keep], d["E_flat"]], np.r_[Tc[keep], d["T_flat"]],
                color=col, ls="--", lw=1.3, label=f"{kit}, power cap")
        ax.plot(d["E_flat"], d["T_flat"], marker="o", ms=7, mfc="white", mec=col, mew=1.6, zorder=5)
        off = (-6, -13) if kit == "low-DF" else (4, 6)
        ax.annotate("flat-out", (d["E_flat"], d["T_flat"]), xytext=off, textcoords="offset points",
                    ha="right" if kit == "low-DF" else "left", fontsize=7.5, color=INK2)
    Ex = crossover(curves["low-DF"], curves["high-DF"])
    if Ex is not None:
        ax.axvline(Ex, color=INK2, lw=0.9, ls=":")
        ax.text(Ex - 0.03, ax.get_ylim()[1] - 0.4, f"kits cross\n{Ex:.2f} kWh/lap",
                ha="right", va="top", fontsize=8, color=INK)
        y0 = ax.get_ylim()[0] + 0.3
        ax.text(Ex - 0.05, y0, "\u2190 low-DF faster", ha="right", fontsize=8, color=BLUE)
        ax.text(Ex + 0.05, y0 + 1.6, "high-DF faster \u2192", ha="left", fontsize=8, color=ORANGE)
    ax.set_xlabel("battery energy per lap [kWh]"); ax.set_ylabel("lap time [s]")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=7.5)
    save(fig, "fig2_energy_tradeoff_gen4.png")
    return Ex
 
 
if __name__ == "__main__":
    R = json.load(open(RES))
    fig_speed(R)
    Ex = fig_energy(R)
    print("crossover energy:", None if Ex is None else round(Ex, 3), "kWh/lap")