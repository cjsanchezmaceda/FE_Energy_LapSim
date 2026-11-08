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

from scipy import sparse
from scipy.optimize import lsq_linear
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d

def resample_closed(P, ds):
    '''Resample a closed polyline at (apporx) uniform spacing ds [m]'''
    Pc = np.vstack([P, P[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(Pc, axis = 0).T))]
    n = int(round(s[-1] / ds))
    s_new = np.linspace(0, s[-1], n, endpoint=False)
    return np.c_[np.interp(s_new, s, Pc[:, 0]), np.interp(s_new, s, Pc[:, 1])]

def centerline(left, right, ds=3.0):
    '''Midpoints betweenn the (resampled) left boundary and its closest points on the right one'''
    L = resample_closed(left, ds)
    R = np.array([project_to_polyline(p, right)[3] for p in L])
    C = (L + R) / 2
    return C

def left_normals(P):
    '''Unit normals pointing to the left of a closed polyline'''
    T = np.roll(P, -1, axis=0) - np.roll(P, 1, axis= 0)
    T = T / np.hypot(*T.T)[:, None]
    return np.c_[-T[:,1], T[:,0]]

def min_curvature_line(C, left, right, margin = 1.3):
    '''Minimum-curvature racing line p_i = c_i + alpha_i*n_i (Heilmeier et al., 2020)'''
    n_pts = len(C)
    n = left_normals(C)
    d_left = np.array([project_to_polyline(p, left)[0] for p in C])
    d_right = np.array([project_to_polyline(p, right)[0] for p in C])
    lo, hi = -(d_right - margin), (d_left - margin)

    D = sparse.diags([np.ones(n_pts), -2 * np.ones(n_pts), np.ones(n_pts)], [-1, 0, 1], shape=(n_pts, n_pts)).tolil()
    D[0, n_pts -1] = 1
    D[n_pts - 1, 0] = 1
    D = D.tocsr()

    A = sparse.vstack([D @ sparse.diags(n[:, 0]), D @ sparse.diags(n[:, 1])]).tocsr()
    b = -np.r_[D @ C[:, 0], D @ C[:, 1]]
    alpha = lsq_linear(A, b, bounds=(lo, hi), method="trf", lsmr_tol="auto").x
    return C + alpha[:, None] * n

def curvature_profile(P, ds=2.0, smooth=5.0):
    Pc = np.vstack([P, P[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(Pc, axis=0).T))]
    sx = CubicSpline(s, Pc[:, 0], bc_type="periodic")
    sy = CubicSpline(s, Pc[:, 1], bc_type="periodic")
    s_new = np.arange(0, s[-1], ds)
    dx, dy, ddx, ddy = sx(s_new, 1), sy(s_new, 1), sx(s_new, 2), sy(s_new, 2)
    kappa = (dx * ddy - dy * ddx) / (dx * dx + dy * dy) ** 1.5
    kappa = gaussian_filter1d(kappa, sigma=smooth / ds, mode="wrap")
    return s_new, np.c_[sx(s_new), sy(s_new)], kappa

if __name__ == "__main__":
    from pathlib import Path
    import matplotlib.pyplot as plt
    from check_alignment import load_xy

    ROOT = Path(__file__).resolve().parents[1]
    gl = list(load_xy(ROOT / "data/track/jarama_left.kml").values())[0]
    gr = list(load_xy(ROOT / "data/track/jarama_right.kml").values())[0]
    loop = load_xy(ROOT / "data/kml/chicane_jarama.kml")
    left, _ = splice_loop(gl, loop["izquierda chicane path"])
    right, _ = splice_loop(gr, loop["Derecha Chicane path"])

    C = resample_closed(centerline(left, right), 3.0)
    P = min_curvature_line(C, left, right)
    s, Pk, kappa = curvature_profile(P)

    print(f"centreline   : {closed_length(C):.1f} m   (official FE layout: 3934 m)")
    print(f"racing line  : {closed_length(P):.1f} m")
    print(f"total heading: {np.degrees(kappa.sum() * 2.0):.1f} deg   (clockwise -> about -360)")
    print(f"min radius   : {1 / np.abs(kappa).max():.1f} m")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    for B in (left, right):
        ax1.plot(*np.vstack([B, B[:1]]).T, "k", lw=0.7)
    ax1.plot(*np.vstack([P, P[:1]]).T, "r", lw=1, label="racing line")
    ax1.plot(*C.T, "b--", lw=0.6, label="centreline")
    ax1.set_aspect("equal"); ax1.legend()
    ax2.plot(s, kappa); ax2.set_xlabel("s [m]"); ax2.set_ylabel("curvature [1/m]"); ax2.grid()
    plt.show()

from pathlib import Path
from check_alignment import load_xy

def load_track(ds=2.0):
    '''KMLs -> spliced lood -> centerline ->racing line -> curvature'''
    ROOT = Path(__file__).resolve().parents[1]
    gl = list(load_xy(ROOT / "data/track/jarama_left.kml").values())[0]
    gr = list(load_xy(ROOT / "data/track/jarama_right.kml").values())[0]
    loop = load_xy(ROOT / "data/kml/chicane_jarama.kml")
    left, _ = splice_loop(gl, loop["izquierda chicane path"])
    right, _ = splice_loop(gr, loop["Derecha Chicane path"])
    P = min_curvature_line(resample_closed(centerline(left, right), 3.0), left, right)
    s, _, kappa = curvature_profile(P, ds=ds)
    return kappa, ds