#!/bin/bash

set -ex

#spack install coreneuron@develop+sympy+nmodl ^nmodl@develop ^bison@3.4.2
#spack install neuron@develop

module load neuron/develop coreneuron/develop


rm -rf nrnivmech_install.sh x86_64 enginemech.o

nrnivmodl mod
nrnivmodl-core mod

./x86_64/special -python run_tests.py 2>&1 | tee run_tests.log | grep CVF

