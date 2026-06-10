#!/usr/bin/bash

JOB_FLAVOUR="tomorrow"
SCRIPT_NAME="runPSB.py"
N_JOBS=$(python -c "from simulation_parameters import count_combinations; print(count_combinations())")

PROJECT_DIR=$(basename $PWD)

echo "We are going to be ssh-ing to lxplus, please provide your username."
echo -n "Username: "
read username

REMOTE_PATH="/afs/cern.ch/work/${username:0:1}/${username}/${PROJECT_DIR}"
OUTPUT_PATH="root://eosuser.cern.ch//eos/user/${username:0:1}/${username}/simulations/${PROJECT_DIR}"

SOCKET="/tmp/ssh-socket-${username}"
SSH_OPTS="-o ControlMaster=auto -o ControlPath=${SOCKET} -o ControlPersist=10m"

# Pack the source code and templates
tar --exclude='results' --exclude='output' --exclude='*.npy' \
    --exclude='psb/psb_line_thin_*.json' \
    --exclude='input/particles_initial_*.json' \
    --exclude='time_tables/tunes_*.json' \
    --exclude='analysis' \
    -czf files.tar.gz *

# Create the remote executable that handles preparation
cat << EOF > executable.sh
#!/usr/bin/env bash
tar xf files.tar.gz
rm files.tar.gz
mkdir -p results

CONTAINER_FULLPATH="/cvmfs/unpacked.cern.ch/ghcr.io/ekatralis/xsuite-containers:v0.50.7-cuda12.9"

containerrun() {
    apptainer exec --env PYTHONNOUSERSITE=1 --home "\$_CONDOR_SCRATCH_DIR" --writable-tmpfs --cleanenv --nv \$CONTAINER_FULLPATH "\$@"
}

echo "*** PREPARING SIMULATION (Index \$1) ***"
containerrun python 001_get_PSB_line.py \$1
containerrun python 002A_include_injection_chicane.py \$1
containerrun python 002B_include_injection_chicane_correction.py \$1
containerrun python 002C_prepare_painting.py \$1
containerrun python 003_prepare_acceleration.py \$1
containerrun python 004_prepare_for_tracking.py \$1
containerrun python 005_prepare_tune_ramp.py \$1
containerrun python 006_lattice_imperfections.py \$1
containerrun python 007_generate_particle_distribution.py \$1
echo "*** PREPARATION COMPLETE ***"

echo "*** STARTING TRACKING ***"
containerrun python ${SCRIPT_NAME} \$1
EOF

cat << EOF > submission.sub
executable = executable.sh
arguments = \$(ProcId)
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
output_destination = ${OUTPUT_PATH}
transfer_input_files = files.tar.gz
transfer_output_files = results
MY.XRDCP_CREATE_DIR = True
output = out.\$(ClusterId).\$(ProcId)
error = err.\$(ClusterId).\$(ProcId)
log = log.\$(ClusterId)
requestGpus = 1
requestCpus = 4
+JobFlavour = "${JOB_FLAVOUR}"
queue ${N_JOBS}
EOF

echo "Submitting simulation (Remote Prep Mode) for ${PROJECT_DIR}..."

ssh $SSH_OPTS ${username}@lxplus.cern.ch "mkdir -p $REMOTE_PATH"

echo "--> Syncing source files..."
rsync -avz -e "ssh $SSH_OPTS" files.tar.gz executable.sh submission.sub ${username}@lxplus.cern.ch:$REMOTE_PATH/

echo "--> Submitting to HTCondor..."
ssh $SSH_OPTS ${username}@lxplus.cern.ch "cd $REMOTE_PATH && condor_submit submission.sub"

rm -f files.tar.gz executable.sh submission.sub
ssh -t $SSH_OPTS ${username}@lxplus.cern.ch "cd $REMOTE_PATH; exec \$SHELL -l"
