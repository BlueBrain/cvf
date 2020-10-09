#!/bin/bash
source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

module purge
module load unstable

module load neuron/develop nmodl/develop
module av
module load python-dev

python3 -mvenv $BUILD_HOME/venv
source $BUILD_HOME/venv/bin/activate

python3 setup.py install

cvf_stdrun mod/cvf mod/neocortex/mod/v5
cvf_stdrun mod/cvf mod/hippocampus/mod
cvf_stdrun mod/cvf mod/thalamus/mod
cvf_stdrun mod/cvf mod/mousify/mod