from neuron import h, gui
from channel_validation_framework.config_reader import ConfigReader
import numpy as np



def getStepWaveform(tv_paired_list):
    out = []
    for t, v in tv_paired_list:
        out.extend([v] * int(t/h.dt))
    return out


def generateVsteps(v):
    out = []
    leading_v_ramp_idx = [idx for idx, x in enumerate(v) if isinstance(x, list)]
    if len(leading_v_ramp_idx):
        leading_v_ramp_idx = leading_v_ramp_idx[0]
        leading_v_ramp = v[leading_v_ramp_idx]
        for v_step in np.arange(leading_v_ramp[0], leading_v_ramp[2], leading_v_ramp[1]):
            v_run = v
            v_run[leading_v_ramp_idx] = v_step
            out.append(v_run)
    else:
        out.append(v)

    return out

def normalize(mat, normalize_with_min):
    val = (min(mat), max(mat))[normalize_with_min]
    if (val):
        mat *= 1.0/val
    return mat




















class Cell:

    def runWaveformProtocol(self, vWaveForm, isNeuron):
        self.vc.dur1 = h.tstop
        v = h.Vector(vWaveForm)
        v.play(self.vc.amp1)

        tvec = h.Vector()
        tvec.record(h._ref_t)

        ivec = h.Vector()
        ivec.record(getattr(self.soma(0.5), "_ref_" + self.conf.channel_data["current"]))


        if (isNeuron):
            h.init()
            h.run()
        else:
            h.stdinit()
            h.ParallelContext().nrncore_run("-e %g" % h.tstop, 0)

        return tvec, ivec




    def runProtocol(self, stimulus_name, isCore):
        [t, v] = self.conf.extract_steps_from_stimulus(stimulus_name)
        h.tstop = self.conf.stimulus[stimulus_name]["tstop"]

        v_steps_mat = generateVsteps(v)

        v_list = []
        i_list = []
        for v_steps in v_steps_mat:
            vvec = getStepWaveform(zip(t, v_steps))
            [tvec, ivec] = self.runWaveformProtocol(vvec, isCore)
            v_list.extend([h.v_init] + vvec)
            i_list.extend(ivec)

        v_list = np.array(v_list)
        i_list = np.array(i_list)

        normalize_with_min = "inward" != self.conf.stimulus[stimulus_name]["type"]
        normalize(v_list, normalize_with_min)
        normalize(i_list, normalize_with_min)

        return v_list, i_list



    def __init__(self, config_file_path, mechanism_name):
        self.config_file_path = config_file_path
        self.mechanism_name = mechanism_name

        # Set a few basic things
        self.soma = h.Section(name='soma')
        self.soma.insert('pas')
        # self.vc = h.SEClamp(self.soma(0.5))
        self.vc = h.custom_SEClamp(self.soma(0.5))
        self.vc.rs = 0.001
        self.soma.insert(self.mechanism_name)


        # Set data from config file
        self.initConfig()

        # print(self.soma.psection())







    def initConfig(self):
        self.conf = ConfigReader.parse_file(self.config_file_path)
        # TODO check that the channel can match the mechanism (i.e.: hhkin must match the channel kv)
        data = self.conf.channel_data #next(iter(self.conf.channel.items()))[1]
        # TODO We want errors if the config file is not conform
        self.soma.L = data['L']
        self.soma.diam = data['diam']
        self.soma.Ra = data["Ra"]
        setattr(self.soma, data["revName"], data["revValue"])
        # TODO: I have no idea what is this term. It was set and never used
        # setattr(self.soma, "gbar_Kv1_1" , 1.0)
        self.soma.g_pas = data["g_pas"]
        h.v_init = data["v_init"]



import os
def find_first_of_in_file(file, keyword):
    token = f.readline()
    while token:
        if token.find(keyword) != -1:
            return token
        token = f.readline()

    return ""



config_file_path = "configs/kv.in"
mod_root = "mod"

h.cvode.cache_efficient(1)

for subdir, dirs, files in os.walk(mod_root):
    for file in files:
        filepath = subdir + os.sep + file
        print(filepath)
        if filepath.endswith(".mod") and filepath.find("custom") == -1:

            # TODO: this way of picking up the suffix could be dangerous
            f = open(filepath, "r")
            find_first_of_in_file(f, "NEURON")
            mechanism_name = find_first_of_in_file(f, "SUFFIX").split()[1]
            f.close()

            cell0 = Cell(config_file_path, mechanism_name)
            [a, b] = cell0.runProtocol("Activation", True)
            print(b)

            [a, b] = cell0.runProtocol("Activation", False)
            print(b)



quit()


