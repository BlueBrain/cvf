#!/usr/bin/bash

sed_apply() (
    f=$1
    sedexp=$2
    echo "PATCHING $f with '$sedexp'"
    (cd $(dirname $f) && git checkout "$(basename $f)") && sed -i "$sedexp" "$f"
    grep 'version(' "$f"
)

check_patch_project() (
    projname="$1"
    branch="$2"
    if [ "$branch" ]; then
        pkg_file="$PKGS_BASE/$projname/package.py"
        sedexp='/version.*tag=/d'  # Drop tags
        sedexp="$sedexp; s#branch=[^,]*,#branch='${branch}', preferred=True,#g" # Replace package branch
        sedexp="$sedexp; s#branch=[^,)]*)#branch='${branch}', preferred=True)#g"
        sed_apply "$pkg_file" "$sedexp"
    fi
)

set -ex
source ${JENKINS_DIR:-.}/_env_setup.sh

if [ "${ghprbGhRepository}" = "BlueBrain/CoreNeuron" ] && [ "${ghprbSourceBranch}" ]; then
    CORENEURON_BRANCH="${ghprbSourceBranch}"
fi
if [ "${ghprbGhRepository}" = "BlueBrain/nmodl" ] && [ "${ghprbSourceBranch}" ]; then
    NMODL_BRANCH="${ghprbSourceBranch}"
fi


spack config get modules

check_patch_project neuron "$NEURON_BRANCH"
spack install neuron@develop~mpi

check_patch_project coreneuron "$CORENEURON_BRANCH"
check_patch_project nmodl "$NMODL_BRANCH"

module load unstable python-dev

spack install coreneuron@develop~mpi~report ^bison@3.4.2
spack install coreneuron@develop+nmodl~mpi~report ^nmodl@develop+python ^bison@3.4.2
spack install coreneuron@develop+nmodl+ispc~mpi~report ^nmodl@develop+python ^bison@3.4.2

source $SPACK_ROOT/share/spack/setup-env.sh
module av