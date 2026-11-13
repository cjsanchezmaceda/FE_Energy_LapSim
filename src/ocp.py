"""Minimum-time lap with an energy budget, as an optimal control problem (OCP)"""
import time

import numpy as np
import casadi as ca

from vehicle import G, RHO
from lapsim import simulate

SB, SF = 1e3, 1e4   # scaling: v^2 ~ 1e3 m^2/s^2, forces ~ 1e4 N -> the solver works with numbers ~1


def initial_guess(car, kappa, ds):
    """Flat-out QSS lap -> starting point for v^2 and the forces (sec. 9)."""
    v = simulate(car, kappa, ds)["v"]
    vn = np.roll(v, -1)
    bm = 0.5 * (v**2 + vn**2)
    q = 0.5 * RHO * bm
    D = q * car.cdA + car.Crr * (car.m * G + q * car.clA)
    F = car.m * (vn**2 - v**2) / (2 * ds) + D           # net tyre force needed in each segment
    Fd = np.maximum(F, 0)
    Fb = np.maximum(-F, 0)
    Fr = np.minimum(Fb, (car.P_regen_f + car.P_regen_r) / car.eta_r / np.sqrt(bm))
    return dict(b=v**2, Fd=Fd, Fr=Fr, Ff=Fb - Fr)


def solve(car, kappa, ds, E_max=None, guess=None, verbose=False):
    """Optimal lap. E_max [kWh/lap] = energy budget, None = unlimited"""
    
    n = len(kappa)
    W = car.m * G
    hl = car.h_cog / car.wheelbase
    opti = ca.Opti()

    b   = SB * opti.variable(n)         # v^2 at each point
    Fd  = SF * opti.variable(n)         # total drive force
    Fdf = SF * opti.variable(n)         # front-axle share of the drive force
    Fr  = SF * opti.variable(n)         # total regen braking force
    Frr = SF * opti.variable(n)         # rear-axle share of the regen force
    Ff  = SF * opti.variable(n)         # friction-brake force
    f   = opti.variable(n)              # grip fraction left after cornering
    Fdr, Frf, Fb = Fd - Fdf, Fr - Frr, Fr + Ff

    b_next = ca.vertcat(b[1:], b[0])    # periodic: point after the last is the first
    bm = 0.5 * (b + b_next)             # mean v^2 of each segment
    vm = ca.sqrt(bm)
    q = 0.5 * RHO * bm
    N = car.m * G + q * car.clA         # vertical load: weight + downforce
    D = q * car.cdA + car.Crr * N       # drag + rolling resistance
    Fy = car.m * bm * np.abs(kappa)     # lateral force to follow the line

    opti.subject_to(car.m * (b_next - b) / (2 * ds) == Fd - Fr - Ff - D)
    opti.subject_to(f**2 + (Fy / (car.mu * N))**2 <= 1)
    opti.subject_to((Fdr * (1 - car.mu * f * hl) - car.mu * f * (1 - car.wf) * N) / W <= 0)
    if car.awd:
        opti.subject_to((Fdf - car.mu * f * car.wf * N) / W <= 0)
        opti.subject_to(Fdf * vm <= car.eta_d * car.P_front)
    else:
        opti.subject_to(Fdf == 0)
    opti.subject_to(Fd * vm <= car.eta_d * car.P_drive)
    opti.subject_to(Frr * vm * car.eta_r <= car.P_regen_r)
    opti.subject_to(Frf * vm * car.eta_r <= car.P_regen_f)
    opti.subject_to((Frr - car.mu * f * ((1 - car.wf) * N - Fb * hl)) / W <= 0)
    if car.rear_friction_brakes:
        opti.subject_to((Fb**2 + Fy**2 - (car.mu * N)**2) / W**2 <= 0)
    else:
        opti.subject_to((Fb - Frr - car.mu * f * (car.wf * N + Fb * hl)) / W <= 0)
    for x in (Fdf, Fdr, Fr, Frr, Frf, Ff, f):
        opti.subject_to(x >= 0)
    opti.subject_to(opti.bounded(1.0, b, 100.0**2))

    E = ca.sum1((Fd / car.eta_d - car.eta_r * Fr) * ds) / 3.6e6
    g_E = None
    if E_max is not None:
        g_E = E <= E_max
        opti.subject_to(g_E)

    T = ca.sum1(ds / vm)
    opti.minimize(T)

    g = guess or initial_guess(car, kappa, ds)
    opti.set_initial(b, g["b"]); opti.set_initial(Fd, g["Fd"])
    opti.set_initial(Fr, g["Fr"]); opti.set_initial(Ff, g["Ff"]); opti.set_initial(f, 0.5)
    opti.solver("ipopt", {"print_time": False},
                {"print_level": 5 if verbose else 0, "max_iter": 3000, "tol": 1e-8,
                 "mu_strategy": "adaptive"})
    t0 = time.time()
    sol = opti.solve()

    out = dict(lap_time=float(sol.value(T)), E_net=float(sol.value(E)),
               v=np.sqrt(sol.value(b)), Fd=sol.value(Fd), Fr=sol.value(Fr), Ff=sol.value(Ff),
               cpu=time.time() - t0)
    if g_E is not None:
        out["lam"] = float(sol.value(opti.dual(g_E)))
    return out