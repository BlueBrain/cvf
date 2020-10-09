import glob
import logging
import os
from multiprocessing import Queue, Process
from pathlib import Path
from queue import Empty, Full

import numpy as np
from neuron import h, gui, coreneuron  # black could remove gui from here. It is needed

from . import utils
from .cell import Cell
from .netcon import Netcon
from .run_result import RunResult


class SimulationError(Exception):
    pass


class Simulation:
    def __init__(self, working_dir, config):
        self.working_dir = working_dir
        self.conf = config

    def run_all_protocols(self, simulator):
        results = []

        for protocol in self.conf:
            results.append(
                self.run(
                    RunResult(
                        modfile=Path(self.conf.mod.modpath).stem,
                        protocol=protocol,
                        simulator=simulator,
                        traces={},
                    )
                )
            )

        return results

    def run(self, result):

        q = Queue()
        p = Process(
            target=self._worker_run,
            args=(
                result,
                q,
            ),
        )

        p.start()
        while p.is_alive():
            try:
                out = q.get(timeout=0.1)
            except Empty:
                continue
            break

        if p.exitcode:
            m = "Worker terminated with exit code {}".format(p.exitcode)
            raise SimulationError(m)

        if p.is_alive():
            p.join(timeout=0.1)

        return out

    def _worker_run(self, result, queue):
        logging.info(f"Run simulation: {result.modfile}")

        self._load_libs(result.simulator)

        h.tstop = self.conf.tstop(result.protocol)
        logging.info(f"tstop: {h.tstop}")
        h.cvode.use_fast_imem(1)
        h.cvode.cache_efficient(1)

        # set morphology, stimuli, and record traces
        logging.info("Init simulator")
        self._init_simulator(result)

        # run simulation
        logging.info("stdinit")
        h.stdinit()
        if result.simulator == utils.Simulators.NEURON:
            h.v_init = self.conf[result.protocol]["global"]["data"]["v_init"]
            logging.info("run NEURON")
            h.run()
        else:
            coreneuron.enable = True
            pc = h.ParallelContext()
            logging.info("run CORENEURON")
            pc.psolve(h.tstop)

        # get traces
        self._get_traces(result)
        self._get_global_traces(result)

        while True:
            try:
                queue.put(result, timeout=0.1)
                break
            except Full:
                continue

    def _load_libs(self, simulator):

        try:
            nrn_lib = os.path.abspath(
                glob.glob(os.path.join(self.working_dir, "x86_64", "libnrnmech.*"))[0]
            )
        except IndexError as e:
            raise SimulationError("nrn_lib not found!") from e
        h.nrn_load_dll(nrn_lib)

        if simulator is not utils.Simulators.NEURON:
            try:
                corenrn_lib = os.path.abspath(
                    glob.glob(
                        os.path.join(self.working_dir, "x86_64", "libcorenrnmech.*")
                    )[0]
                )
            except IndexError as e:
                raise SimulationError("corenrn_lib not found!") from e
            os.environ["CORENEURONLIB"] = corenrn_lib

    def _init_simulator(self, result):
        protocol = self.conf[result.protocol]
        utils.set_data(protocol["global"], h)

        self.sections = {}
        for k, v in protocol["sections"].items():
            self.sections[k] = Cell(k, v)

        if "netcons" in protocol:
            h.load_file("netparmpi.hoc")
            pnm = h.ParallelNetManager(len(protocol["netcons"]))  # 1 netcon, 1 "cell"
            self.netcons = {}
            for name, data in protocol["netcons"].items():
                self.netcons[name] = Netcon(name, data, self.sections)
                pnm.set_gid2node(0, pnm.myid)  # alternatively: pnm.round_robin()
                pnm.pc.cell(0, self.netcons[name].netcon)

        self._record_global_traces()

    def _record_global_traces(self):
        self.traces = {}

        self.traces["t"] = h.Vector()
        self.traces["t"].record(getattr(h, utils.std_trace_name("t")))

        self.traces["netcon"] = h.Vector()
        self.traces["netcon_gids"] = h.Vector()
        pc = h.ParallelContext()
        pc.spike_record(-1, self.traces["netcon"], self.traces["netcon_gids"])

    # hard copy is necessary since next simulations override
    def _get_traces(self, result):
        for k, v in self.sections.items():
            utils.convert_and_copy_traces(v.traces, result.traces, k)

    def _get_global_traces(self, result):
        result.tvec = np.array(self.traces.pop("t")).copy()
        self.traces.pop("netcon_gids", None)  # we do not need gids for now

        utils.convert_and_copy_traces(self.traces, result.traces, "global")
