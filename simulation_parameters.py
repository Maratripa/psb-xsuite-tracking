import xobjects as xo
import numpy as np

import sys

PARAMS = {} 

# Tracking parameters
PARAMS['num_turns'] = int(55e3) # number of turns to track
PARAMS['turns2saveparticles'] = [0, 1, PARAMS['num_turns'] - 1] # turns to save particles object
PARAMS['turns2plot'] = [] # turns to plot phase space (while tracking)

# Beam intensity and emittance
PARAMS['n_part'] = int(100e3) # number of macroparticles
PARAMS['bunch_intensity'] = 100e10 # number of particles per bunch
PARAMS['particle_distribution'] = 'real' # 'simulated' or 'real
if PARAMS['particle_distribution']=='simulated':
    PARAMS['nemitt_x'] = 1e-6 # normalized emittance in x
    PARAMS['nemitt_y'] = 1e-6 # normalized emittance in y
    PARAMS['sigma_z'] = (400/4)*0.525*0.3 # bunch length in m
    PARAMS['longitudinal_shape'] = 'gaussian' # 'parabolic' or 'coasting' or 'gaussian'
elif PARAMS['particle_distribution']=='real':
    PARAMS['nemitt_x'] = 1e-6 # approximate
    PARAMS['nemitt_y'] = 1e-6 # approximate
    PARAMS['sigma_z'] = 10 # guess, tos be revised
    PARAMS['longitudinal_shape'] = np.nan # not used

# Tunes (at injection), chromaticity, imperfections
PARAMS['qx_ini'] = 4.40
PARAMS['qy_ini'] = 4.45
PARAMS['correct_chroma'] = False # if True, chromaticity is corrected using XNOH0 (harmonic) sextupoles
PARAMS['chroma_plane'] = 'y' # to correct horizontal ('x') or vertical ('y') chromaticity
PARAMS['include_field_errors'] = True # if True, field errors are included
PARAMS['field_errors'] = {
    'kbr1qno816l3': -6.15363e-4, # half-integer excitation (deltaI_816 = -2A)
    'kbr1qno412l3': 0,
}
PARAMS['injection_missteering_x'] = 0.0e-3 # horizontal injection missteering in m
PARAMS['injection_missteering_y'] = 0.0e-3 # vertical injection missteering in m

# Setup acceleration
PARAMS['prepare_acceleration'] = 2 # 0: all RF OFF, 1: flat bottom (single RF at 8kV), 2: nominal PSB acceleration (double RF), 3: triple harmonic with acceleration
PARAMS['twiss_mode'] = '4d' # '4d' or '6d, used only if all RF are OFF
PARAMS['zeta0'] = 17.5 # if double RF, 6d-twiss at zeta0=0 fails because is unstable fixed point; this is a guess of the stable fixed point
#PARAMS['zeta0'] = 10.0 # if triple RF, 6d-twiss at zeta0=0 fails because is unstable fixed point; this is a guess of the stable fixed point

# L4 parameters and number of injections
PARAMS['choppingFactor'] = 0.7
PARAMS['z_offset'] = 0.0 #-0.8 # for ramp #0.0
PARAMS['Linac4_current'] = 25e-3 # Amps
PARAMS['num_injections'] = 1 # if > 1: a multi-turn injection is setup

# Injection chicane and correction
PARAMS['include_injection_chicane'] = 0 # if 1, 002A_include_injection_chicane.py is executed
PARAMS['on_chicane_k0'] = 1 # if 1, activates edge focusing of injection chicane
PARAMS['on_chicane_k2'] = 1 # if 1, activates eddy currents of injection chicane
PARAMS['include_injection_chicane_correction'] = 0 # if 1, 002B_include_injection_chicane_correction.py is executed
PARAMS['on_chicane_tune_corr'] = 1 # if 1, activates tune correction of injection chicane
PARAMS['on_chicane_beta_corr'] = 1 # if 1, activates beta correction of injection chicane

# Setup injection foil
PARAMS['install_injection_foil'] = False # if True, injection foil is installed
PARAMS['scatterchoice'] = 1 # 1: simple (no losses) 0: full (with losses) not working (for now)!

