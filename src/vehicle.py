from dataclasses import dataclass, replace

G = 9.81 #[g]
#FP1 weather report 2026 Madrid E-Prix
Pamb = 94170 #[Pa] 941.7 mbar
R_air = 287.05 #[J/kg/K]
Tamb = 11.9 + 273.15 #[K]
RHO = Pamb/(R_air * Tamb)

@dataclass
class Car:
    m: float
    P_drive: float
    awd: bool # front motor driving? (Gen3 Evo: only in attack mode / qualifying)
    P_front: float
    P_regen_f: float
    P_regen_r: float
    wheelbase: float
    h_cog: float
    wf: float
    cdA: float
    clA: float
    mu: float
    Crr: float = 0.012
    eta_d: float = 0.93
    eta_r: float = 0.90

GEN3_EVO = Car(
    m = 856,
    P_drive = 300e3, #300 kW normal mode, 350 kW attack mode
    awd = False, #limited to the rear powertrain in normal mode, front motor only in attack mode
    P_front = 50e3, #50 kW front motor in attack mode
    P_regen_f = 250e3, #250 kW front regen
    P_regen_r = 350e3, #350 kW rear regen
    wheelbase = 2.9705,
    h_cog = 0.30,
    wf = 0.42,
    cdA = 0.9,
    clA = 1.6,
    mu = 1.6, #reference
)

def mode(car, P_kw, awd=False, **changes):
    '''GEN3 Evo in other mode'''
    return replace(car, P_drive=P_kw*1e3, awd=awd, **changes)