'''Module 4: calibrate tyre grip on FP1 300 kW lap, validate on 350 kW + AWD.'''
from dataclasses import replace
from scipy.optimize import brentq

from vehicle import GEN3_EVO, mode
from lapsim import simulate
from track import load_track

#FIA, Madrid E-prix 2026, FP1 (dry)
T300_FP1 = 91.612 # FP1 best 300 kW lap (Da Costa)
T350_FP1 = 89.403 # FP1 best 350 kW lap (Ticktum)

def fit_mu(car, kappa, ds, T_target=T350_FP1, lo=1.2, hi=2.2):
    '''mu such that simulated lap-time equals T_target'''
    f = lambda mu: simulate(replace(car, mu=mu), kappa, ds)['lap_time']-T_target
    return brentq(f, lo, hi, xtol=1e-4)

def calibrate_and_check(car, kappa, ds, awd_350):
    c350 = mode(car, 350, awd=awd_350)
    mu = fit_mu(c350, kappa, ds)
    r350 = simulate(replace(c350, mu=mu), kappa, ds)
    r300 = simulate(mode(car, 300, awd=False, mu=mu), kappa, ds)
    return dict(mu=mu, T350=r350['lap_time'], T300=r300['lap_time'],
                d300=r300['lap_time']-T300_FP1,
                vmax350=r350['v'].max()*3.6,
                E300=r300['E_net'])

if __name__ == '__main__':
    kappa, ds = load_track()
    for awd in (False, True):
        for cdA in (0.75, 0.9, 1.05):
            r = calibrate_and_check(replace(GEN3_EVO, cdA=cdA), kappa, ds, awd)
            print(f'AWD{str(awd):5} cdA {cdA:.2f} | mu {r['mu']:.3f} | T350 {r['T350']:.3f} |'
                  f'T300 {r['T300']:.2f} (vs FIA {r['d300']:+.2f}s) | vmax {r['vmax350']:.0f} km/h')
            