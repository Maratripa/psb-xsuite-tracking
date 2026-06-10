#%%
import xtrack as xt
import xobjects as xo
import xfields as xf
import xpart as xp
import numpy as np
import json
import time
import os
from lib.statisticalEmittance import StatisticalEmittance as stE


#%%
#########################################
# Load parameters
#########################################
from simulation_parameters import parameters as p, idx
source_dir = os.getcwd() + '/'
results_dir = os.path.join(source_dir, 'results')
os.makedirs(results_dir, exist_ok=True)
if p['prepare_tune_ramp']:
    with open(source_dir+f'time_tables/tunes_{idx}.json', 'r') as fid:
        d = json.load(fid)
    for key in d:
        p[key] = d[key]


#%%
#########################################
# Load PSB line
#########################################
context = p['context']
line = xt.Line.from_json(source_dir+f'psb/psb_line_thin_{idx}.json')
Cpsb = line.get_length() # 157.08 m
print('Loaded PSB line from psb/psb_line_thin.json.')


#%%
#########################################
# Install space charge nodes
#########################################
if p['install_space_charge']:
    mode = p['space_charge_mode']
    print(f'Installing space charge in {mode} mode')
    # install nodes in lattice frozen-like (exact parameters do not matter if pic is used)
    lprofile = xf.LongitudinalProfileQGaussian(number_of_particles=p['bunch_intensity'], 
                                            sigma_z=p['sigma_z'], 
                                            z0=0, q_parameter=1.)
    xf.install_spacecharge_frozen(line=line,
                    particle_ref=line.particle_ref,
                    longitudinal_profile=lprofile,
                    nemitt_x=p['nemitt_x'], nemitt_y=p['nemitt_y'],
                    sigma_z=p['sigma_z'],
                    num_spacecharge_interactions=p['num_spacecharge_interactions'],
                    delta_rms=1e-3
                    )
    if mode == 'frozen':
        pass # Already configured in line
    # switch to pic or quasi-frozen
    elif mode == 'quasi-frozen':
        xf.replace_spacecharge_with_quasi_frozen(line,
                                        update_mean_x_on_track=True,
                                        update_mean_y_on_track=True)
    elif mode == 'pic':
        pic_collection, all_pics = xf.replace_spacecharge_with_PIC(
            _context=context, line=line,
            n_sigmas_range_pic_x=10, 
            n_sigmas_range_pic_y=10,
            nx_grid=128, ny_grid=128, nz_grid=64, # to be reviewed
            n_lims_x=7, n_lims_y=7,
            #z_range=(-3*p['sigma_z'], 3*p['sigma_z']), 
            z_range=(-Cpsb/2, Cpsb/2), 
            solver=p['pic_solver'],
            #grid_extend_in_x = 0.045, grid_extend_in_y = 0.045
            )
    else:
        raise ValueError(f'Invalid mode: {mode}')
    print('Space charge installed')
else:
     print('Skipping space charge...')


#%%
#########################################
# Build tracker
#########################################
line.build_tracker(_context=context)
print('Tracker built')
#line_sc_off = line.filter_elements(exclude_types_starting_with='SpaceCh') # to remove space charge
#print('Keeping line_sc_off: line without space charge knobs.')


#%%
#########################################
# Setup particles for injection
#########################################
print('%s particle distribution.'%p['particle_distribution'])
with open(source_dir+f'input/particles_initial_{idx}.json', 'r') as fid:
    particles_for_injection = xp.Particles.from_dict(json.load(fid), _context=context)
print('Loaded particles from input/particles_initial.json.')
if p['num_injections']==1:
    print('Number of injections = 1.')
    if p['particle_distribution'] == 'simulated':
        particles = particles_for_injection
    elif p['particle_distribution'] == 'real':
        # to be reviewed; current implementation is not correct
        # 'real' particles_for_injection is of length 60000, different from p['n_part']
        particles = particles_for_injection
