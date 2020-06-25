#!/bin/bash

# Based on spack_setup.sh from blueconfigs repo
source ${JENKINS_DIR:-.}/_env_setup.sh

echo "
=====================================================================
Preparing spack environment...
====================================================================="


############################# CLONE/SETUP REPOSITORY #############################

install_spack() (
    set -ex
    BASEDIR="$(dirname "$SPACK_ROOT")"
    mkdir -p $BASEDIR && cd $BASEDIR
    rm -rf .spack   # CLEANUP SPACK CONFIGS
    SPACK_REPO=https://github.com/BlueBrain/spack.git
    SPACK_BRANCH=${SPACK_BRANCH:-"develop"}

    echo "Installing SPACK. Cloning $SPACK_REPO $SPACK_ROOT --depth 1 -b $SPACK_BRANCH"
    git clone $SPACK_REPO $SPACK_ROOT --depth 1 -b $SPACK_BRANCH
    # Use BBP configs
    cp /gpfs/bbp.cscs.ch/apps/hpc/jenkins/config/*.yaml $SPACK_ROOT/etc/spack/
    sed -i -e 's/whitelist:/whitelist:\n      - neuron\n      - coreneuron\n      - nmodl/' $SPACK_ROOT/etc/spack/modules.yaml
    sed -i -e '/- neuron+mpi~debug%intel/d' $SPACK_ROOT/etc/spack/modules.yaml

    # Use applications upstream
    cat << EOF > "$SPACK_ROOT/etc/spack/upstreams.yaml"
upstreams:
  applications:
    install_tree: /gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/applications/latest
    modules:
      tcl: /gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/applications/latest/modules
  libraries:
    install_tree: /gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/libraries/latest
    modules:
      tcl: /gpfs/bbp.cscs.ch/ssd/apps/hpc/jenkins/deploy/libraries/latest/modules
EOF
cat "$SPACK_ROOT/etc/spack/upstreams.yaml"
)

install_spack
