#!/bin/bash

source ${JENKINS_DIR:-.}/_env_setup.sh
set -ex

ls

cd mod

ls

git clone --recursive ssh://bbpcode.epfl.ch/sim/models/neocortex
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/hippocampus
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/mousify
git clone --recursive ssh://bbpcode.epfl.ch/sim/models/thalamus

