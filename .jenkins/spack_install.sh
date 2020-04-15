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
        sedexp="$sedexp; s#branch=[^)]*)#branch='$branch', preferred=True)#g"  # replace branch
        sed_apply "$pkg_file" "$sedexp"
    fi
)

set -ex
source ${JENKINS_DIR:-.}/_env_setup.sh

check_patch_project coreneuron "$CORENEURON_BRANCH"
check_patch_project nmodl "$NMODL_BRANCH"
spack install coreneuron@develop+sympy+nmodl ^nmodl@develop ^bison@3.4.2

check_patch_project neuron "$NEURON_BRANCH"
spack install neuron@develop

source $SPACK_ROOT/share/spack/setup-env.sh
module av neuron coreneuron