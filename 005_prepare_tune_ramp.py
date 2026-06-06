import xtrack as xt
import json
import xdeps as xd
import numpy as np
from simulation_parameters import parameters as p, idx

print('*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~**~*~*~**~*~*~**~*~*~*')
print('005_prepare_tune_ramp.py')
print('*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~*~**~*~*~**~*~*~**~*~*~*')

if p['prepare_tune_ramp']==0:
    print('prepare_tune_ramp = 0')
    print('Tunes will remain constant.')

elif p['prepare_tune_ramp']==1:

      #########################################
      # Load PSB line in xsuite
      #########################################
      line = xt.Line.from_json(f'psb/psb_line_thin_{idx}.json')
      line.build_tracker()

      #########################################
      # Deactivate chicane and correction
      # Deactivate painting bump
      #########################################
      line.vars['on_chicane_k0'] = 0
      line.vars['on_chicane_k2'] = 0
      line.vars['on_chicane_tune_corr'] = 0
      line.vars['on_chicane_beta_corr'] = 0
      line.vars['on_painting_bump'] = 0
      print('Chicane and correction deactivated.')
      print('Painting bump deactivated.')

      #########################################
      # Generate tune ramp
      #########################################
      kf_array = []
      kd_array = []
      
      for i, (qx_t, qy_t) in enumerate(zip(p['qx_target'], p['qy_target'])):
            print(f"Matching point {i+1}/{len(p['qx_target'])} at (Qx, Qy) = ({qx_t}, {qy_t})")
            line.match(
                  vary=[
                        xt.Vary('kbrqf', step=1e-8),
                        xt.Vary('kbrqd', step=1e-8),
                  ],
                  targets = [
                        xt.Target('qx', qx_t, tol=1e-5),
                        xt.Target('qy', qy_t, tol=1e-5)
                  ]
            )
            kf = line.vars['kbrqf']._value
            kd = line.vars['kbrqd']._value
            kf_array.append(kf)
            kd_array.append(kd)
            print(f'Converged to strengths (kf, kd) = ({kf}, {kd})')

      d = {
            'tune_time_sec': p['tune_time_sec'].tolist(),
            'qx_target': p['qx_target'].tolist(),
            'qy_target': p['qy_target'].tolist(),
            'kf_array': kf_array,
            'kd_array': kd_array,
            'num_turns': p['num_turns'],
      }
      with open(f'time_tables/tunes_{idx}.json','w') as fid:
            json.dump(d, fid, indent=2)
      print('Dictionary: ', d)
      print(f'Wrote time_tables/tunes_{idx}.json')

      #########################################
      # Reactivate chicane and correction
      # Reactivate painting bump
      #########################################
      line.vars['on_chicane_k0'] = p['on_chicane_k0']
      line.vars['on_chicane_k2'] = p['on_chicane_k2']
      line.vars['on_chicane_tune_corr'] = p['on_chicane_tune_corr']
      line.vars['on_chicane_beta_corr'] = p['on_chicane_beta_corr']
      line.vars['on_painting_bump'] = p['on_painting_bump']
      if ((p['include_injection_chicane']>0) or (p['include_injection_chicane_correction']>0)):
            print('Chicane and correction reactivated.')
      if p['prepare_painting']>0:
            print('Painting bump reactivated.')
      tw = line.twiss()
      print('Working point of thin lattice: (Qx, Qy) = (%s, %s)'%(tw.qx, tw.qy))

      #########################################
      # Generating xsuite functions and
      # assigning to main quads
      #########################################
      line.functions['kbrqf_func'] = xd.FunctionPieceWiseLinear(x=p['tune_time_sec'], y=np.array(kf_array))
      line.functions['kbrqd_func'] = xd.FunctionPieceWiseLinear(x=p['tune_time_sec'], y=np.array(kd_array))

      line.vars['on_tune_ramp'] = p['on_tune_ramp'] # to easily switch off the tune ramp
      line.vars['kbrqf'] = line.functions.kbrqf_func(line.vars['t_turn_s']) * line.vars['on_tune_ramp']
      line.vars['kbrqd'] = line.functions.kbrqd_func(line.vars['t_turn_s']) * line.vars['on_tune_ramp'] 

      #########################################
      # Save line to .json
      #########################################
      line.to_json(f'psb/psb_line_thin_{idx}.json')
      print('Line saved to psb/psb_line_thin.json')