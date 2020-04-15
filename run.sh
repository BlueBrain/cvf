#!/bin/bash

set -ex

#spack install coreneuron@develop+sympy+nmodl ^nmodl@develop ^bison@3.4.2
#spack install neuron@develop

module purge
module load neuron/develop-parallel coreneuron/develop-parallel


rm -rf nrnivmech_install.sh x86_64 enginemech.o

nrnivmodl mod
nrnivmodl-core mod

#export CORENEURONLIB=$(pwd)/x86_64/libcorenrnmech.0.0.so

./x86_64/special -python ./channel_validation_framework/run_neuron.py

