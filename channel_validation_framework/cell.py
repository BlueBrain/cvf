import numpy as np
from neuron import h, gui  # pycharm could remove gui from here. It is needed
from recordtype import recordtype
import os

from .config_parser import Config
from .mod_parser import Mod
from .utils import get_V_steps, get_step_wave_form, Simulators

RunResult = recordtype(
    "RunResult",
    [
        "mechanism",
        "stimulus",
        "simulator",
        "t_steps",
        "v_steps",
        ("tvec", []),
        ("traces", {}),
    ],
    default="",
)


class Cell:
    def __init__(self, filepath, config_file_path=None):
        self.filepath = filepath
        self.config_file_path = config_file_path

        # Load mod data and set main mechanism
        self.mod = Mod(self.filepath)
        # Set data from config file
        self.conf = Config(self.config_file_path, self.mod)

        self._set_cell()

    def _set_cell(self):
        # Set a few basic things
        self.soma = h.Section(name="soma")
        self.soma.insert("pas")
        self.vc = h.cvf_svclamp(self.soma(0.5))
        self.vc.rs = 0.001
        # Some keywords in channel could be inserted in h or soma directly
        for att_name, att_value in self.conf.data["channel"].items():

            try:
                setattr(self.soma, att_name, att_value)
            except Exception:
                try:
                    setattr(h, att_name, att_value)
                except Exception:
                    pass
        # mechanism
        self.mechanism = self.mod.data["NEURON"]["SUFFIX"][0]
        self.soma.insert(self.mechanism)
        # try useion
        try:
            for key, value in self.conf.data["channel"]["USEION"]["READ"]:
                setattr(self.soma, key, value)
        except:
            pass

    @staticmethod
    def trace_name(name):
        return "_ref_{}".format(name)

    def _set_traces(self):
        traces = {}
        try:
            for name in self.conf.data["channel"]["USEION"]["WRITE"]:
                new_trace = h.Vector()
                new_trace.record(getattr(self.soma(0.5), self.trace_name(name)))
                traces[name] = new_trace
        except KeyError:
            pass

        i_mem = h.Vector()
        i_mem.record(self.soma(0.5)._ref_i_membrane_)
        traces["i_membrane_"] = i_mem

        return traces

    def _get_traces(self, traces):
        out = {}
        for key, val in traces.items():
            out[key] = np.array(val).copy()
        return out

    def run_simulator(self, result):

        h.cvode.use_fast_imem(1)
        h.cvode.cache_efficient(1)

        TwaveForm, VwaveForm = get_step_wave_form(result.t_steps, result.v_steps, h.dt)

        self.vc.dur1 = h.tstop
        TwaveForm = h.Vector(TwaveForm)
        VwaveForm = h.Vector(VwaveForm)

        VwaveForm.play(self.vc, self.vc._ref_amp1, TwaveForm, 1)

        tvec = h.Vector()
        tvec.record(h._ref_t)

        # start recording
        traces = self._set_traces()

        if result.simulator == Simulators.NEURON:
            h.init()
            h.run()
        else:
            pc = h.ParallelContext()
            h.stdinit()

            pc.nrncore_run(
                " -e {} -v {}".format(h.tstop, self.conf.data["channel"]["v_init"]), 0
            )

        result.tvec = np.array(tvec).copy()
        result.traces = self._get_traces(traces)

    def run_protocol(self, stimulus, simulator):

        [t_steps, v_steps_zipped] = self.conf.extract_steps_from_stimulus(stimulus)
        h.tstop = self.conf.data["stimulus"][stimulus]["tstop"]
        v_steps_mat = get_V_steps(v_steps_zipped)

        results = []
        for v_steps in v_steps_mat:
            results.append(
                RunResult(
                    mechanism=self.mechanism,
                    stimulus=stimulus,
                    simulator=simulator,
                    t_steps=t_steps,
                    v_steps=v_steps,
                )
            )
            self.run_simulator(results[-1])

        return results

    def run_all_protocols(self, simulator):
        results = []
        for protocol_name in self.conf.data["stimulus"]:
            results += self.run_protocol(protocol_name, simulator)

        return results
