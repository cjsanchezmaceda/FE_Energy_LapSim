'''GEN4 projection at Jarama (FE layout) from the Gen3 Evo-calibrated model'''
from dataclasses import replace

from vehicle import GEN3_EVO, mode
from lapsim import simulate
from track import load_track

mu_Gen3 = 1.689  # calibration.py: FP1 350 kW lap, AWD=True, CdA=0.90

TYRE = 1.05 #grip increasing compared to Gen3 Hankook --> assumption
KITS = {'low-DF': dict(cdA=0.95, clA=2.7),
        'high-DF': dict(cdA=1.24, clA=3.8),
        }

GEN4 = replace(GEN3_EVO,
               m=1046, awd=True, P_front=250e3,
               P_regen_f=350e3, P_regen_r=350e3,
               wf=0.44, mu=mu_Gen3*TYRE,
               wheelbase=3.08,
               rear_friction_brakes=True)

if __name__ == '__main__':
    kappa, ds = load_track()
    ref = simulate(mode(GEN3_EVO, 350, awd=True, mu=mu_Gen3), kappa, ds)
    print(f'Gen3 Evo 350 kW reference   lap{ref['lap_time']:.2f}s')
    for kit, aero in KITS.items():
        for P in (450, 600):
            car = mode(replace(GEN4, **aero), P, awd=True)
            r = simulate(car, kappa, ds)
            print(f"GEN4 {kit:7} {P} kW   lap {r['lap_time']:.2f} s "
                  f"({r['lap_time'] - ref['lap_time']:+.2f})  vmax {r['v'].max()*3.6:.0f} km/h  "
                  f"vmin {r['v'].min()*3.6:.0f} km/h  E {r['E_net']:.2f} kWh")