#!/usr/bin/bash

set -ex

#spack install coreneuron+nmodl+sympy@develop ^nmodl@develop
# Install coreneuron without nmodl to avoid error with solve method
spack install coreneuron@develop

spack install neuron@develop

spack module tcl refresh --y --latest coreneuron
spack module tcl refresh --y --latest neuron

module av coreneuron neuron

module load coreneuron/develop neuron/develop

module list

rm -rf x86_64 enginemech.o

# Remove svclmp.mod from mod to avoid redefinition of SEClamp in Neuron
mv mod/svclmp.mod .

nrnivmodl mod

# Move it back to add it to CoreNEURON executable
mv svclmp.mod mod

nrnivmodl-core mod

# For BB%
unset PMI_RANK

# Run script that launches CoreNEURON with SEClamp call
./x86_64/special -python neuron_direct.py
