#!/bin/bash
source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

module purge
module load unstable

module load neuron/develop coreneuron/develop nmodl/develop
module av
module load python/3.7.4

python3.7 -mvenv $BUILD_HOME/venv
source $BUILD_HOME/venv/bin/activate

python3.7 setup.py install

cvf_stdrun
