!/usr/bin/bash

set -ex

spack install coreneuron@develop neuron@develop

spack module tcl refresh --y --latest coreneuron
spack module tcl refresh --y --latest neuron

module load coreneuron/develop-parallel neuron/develop-parallel

# Remove svclmp.mod from mod to avoid redefinition of SEClamp in Neuron
mv mod/svclmp.mod .

nrnivmodl mod

# Move it back to add it to CoreNEURON executable
mv svclmp.mod mod

nrnivmodl-core mod

# Run script that launches CoreNEURON with SEClamp call
./x86_64/special -python neuron_direct.py
