#!/bin/bash
source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

module load neuron/develop coreneuron/develop
module load python/3.7.4

python3.7 -mvenv $BUILD_HOME/venv
source $BUILD_HOME/venv/bin/activate

python3.7 setup.py install

cvf_run_and_compare_tests
