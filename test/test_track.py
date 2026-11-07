from pathlib import Path
from check_alignment import load_xy, signed_area
from track import splice_loop, closed_length

ROOT = Path(__file__).resolve().parents[1]

def _sides():
    gl = list(load_xy(ROOT / "data/track/jarama_left.kml").values())[0]
    gr = list(load_xy(ROOT / "data/track/jarama_right.kml").values())[0]
    loop = load_xy(ROOT / "data/kml/chicane_jarama.kml")
    return [(gl, loop["izquierda chicane path"]), (gr, loop["Derecha Chicane path"])]

def test_loop_adds_about_30_m():
    for gps, path in _sides():
        new, _ = splice_loop(gps, path)
        extra = closed_length(new) - closed_length(gps)
        assert 25 < extra < 35          # Google Earth measurement: ~30 m

def test_still_clockwise():
    for gps, path in _sides():
        new, _ = splice_loop(gps, path)
        assert signed_area(new) < 0