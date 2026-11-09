'''quasi-steady-state (QSS) point-mass lap simulation with an electric energy model'''
import numpy as np
from vehicle import G, RHO

def forces(car, v):
    '''Resistive force (drag + rolling) and total vertical load at speed v'''
    F_res = 1/2*RHO*car.cdA*v*v + car.Crr*(car.m*G + 1/2*RHO*car.clA*v*v)
    F_ver = car.m*G + 1/2*RHO * car.clA*v* v
    return F_res, F_ver

def v_lateral(car, kappa):
    '''Cornering speed limit at every point (pure lateral grip, incl. downforce)'''
    k = np.abs(kappa)
    den = k - 1/2*(RHO*car.clA*car.mu/car.m)
    v = np.full_like(k, 100)
    ok = den > 1e-9
    v[ok] = np.sqrt(G*car.mu/den[ok])
    return np.minimum(v, 100.0)

def grip_fraction(car, v, kappa):
    '''Share of grip left for longitudinal force after cornering (friction circle)'''
    _, N = forces(car,v)
    ay_ratio = min(car.m*v*v*abs(kappa)/(car.mu*N),1.0)
    return np.sqrt(1-ay_ratio**2),N

def accel(car, v, kappa):
    '''Max longitudinal acceleration: traction (with load transfer) or power, minus resistance'''
    Fres, _ = forces(car,v)
    f, N = grip_fraction(car,v,kappa)
    hl = car.h_cog/car.wheelbase
    vv = max(v,1.0)
    F = car.mu*f*(1-car.wf)*N/(1-hl*car.mu*f)
    if car.awd:
       F += min(car.mu*f*car.wf*N, car.P_front*car.eta_d/vv)
    F = min(F, car.P_drive*car.eta_d/vv)
    return (F-Fres)/car.m

def decel(car, v, kappa):
    '''Max deceleration: front friction + rear regen-only braking, with load transfer'''
    Fres, _ = forces(car, v)
    f, N = grip_fraction(car,v,kappa)
    hl = car.h_cog/car.wheelbase
    if car.rear_friction_brakes:
        Fb = car.mu*f*N
    else:
        R = car.P_regen_r/(car.eta_r*max(v,1.0))
        Fb = min(car.mu*f*N,(car.mu*f*N*car.wf+R)/(1-car.mu*f*hl))
    return (Fb+Fres)/car.m

def simulate(car, kappa, ds, coast_mask=None):
    '''Flying lap. Returns speed profile, lap time [s] and battery energy [kWh]'''
    n = len(kappa)
    vlat = v_lateral(car, kappa)
    k2, vl2 = np.r_[kappa, kappa], np.r_[vlat, vlat]

    #backward pass
    vb = vl2.copy()
    for i in range(2*n-2, -1, -1):
        vb[i] = min(vl2[i], np.sqrt(vb[i+1]**2 + 2*decel(car,vb[i+1], k2[i+1])*ds))

    m2 = np.zeros(2*n, dtype = bool) if coast_mask is None else np.r_[coast_mask, coast_mask]    
    #forward pass
    v = np.empty(2*n)
    v[0] = vb[0]
    for i in range(2*n-1):
        if m2[i]:
            a = -forces(car, v[i])[0]/car.m # coasting: no drive, only drag + rolling
        else:
            a = accel(car,v[i],k2[i])
        v[i+1] = min(vb[i+1], np.sqrt(max(v[i]**2+2*a*ds,1)))
    v = v[n:]

    v_next = np.roll(v,-1)
    v_mid = 0.5*(v + v_next)
    dt = ds/v_mid
    Fres, _ = forces(car,v_mid)
    P_wheel = (car.m*(v_next**2- v**2)/(2*ds)+Fres)*v_mid
    E_drive = np.where(P_wheel > 0, P_wheel/car.eta_d, 0)*dt
    P_brake = np.where(P_wheel < 0, -P_wheel, 0)
    P_regen = np.minimum(P_brake, (car.P_regen_f + car.P_regen_r)/car.eta_r)
    E_regen = P_regen*car.eta_r*dt
    return dict(v=v, lap_time=dt.sum(),
                E_net=(E_drive.sum()-E_regen.sum())/(3600*1000),
                E_drive=E_drive.sum()/(3600*1000),
                E_regen=E_regen.sum()/(3600*1000))