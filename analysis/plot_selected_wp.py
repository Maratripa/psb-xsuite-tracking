#%%
import numpy as np
import pylab as plt
from scipy.interpolate import griddata
from PyNAFF import naff
from resonance_lines import resonance_lines
import matplotlib.gridspec as gridspec
import os
import glob

# ==========================================
# SELECT YOUR WORKING POINT AND PARAMETERS
# ==========================================
qx_ini = 4.40
qy_ini = 4.48  # Change this to 4.45, 4.48, 4.52, 4.55, 4.58, or 4.60
bunch_intensity = 40e10 # Change this to 40e10, 100e10, or 400e10
n_part = 100e3
num_turns = 55e3
install_space_charge = True
space_charge_mode = 'pic'
# ==========================================

# Construct the base filename
fname = f"Q({qx_ini:.2f}-{qy_ini:.2f})I{bunch_intensity/1e10:.1e}P{n_part:.1e}T{num_turns:.1e}{'SC'*install_space_charge}{'_pic' * install_space_charge * (space_charge_mode == 'pic')}"

# Check if the file exists
qx_file = f'../output/{fname}_qx_pic.npy'
qy_file = f'../output/{fname}_qy_pic.npy'

if not os.path.exists(qx_file) or not os.path.exists(qy_file):
    print(f"Error: Could not find extracted tune files for this working point.")
    print(f"Expected to find:\n  {qx_file}\n  {qy_file}")
    
    print("\nAvailable working points in ../output/:")
    available = glob.glob('../output/*_qx_pic.npy')
    for f in available:
        print("  -", os.path.basename(f).replace('_qx_pic.npy', ''))
    raise FileNotFoundError("Tune spread arrays not found.")

print(f"Plotting working point: Qx={qx_ini}, Qy={qy_ini}, Intensity={bunch_intensity/1e10}e10")

#%%
qx_pic = np.load(qx_file)
qy_pic = np.load(qy_file)
qxnew = np.copy(qx_pic)
qynew = np.copy(qy_pic)
qxnew[np.where(qxnew<0)] += 1
qynew[np.where(qynew<0)] += 1
qxnew = qxnew+4
qynew = qynew+4

#%%
my_cmap = plt.cm.jet
my_cmap.set_under('w',1)
fontsize=20
bins = 1000
vmin = 1
# Dynamically set axes to be nicely centered around the selected working point
qx_min, qx_max = qx_ini - 0.1, qx_ini + 0.1
qy_min, qy_max = qy_ini - 0.2, qy_ini + 0.1

# r.Qx_min, r.Qx_max are used for resonance lines range limits
r=resonance_lines([qx_min, qx_max], [qy_min, qy_max], [1,2,3,4], 16)

fig = plt.figure(figsize=(10,8))
gs = gridspec.GridSpec(6, 6)
ax = plt.subplot(gs[1:6, 0:4])
ax_xDist = plt.subplot(gs[0, 0:4],sharex=ax)
ax_yDist = plt.subplot(gs[1:6, 4],sharey=ax)

ax.hist2d(qxnew, qynew,
          bins=500, cmap = my_cmap, vmin=vmin, 
          range=[[r.Qx_min, r.Qx_max], [r.Qy_min, r.Qy_max]]
          )

# Plot the selected working point
ax.plot(qx_ini, qy_ini, '*', ms=20, color='k', zorder=1e5)

ax.set_xlabel('$\mathrm{Q_x}$', fontsize=fontsize)
ax.set_ylabel('$\mathrm{Q_y}$', fontsize=fontsize)
ax.tick_params(axis='both', labelsize=fontsize)

# Dynamically set axes to be nicely centered around the selected working point
ax.set_xlim(qx_min, qx_max)
ax.set_ylim(qy_min, qy_max)
ax.axhline(qy_ini, color='k', ls='--')
ax.axvline(qx_ini, color='k', ls='--')

ax_xDist.hist(qxnew,bins=bins,align='mid', color='black')
ax_xDist.tick_params(axis='x', labelleft=False, labelright=False, labeltop=False, labelbottom=False)
ax_xDist.tick_params(axis='y', labelleft=False, labelright=False, labeltop=False, labelbottom=False)
nsigmas = 2.5
ax_xDist.axvline(np.mean(qxnew)-nsigmas*np.std(qxnew), color='red', ls='-')
ax_xDist.axvline(np.mean(qxnew)+nsigmas*np.std(qxnew), color='red', ls='-')
print('Total tune spread in x: ', nsigmas*np.std(qxnew)*2)

ax_yDist.hist(qynew,bins=bins,orientation='horizontal',align='mid', color='black')
ax_yDist.tick_params(axis='x', labelleft=False, labelright=False, labeltop=False, labelbottom=False)
ax_yDist.tick_params(axis='y', labelleft=False, labelright=False, labeltop=False, labelbottom=False)
nsigmas = 2.5
ax_yDist.axhline(np.mean(qynew)-nsigmas*np.std(qynew), color='red', ls='-')
ax_yDist.axhline(np.mean(qynew)+nsigmas*np.std(qynew), color='red', ls='-')
print('Total tune spread in y: ', nsigmas*np.std(qynew)*2)

fig.tight_layout()
output_image = f"tunespread_Q({qx_ini:.2f}-{qy_ini:.2f}).png"
plt.savefig(output_image, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_image}")
plt.show()
