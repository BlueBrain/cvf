from neuron import h, gui
import numpy as np
from .config_parser import Config
from .utils import get_V_steps, get_step_wave_form
from collections import namedtuple

RunRecap = namedtuple("RunResult", ["mechanism", "stimulus", "tsteps", "vsteps"])


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

    def run_simulators(self, tvec, vvec):

        h.cvode.use_fast_imem(1)
        h.cvode.cache_efficient(1)

        self.vc.dur1 = h.tstop
        tvec = h.Vector(tvec)
        vvec = h.Vector(vvec)

        vvec.play(self.vc, self.vc._ref_amp1, tvec, 1)

        trec = h.Vector()
        trec.record(h._ref_t)

        irec = h.Vector()
        irec.record(
            getattr(self.soma(0.5), "_ref_" + self.conf.channel_data["current"])
        )

        h.init()
        h.run()

        irec_neuron = np.array(irec).copy()

        pc = h.ParallelContext()
        h.stdinit()
        pc.nrncore_run(" -e %f -v %f" % (h.tstop, self.conf.channel_data["v_init"]), 0)

        irec_core = np.array(irec).copy()

        return trec, irec_neuron, irec_core

    def run_protocol(self, stimulus):

        [t_steps, v_steps_zipped] = self.conf.extract_steps_from_stimulus(stimulus)
        h.tstop = self.conf.stimulus[stimulus]["tstop"]
        v_steps_mat = get_V_steps(v_steps_zipped)

        resMsg = "SUCCESS"
        for v_steps in v_steps_mat:
            TwaveForm, VwaveForm = get_step_wave_form(t_steps, v_steps)
            tvec, ivec, ivec_core = self.run_simulators(TwaveForm, VwaveForm)

            rr = RunRecap(self.mechanism, stimulus, t_steps, v_steps)
            try:
                np.testing.assert_almost_equal(
                    np.array(ivec_core), np.array(ivec), err_msg=rr.__str__()
                )
            except AssertionError as e:
                resMsg = "FAIL"
                print(e)

        print("CVF - {} - {}, {} ".format(resMsg, self.mechanism, stimulus))

    def run_all_protocols(self):
        for protocol_name in self.conf.stimulus:
            self.run_protocol(protocol_name)