# Transverse painting
PARAMS['prepare_painting'] = 0 # if 1, 002C_prepare_painting.py is executed
PARAMS['on_painting_bump'] = 0 # if 1, activates painting bump
# Following convention: (t0,A0), (t1,A1), (t2,A2), (t3,A3), (1000,0)
# ISOLDE-like painting (check PSB_MD logbook entry 3806505 from 20/07/2023)
# https://logbook.cern.ch/elogbook-server/GET/showEventInLogbook/3806505
t2 = 148e-6 # num_injections*1e-6
t3 = 158e-6 # (num_injections+10)*1e-6
PARAMS['KSW_time_sec'] =         np.array([0.0e-6,  10e-6,      t2,     t3,  1000e-6])
PARAMS['KSW_bump_amplitude_m'] = np.array([-35e-3, -23e-3,  -12e-3, 9.2e-3,  0.0])

# Setup a linear tune ramp
PARAMS['prepare_tune_ramp'] = 1 # if 1, 005_prepare_tune_ramp.py is executed
PARAMS['on_tune_ramp'] = 1 # if 1, activates a linear tune ramp
PARAMS['tune_time_sec'] = np.array([0.0, 0.02, 0.04, 0.055]) # Time in seconds
PARAMS['qx_target']     = np.array([4.40, 4.35, 4.25, 4.17])
PARAMS['qy_target']     = np.array([4.45, 4.40, 4.30, 4.23])

# Setup slicing and line cycling
PARAMS['slices'] = 3 # number of slices in thin lattice
# To have the starting point of the lattice at a different location, None otherwise
# Relevant ONLY when using simulated particle distribution, foil otherwise
PARAMS['element_to_cycle'] = None # line starts at the start of the 1st sector (NOT at the stripping foil)
#PARAMS['element_to_cycle'] = 'bi1.tstr1l1' # stripping foil
#PARAMS['element_to_cycle'] = 'br1.bwsv11l1' # vertical LIU wire scanner

# Setup space charge calculation
PARAMS['install_space_charge'] = True # if True, space charge is installed
PARAMS['space_charge_mode'] = 'pic' # 'frozen' or 'pic' or 'quasi-frozen'
PARAMS['num_spacecharge_interactions'] = 160 # space charge interactions per turn
PARAMS['pic_solver'] = 'FFTSolver2p5DAveraged' # `FFTSolver2p5DAveraged` or `FFTSolver2p5D` or 'FFTSolver3D'

# Setup resources
PARAMS['GPU_FLAG'] = True # if True, GPU is used

def count_combinations():
    count = 1
    for param in PARAMS:
        if isinstance(PARAMS[param], (list, np.ndarray)) and param not in ['turns2saveparticles', 'turns2plot', 'KSW_time_sec', 'KSW_bump_amplitude_m', 'tune_time_sec', 'qx_target', 'qy_target']:
            count = count * len(PARAMS[param])
    return count

def get_params(idx):
    total_combinations = count_combinations()
    if idx >= total_combinations:
        raise ValueError(f"Index {idx} exceeds the total number of combinations.")

    OUT_PARAMS = PARAMS.copy()

    cum_mul = [1]
    list_params = []
    for param in PARAMS:
        if isinstance(PARAMS[param], (list, np.ndarray)) and param not in ['turns2saveparticles', 'turns2plot', 'KSW_time_sec', 'KSW_bump_amplitude_m', 'tune_time_sec', 'qx_target', 'qy_target']:
            list_params.append(param)
            OUT_PARAMS[param] = PARAMS[param][(idx // cum_mul[-1]) % len(PARAMS[param])]
            cum_mul.append(cum_mul[-1] * len(PARAMS[param]))
            
    # Re-evaluate dependent variables
    OUT_PARAMS['macrosize'] = OUT_PARAMS['bunch_intensity']/OUT_PARAMS['n_part']
    if 'Linac4_current' in OUT_PARAMS and 'choppingFactor' in OUT_PARAMS:
        OUT_PARAMS['num_injections'] = int(np.ceil(OUT_PARAMS['bunch_intensity']/OUT_PARAMS['choppingFactor']/OUT_PARAMS['Linac4_current']/6.25e12))
    
    # User had this to overwrite num_injections
    OUT_PARAMS['num_injections'] = 1 # if > 1: a multi-turn injection is setup
    
    if OUT_PARAMS['GPU_FLAG']:
        OUT_PARAMS['context'] = xo.ContextCupy()
    else:
        OUT_PARAMS['context'] = xo.ContextCpu()

    return OUT_PARAMS

try:
    idx = int(sys.argv[1])
except (IndexError, ValueError):
    idx = 0

parameters = get_params(idx)
