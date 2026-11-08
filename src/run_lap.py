import numpy as np
from pathlib import Path
from check_alignment import load_xy
from track import splice_loop, centerline, resample_closed, min_curvature_line, curvature_profile
from vehicle import GEN3_EVO, mode
from lapsim import simulate

ROOT = Path(__file__).resolve().parents[1]
gl = list(load_xy(ROOT / "data/track/jarama_left.kml").values())[0]
gr = list(load_xy(ROOT / "data/track/jarama_right.kml").values())[0]
loop = load_xy(ROOT / "data/kml/chicane_jarama.kml")
left, _ = splice_loop(gl, loop["izquierda chicane path"])
right, _ = splice_loop(gr, loop["Derecha Chicane path"])
P = min_curvature_line(resample_closed(centerline(left, right), 3.0), left, right)
s, _, kappa = curvature_profile(P, ds=2.0)

for name, car in [('300 kW', GEN3_EVO), ('350 kW + front', mode(GEN3_EVO, 350, awd=True))]:
    r = simulate(car, kappa, 2.0)
    print(f"{name:15s} lap {r['lap_time']:.2f} s   vmax {r['v'].max()*3.6:.0f} km/h   "
          f"vmin {r['v'].min()*3.6:.0f} km/h   energy {r['E_net']:.3f} kWh")