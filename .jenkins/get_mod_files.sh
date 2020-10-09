#!/bin/bash

source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

git clone --recursive ssh://bbpcode.epfl.ch/sim/models/neocortex mod/neocortex
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/hippocampus mod/hippocampus
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/mousify mod/mousify
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/thalamus mod/thalamus

