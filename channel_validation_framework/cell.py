from neuron import h

from .utils import *


class Cell:
    def __init__(self, mod, conf, name):

        # Ref to mod data
        self.mod = mod
        # Set data from config file
        self.conf = conf

        self.name = name

        self.soma = h.Section(name=self.name, cell=self)
        self.soma.insert("pas")
        # Some keywords in channel could be inserted in h or soma directly
        for att_name, att_value in self.conf["channel"].items():
            try:
                setattr(self.soma, att_name, att_value)
            except Exception:
                try:
                    setattr(h, att_name, att_value)
                except Exception:
                    pass

    def set_mechanism(self):
        if "SUFFIX" in self.mod["NEURON"]:
            # useion
            self.soma.insert(self.mod.mechanism())
            # set initial values
            try:

                for key, value in self.conf["channel"]["USEION"]["READ"].items():
                    setattr(self.soma, key, value)
            except KeyError:
                pass

        if "POINT_PROCESS" in self.mod["NEURON"]:
            self.pp = getattr(h, self.mod["NEURON"]["POINT_PROCESS"][0])(self.soma(0.5))
            try:
                self.pp.setRNG(
                    self.conf["channel"]["rng"][0],
                    self.conf["channel"]["rng"][1],
                    self.conf["channel"]["rng"][2],
                )
            except AttributeError:
                pass

    def record_traces(self):

        self.traces = {}

        for name in self.conf["channel"]["USEION"].get("WRITE", []):
            record_trace(name, self.soma(0.5), self.traces)

        # non-specific currents are inserted with the suffix
        for name in self.conf["channel"].get("NONSPECIFIC_CURRENT", []):

            try:
                if "POINT_PROCESS" in self.mod["NEURON"]:
                    record_trace(name, self.pp, self.traces)
                else:
                    record_trace(
                        "{}_{}".format(name, self.mod.mechanism()),
                        self.soma(0.5),
                        self.traces,
                    )
            except AttributeError:
                pass

        record_trace("v", self.soma(0.5), self.traces)

    def set_stimulus(self, result):
        # set std stimulus
        self.stimulus = h.cvf_svclamp(self.soma(0.5))
        self.stimulus.rs = 0.001
        self.stimulus.dur1 = h.tstop

        # play
        TwaveForm, VwaveForm = get_step_wave_form(result.t_steps, result.v_steps, h.dt)
        self.stimulus_input = [h.Vector(TwaveForm), h.Vector(VwaveForm)]
        self.stimulus_input[1].play(
            self.stimulus, self.stimulus._ref_amp1, self.stimulus_input[0], 1
        )
