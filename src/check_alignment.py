from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from geo import read_kml_paths, lonlat_to_xy

ROOT = Path(__file__).resolve().parents[1]

def load_xy(kml_path):
    '''Return {name: array(N,2) of [x,y] in m} for every path in a kml file'''
    out = {}
    for name, lonlat in read_kml_paths(kml_path).items():
        x, y = lonlat_to_xy(lonlat[:,0], lonlat[:,1])
        out[name] = np.c_[x,y]
    return out

def signed_area(p):
    '''Shoelace formula.P: array(N,2). >0 anticlockwise, <0 clockwise'''
    x, y = p[:,0], p[:,1]
    return 1/2*np.sum(x*np.roll(y,-1)-y*np.roll(x,-1))
    
def distance_to_polyline(points, poly):
    """Minimum distance from each point to a polyline (projection onto every segment)."""
    a, b = poly[:-1], poly[1:]
    ab = b - a
    d = []
    for p in points:
        t = np.clip(((p - a) * ab).sum(1) / (ab * ab).sum(1), 0, 1)
        q = a + ab * t[:, None]
        d.append(np.hypot(*(q - p).T).min())
    return np.array(d)

if __name__ == '__main__':
    gps_left = list(load_xy(ROOT / 'data/track/jarama_left.kml').values())[0]
    gps_right = list(load_xy(ROOT / 'data/track/jarama_right.kml').values())[0]
    loop = load_xy(ROOT / 'data/kml/chicane_jarama.kml')

    print('signed area left:', round(signed_area(gps_left)))
    print('signed area right:', round(signed_area(gps_right)))

    for name, P in loop.items():
        ends = P[[0, 1, -2, -1]]
        print(name, '-> GPS left:', distance_to_polyline(ends, gps_left).round(2), 'GPS right:', distance_to_polyline(ends, gps_right).round(2))

    fig, ax = plt.subplots(figsize=(7,7))
    ax.plot(gps_left[:,0], gps_left[:,1], color = 'grey', label='GPS left')
    ax.plot(gps_right[:,0], gps_right[:,1], color= 'grey', label='GPS right')
    for name, P in loop.items():
        ax.plot(P[:,0], P[:,1], label=name)
    ax.set_aspect('equal')
    ax.legend()
    plt.show()