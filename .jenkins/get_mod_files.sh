#!/bin/bash

source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

git clone --recursive ssh://git@bbpgitlab.epfl.ch/hpc/sim/models/neocortex mod/neocortex
git clone --recursive ssh://git@bbpgitlab.epfl.ch/hpc/sim/models/hippocampus mod/hippocampus
git clone --recursive ssh://git@bbpgitlab.epfl.ch/hpc/sim/models/mousify mod/mousify
git clone --recursive ssh://git@bbpgitlab.epfl.ch/hpc/sim/models/thalamus mod/thalamus

