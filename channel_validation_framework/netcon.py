import logging

from neuron import h, gui

from . import utils


class Netcon:
    def __init__(self, name, conf, sections):
        self.name = name
        self.conf = conf

        source, source_var = next(iter(self.conf["source"].items()))
        target = self.conf["target"]
        logging.info("SET NETCON {}".format(self.name))

        self.netcon = h.NetCon(
            getattr(sections[source].section(0.5), utils.std_trace_name(source_var)),
            sections[target].pp,
        )
        utils.set_data(self.conf, self.netcon)
