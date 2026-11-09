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
               m=1046 #minimum wigh)