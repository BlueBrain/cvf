## channel-validation-framework

CVF aims to validate nmodl comparing its results with mod2c traces. The general scheme is presented below:

![scheme](scheme.png)

For each mechanism in the mod folder the program:
- uses nmodl and mod2c to generate c++ and c code respectively
- generates single-cell system using the appropriate configuration file (more on this later)
- runs the simulations with coreneuron/neuron
- compares the relevant traces

For each mechanism in the mod file and each stimulus in the appropriate configuration file, CVF runs a simulation and compares traces. Thus, if we want to test nmodl on a new mechanism we need to provide:
- the mod file
- the configuration file (in case the mechanism class is new)

### The configuration file

The configuration file is specific for a class of channels (i.e. all the kv channels) and instructs the code on:
- how to stimulate the cell (comparisons among various stimuli) 
- what traces must be compared. In other words, what current/voltages are relevant in the simulation
- what are the numerical values of the various constants required by the channel (i.e. reverse potentials, conductances etc.)

### Auxiliary mechanisms/point processes

In case you need to add an auxiliary mechanism/point process (A) required to analyze mechanism (B) that should not be analyzed itself by the code (i.e. a custom point process to inject a stimulus) the name of the mechanism must be prepended with "custom".  

## Installation

In order to use CVF you need coreneuron (with nmodl) and neuron installed. In case you do not have them you can get [bbp spack](https://github.com/BlueBrain/spack) and follow the installation guide for your particular sistem. After, you need to get neuron and coreneuron (with nmodl):  

```bash
spack install coreneuron@develop+sympy+nmodl ^nmodl@develop ^bison@3.4.2

spack install neuron@develop

source $SPACK_ROOT/share/spack/setup-env.sh
module av neuron coreneuron
```

where `module av neuron coreneuron` should return 
```bash
[...]
neuron/develop
[...]
coreneuron/develop
```

## Running installing the python module

```Python
python setup.py install
```

Now you can call svc_stdrun from command line:

```Bash
svc_stdrun
```

... or use the commands from the module in python. For example, for the standard run:

```python
from channel_validation_framework.commands import *
cvf_stdrun()
```

## Running without installing

You can directly call the module commands from bash:

```bash
python -c "from channel_validation_framework.commands import *; cvf_stdrun()"
```


