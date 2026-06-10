# Realistic Proton Synchrotron Booster (PSB) Beam Dynamics Simulation with Xsuite

This repository provides a full simulation pipeline for realistic modeling of beam dynamics in CERN’s Proton Synchrotron Booster (PSB) using Xsuite.

It includes tools for:

- Lattice generation (tested ✅)
- Multi-turn injection and transverse painting modeling
- Foil scattering
- Acceleration (tested ✅)
- Time-dependent settings (e.g. tune ramps) (tested ✅)
- Machine imperfections (tested ✅)
- Space charge effects (tested ✅)
- Tracking and output analysis (semi-tested ❌✅)
- Scripts for submittion to [HTCondor](https://abpcomputing.web.cern.ch/computing_resources/cernbatch/) (only GPU for now)

**Original repo:** https://github.com/tprebiba/psb-xsuite-tracking

---

## Simulation Parameters
All the settings are controlled via `simulation_parameters.py`. The file is written so that any parameters on a `list` or `np.array` are separated into different simulations. To run a specific configuration of parameters an index must be provided, see next section for an example of usage.

## Running Locally

### Part I: Preparing the Simulation

- Generate the desired lattice and particle distribution (lattice setup, beam transverse and longitudinal characteristics, ...).
- All settings are controlled via `simulation_parameters.py`.
- Execution:
    ```
    ./000_prepare_simulation.sh <idx>
    ```
    Where `<idx>` is the index of the parameter configuration.
- Will generate the lattice and machine settings in `psb/` and the initial particle distribution in `input/`


### Part II: Tracking

- Perform beam tracking (configured also via `simulation_parameters.py`).
- Execution:
    ```
    python -m runPSB.py <idx>
    ```
<!-- - All the outputs (turn-by-turn beam data, beam profiles, ...) are saved in `output/`. -->

## Running on HTCondor
The workflow is designed to be run on HTCondor. To submit the simulations there are two steps:

- Prepare the simulations via `simulation_parameters.py`.
- Submit the simulations:
    ```
    ./submit_remote.sh
    ```