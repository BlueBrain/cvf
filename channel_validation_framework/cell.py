import logging

from neuron import h, gui

from . import utils


class Cell:
    def __init__(self, name, conf):
        self.name = name
        self.conf = conf
        self.traces = {}

        self.section = h.Section(name=self.name, cell=self)
        self.section.insert("pas")

        logging.info("SET CELL {}".format(self.name))
        self._set_mechanisms()
        utils.set_data(self.conf, self.section)

        if "record_traces" in self.conf:
            self._record_traces(self.conf["record_traces"])

        self._set_inputs()

        logging.info("CELL SETUP COMPLETED")

    def _set_mechanisms(self):
        if "mechanisms" in self.conf:
            for mech, mech_conf in self.conf["mechanisms"].items():
                logging.info("SET MECHANISM {}:{}".format(mech, mech_conf["type"]))
                if mech_conf["type"] == "SUFFIX":
                    self.section.insert(mech)
                    if "rng" in mech_conf:
                        getattr(h, f"setdata_{mech}")(self.section(0.5))
                        getattr(h, f"setRNG_{mech}")(*mech_conf["rng"])

                elif mech_conf["type"] == "POINT_PROCESS":
                    self.pp = getattr(h, mech)(self.section(0.5))
                    if "rng" in mech_conf:
                        self.pp.setRNG(*mech_conf["rng"])

                utils.set_data(mech_conf, self.section)

    def _record_traces(self, dic, suffix=""):
        for i in dic:
            key = i + suffix
            self.traces[key] = h.Vector()
            try:
                self.traces[key].record(
                    getattr(self.section(0.5), utils.std_trace_name(i))
                )
            except AttributeError:
                self.traces[key].record(getattr(self.pp, utils.std_trace_name(i)))

    def _set_inputs(self):
        if "inputs" in self.conf:
            self.inputs = {}
            for var, steps in self.conf["inputs"].items():
                TwaveForm, VwaveForm = utils.get_step_wave_form(
                    steps["t_steps"], steps["y_steps"], h.dt
                )
                input_traces = [h.Vector(TwaveForm), h.Vector(VwaveForm)]
                logging.info("SET INPUT {}".format(var))

                if var == "v":
                    s = h.cvf_svclamp(self.section(0.5))
                    s.rs = 0.001
                    s.dur1 = h.tstop

                    input_traces[1].play(s, s._ref_amp1, input_traces[0], 1)
                else:
                    s = getattr(self.section(0.5), utils.std_trace_name(var))
                    input_traces[1].play(s, input_traces[0], 1)

                self.inputs[var] = (s, input_traces)

            self._record_traces(self.inputs, "_in")
