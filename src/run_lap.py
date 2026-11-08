from track import load_track
from vehicle import GEN3_EVO, mode
from lapsim import simulate

kappa, ds = load_track()

for name, car in [('300 kW', GEN3_EVO), ('350 kW + front', mode(GEN3_EVO, 350, awd=True))]:
    r = simulate(car, kappa, ds)
    print(f"{name:15s} lap {r['lap_time']:.2f} s   vmax {r['v'].max()*3.6:.0f} km/h   "
          f"vmin {r['v'].min()*3.6:.0f} km/h   energy {r['E_net']:.3f} kWh")