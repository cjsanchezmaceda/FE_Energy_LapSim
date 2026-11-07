from pathlib import Path
import numpy as np
from geo import read_kml_paths, lonlat_to_xy

ROOT = Path(__file__).resolve().parents[1]
KML = ROOT / 'data' / 'kml' / 'chicane_jarama.kml'

def _xy(name):
    lonlat = read_kml_paths(KML)[name]
    return lonlat_to_xy(lonlat[:,0], lonlat[:,1])

def test_left_path_length():
    x, y = _xy('izquierda chicane path')
    length = np.hypot(np.diff(x), np.diff(y)).sum()
    assert abs(length - 444.8) < 0.5

def test_straight_heading():
    x, y = _xy('izquierda chicane path')
    heading = np.degrees(np.arctan2(x[-1] - x[0], y[-1] - y[0])) % 360
    assert  abs(heading - 162.2) < 1.0