elif p['num_injections']>1:
    print('Number of injections = %i.'%p['num_injections'])
    
    # Build and insert multi-turn injection element 
    print('Building and inserting multi-turn injection element to PSB lattice.')
    print('Number of injections: ', p['num_injections'])
    print('Number of macroparticles per injection: ', int(p['n_part']/p['num_injections']))
    p_injection = xt.ParticlesInjectionSample(particles_to_inject=particles_for_injection,
                                              line=line,
                                              element_name='injection',
                                              num_particles_to_inject=int(p['n_part']/p['num_injections']))
    line.discard_tracker()
    if p['particle_distribution']=='real':
        line.insert_element(index='bi1.tstr1l1', element=p_injection, name='injection')
    elif ((p['particle_distribution']=='simulated') and (p['element_to_cycle'] is not None)):
        line.insert_element(index=p['element_to_cycle'], element=p_injection, name='injection')
    else:
        line.insert_element(index='psb1$start', element=p_injection, name='injection')
    line.build_tracker()

    # Generate particle object with unallocated space
    print('Generating particle object with unallocated space.')
    particles = line.build_particles(_capacity=p['n_part']+1, x=0)
    particles.state[0] = -500 # kill the particle added by default


line.enable_time_dependent_vars = True
#line.dt_update_time_dependent_vars = 3e-6 # approximately every 3 turns
line.vars.cache_active = False
if line.energy_program is not None:
    line.energy_program.line.particle_ref = line.particle_ref
line.vars['t_turn_s'] = 0.0
output = []
if p['GPU_FLAG']:
    import cupy as cp
    op = cp
    r = stE(context='GPU')
else:
    op = np
    r = stE(context='CPU')
output=[]
intensity = []
fname = f"Q({p['qx_ini']:.3f}-{p['qy_ini']:.3f})I{p['bunch_intensity']/1e10:.1e}P{p['n_part']:.1e}T{p['num_turns']:.1e}{'FE'*p['include_field_errors']}{'SC'*p['install_space_charge']}{'_pic' * p['install_space_charge'] * (p['space_charge_mode'] == 'pic')}"


#%%
#########################################
# Start tracking
#########################################
num_turns = p['num_turns']
print('Now start tracking...')
start = time.time()
for ii in range(num_turns):
    print(f'Turn {ii} out of {num_turns}')

    # multi-turn injection + foil
    if p['num_injections']>1:
        if ii == p['num_injections']:
            p_injection.num_particles_to_inject = 0
            print('Injection finished.')
        elif ii < p['num_injections']:
            print('Injecting %i macroparticles.'%(int(p['n_part']/p['num_injections'])))
        intensity.append(particles.weight[particles.state>0].sum())

    # keep particles within the ring circumference
    particles.zeta = (particles.zeta+Cpsb/2)%Cpsb-Cpsb/2

    # track one turn
    #line.track(particles, turn_by_turn_monitor=True)
    line.track(particles, num_turns=1)

    # update output
    bunch_moments=r.measure_bunch_moments(particles)
    
    means = op.array([
        op.mean(particles.x), op.mean(particles.y), op.mean(particles.zeta),
        op.mean(particles.px), op.mean(particles.py), op.mean(particles.delta)
    ])

    stds = op.array([
        op.std(particles.x), op.std(particles.y), op.std(particles.zeta),
        op.std(particles.px), op.std(particles.py), op.std(particles.delta)
    ])

    output.append([
        len(r.coordinate_matrix[0]),
        bunch_moments['nemitt_x'].tolist(),
        bunch_moments['nemitt_y'].tolist(),
        bunch_moments['emitt_z'].tolist(),
        *context.nparray_from_context_array(means),
        *context.nparray_from_context_array(stds),
        float(context.nparray_from_context_array(particles.beta0)[0]),
        float(context.nparray_from_context_array(particles.gamma0)[0]),
        float(context.nparray_from_context_array(particles.p0c)[0])
    ])

    if ii in p['turns2saveparticles']:
        print(f'Saving turn {ii}')
        particles_fname = os.path.join(results_dir, f"{fname}_particles_turn_{ii:05d}.json")
        with open(particles_fname, 'w') as fid:
            json.dump(particles.to_dict(), fid, cls=xo.JEncoder)
            print(f'Particles saved to {particles_fname}.')

end = time.time()
print('Tracking finished.')
print('Total seconds = ', end - start)
np.save(os.path.join(results_dir, fname), output)
print(f'Emittances saved to {os.path.join(results_dir, fname)}.npy.')