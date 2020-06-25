import numpy as np
from neuron import h, gui  # pycharm could remove gui from here. It is needed
from recordtype import recordtype

from .config_parser import Config
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
        ("trace", []),
    ],
    default="",
)


class Cell:
    def __init__(self, config_file_path, mechanism):
        self.config_file_path = config_file_path
        self.mechanism = mechanism

        # Set a few basic things
        self.soma = h.Section(name="soma")
        self.soma.insert("pas")
        # self.vc = h.SEClamp(self.soma(0.5))
        self.vc = h.custom_SEClamp(self.soma(0.5))
        self.vc.rs = 0.001
        self.soma.insert(self.mechanism)

        # Set data from config file
        self.init_config()

    def init_config(self):
        self.conf = Config(self.config_file_path)
        data = self.conf.channel_data

        for att_name, att_value in data.items():
            try:
                setattr(self.soma, att_name, att_value)
            except Exception:
                try:
                    setattr(h, att_name, att_value)
                except Exception:
                    pass

        setattr(self.soma, data["revName"], data["revValue"])

    def trace_name(self):
        return "_ref_" + self.conf.channel_data["current"]

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

        trace = h.Vector()
        trace.record(getattr(self.soma(0.5), self.trace_name()))

        if result.simulator == Simulators.NEURON:
            h.init()
            h.run()
        elif result.simulator == Simulators.CORENEURON:
            pc = h.ParallelContext()
            h.stdinit()
            pc.nrncore_run(
                " -e {} -v {}".format(h.tstop, self.conf.channel_data["v_init"]), 0
            )

        result.tvec = np.array(tvec).copy()
        result.trace = np.array(trace).copy()

    def run_protocol(self, stimulus, simulators):

        [t_steps, v_steps_zipped] = self.conf.extract_steps_from_stimulus(stimulus)
        h.tstop = self.conf.stimulus[stimulus]["tstop"]
        v_steps_mat = get_V_steps(v_steps_zipped)

        results = []
        for v_steps in v_steps_mat:
            result_sim_col = []
            for simulator in simulators:
                result_sim_col.append(
                    RunResult(
                        mechanism=self.mechanism,
                        stimulus=stimulus,
                        simulator=simulator,
                        t_steps=t_steps,
                        v_steps=v_steps,
                    )
                )
                self.run_simulator(result_sim_col[-1])

            results.append(result_sim_col)

        return results

    def run_all_protocols(self, simulators):
        results = []
        for protocol_name in self.conf.stimulus:
            results += self.run_protocol(protocol_name, simulators)

        return results
