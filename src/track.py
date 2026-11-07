import numpy as np

def project_to_polyline(p, poly):
    '''Closest point to `p` on a CLOSED polyline `poly` (N, 2).'''
    a = poly
    b = np.roll(poly, -1, axis=0)
    ab = b - a
    t = np.clip(((p - a)*ab).sum(1)/(ab*ab).sum(1), 0, 1)
    q = a + ab * t[:,None]
    d = np.hypot(*(q - p).T)
    k = int(d.argmin())
    return d[k], k, t[k], q[k]

def splice_loop(gps, path, treshold = 2.5):
    '''Replace the GPS straight by the digitised loop'''
    d = np.array([project_to_polyline(p, gps)[0] for p in path])
    off = np.where(d > treshold)[0]
    i_in, i_out = off[0] - 1, off[-1] + 1

    _, k_in, _, A_in = project_to_polyline(path[i_in], gps)
    _, k_out, _, A_out = project_to_polyline(path[i_out], gps)
    
    N = len(gps)
    r = np.roll(gps,-(k_out + 1), axis=0)
    kin = k_in - k_out - 1
    new = np.vstack([r[:kin + 1], A_in, path[i_in + 1:i_out], A_out])

    return new, dict(i_in = i_in, i_out = i_out, k_in=k_in, k_out=k_out)

def closed_length(P):
    '''Perimeter of a closed polyline (includes last -> first)'''
    return np.hypot(*np.diff(np.vstack([P, P[:1]]), axis = 0).T).sum()

if __name__ == "__main__":
    from pathlib import Path
    import matplotlib.pyplot as plt
    from check_alignment import load_xy, signed_area

    ROOT = Path(__file__).resolve().parents[1]
    gps_left = list(load_xy(ROOT / "data/track/jarama_left.kml").values())[0]
    gps_right = list(load_xy(ROOT / "data/track/jarama_right.kml").values())[0]
    loop = load_xy(ROOT / "data/kml/chicane_jarama.kml")

    fig, ax = plt.subplots(figsize=(7, 7))
    for side, gps, name in [("left", gps_left, "izquierda chicane path"),("right", gps_right, "Derecha Chicane path")]:
        new, idx = splice_loop(gps, loop[name])
        print(side, idx)
        print(f"   GPS length  : {closed_length(gps):.1f} m")
        print(f"   with loop   : {closed_length(new):.1f} m  (+{closed_length(new) - closed_length(gps):.1f} m)")
        print(f"   points      : {len(new)}   signed area: {signed_area(new):.0f} m2")
        ax.plot(*np.vstack([new, new[:1]]).T, label=f"{side} (spliced)")
    ax.set_aspect("equal")
    ax.legend()
    plt.show()