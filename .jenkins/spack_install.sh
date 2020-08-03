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

check_patch_project coreneuron "$CORENEURON_BRANCH"
check_patch_project nmodl "$NMODL_BRANCH"
spack install -v coreneuron@develop+sympy+nmodl~mpi~report ^nmodl@develop ^bison@3.4.2

check_patch_project neuron "$NEURON_BRANCH"
spack install neuron@develop~mpi

source $SPACK_ROOT/share/spack/setup-env.sh
module av neuron coreneuron
