from enum import Enum
from multiprocessing import Process, Queue

from neuron import h, gui  # black could remove gui from here. It is needed

from .cell import Cell
from .config_parser import Config
from .mod_parser import Mod
from .run_result import RunResult
from .utils import *


class SimulationError(Exception):
    pass


class Simulation:
    class Morphology(Enum):
        SINGLE_CELL = auto()
        PRE_POST_CELLS = auto()

    def __init__(self, working_dir, filepath, config_file=None):
        self.working_dir = working_dir
        self.mod = Mod(filepath)
        self.conf = Config(config_file, self.mod)
        self.init_morphology()

    def init_morphology(self):
        if "SUFFIX" in self.mod["NEURON"]:
            self.morphology = self.Morphology.SINGLE_CELL
        elif "POINT_PROCESS" in self.mod["NEURON"]:
            if "NET_RECEIVE" in self.mod:
                self.morphology = self.Morphology.PRE_POST_CELLS
            else:
                self.morphology = self.Morphology.SINGLE_CELL
        else:
            raise SimulationError("Unknown mechanism: proper morphology unknown")

    def run(self, simulator):
        results = []
        for protocol_name in self.conf["stimulus"]:
            results += self.run_protocol(protocol_name, simulator)

        return results

    def run_protocol(self, stimulus, simulator):
        t_steps = self.conf["stimulus"][stimulus]["t_steps"]
        v_steps_zipped = self.conf["stimulus"][stimulus]["v_steps"]
        h.tstop = self.conf["stimulus"][stimulus]["tstop"]

        v_steps_mat = get_V_steps(v_steps_zipped)

        results = []
        for v_steps in v_steps_mat:
            results.append(
                RunResult(
                    mechanism=self.mod.mechanism(),
                    stimulus=stimulus,
                    simulator=simulator,
                    t_steps=t_steps,
                    v_steps=v_steps,
                    traces={},
                )
            )
            results[-1] = self.run_simulator(results[-1])

        return results

    def run_simulator(self, result):

        q = Queue()
        p = Process(target=self._worker_run, args=(result, q,),)

        p.start()
        out = q.get()

        p.join()

        return out

    def _worker_run(self, result, queue):

        self._load_libs(result.simulator)

        h.cvode.use_fast_imem(1)
        h.cvode.cache_efficient(1)

        # set morphology, stimuli, and record traces
        self._init_simulator(result)

        # run simulation
        h.stdinit()
        if result.simulator == Simulators.NEURON:
            h.run()
        else:
            pc = h.ParallelContext()
            pc.nrncore_run(
                " -e {} -v {}".format(h.tstop, self.conf["channel"]["v_init"]), 0
            )

        # get traces
        self._get_traces(result)
        self._get_global_traces(result)

        queue.put(result)

    def _load_libs(self, simulator):

        h.nrn_load_dll(
            os.path.abspath(
                glob.glob(
                    self.working_dir
                    + os.sep
                    + "x86_64"
                    + os.sep
                    + ".libs"
                    + os.sep
                    + "libnrnmech.*"
                )[0]
            )
        )

        if simulator is not Simulators.NEURON:
            os.environ["CORENEURONLIB"] = os.path.abspath(
                glob.glob(
                    self.working_dir
                    + os.sep
                    + "x86_64"
                    + os.sep
                    + ".libs"
                    + os.sep
                    + "libcorenrnmech.*"
                )[0]
            )

    def _init_simulator(self, result):

        if self.morphology == self.Morphology.SINGLE_CELL:
            self.cell = Cell(self.mod, self.conf, "cell")
            self.cell.set_mechanism()
            self.cell.set_stimulus(result)

            # record
            self.cell.record_traces()
            self._record_global_traces()
        elif self.morphology == self.Morphology.PRE_POST_CELLS:
            # pre cell
            self.pre_cell = Cell(self.mod, self.conf, "pre_cell")
            self.pre_cell.set_stimulus(result)
            self.pre_cell.record_traces()
            # post cell
            self.post_cell = Cell(self.mod, self.conf, "post_cell")
            self.post_cell.set_mechanism()
            self.post_cell.record_traces()
            # netcon
            self.nc = h.NetCon(self.pre_cell.soma(0.5)._ref_v, self.post_cell.pp,)
            self.nc.weight[0] = self.conf["channel"]["netcon"]["weight"]
            self.nc.delay = self.conf["channel"]["netcon"]["delay"]
            self.nc.threshold = self.conf["channel"]["netcon"]["threshold"]
            # set gids for coreneuron
            h.load_file("netparmpi.hoc")
            pnm = h.ParallelNetManager(1)  # 1 netcon, 1 "cell"
            pnm.set_gid2node(0, pnm.myid)  # alternatively: pnm.round_robin()
            pnm.pc.cell(0, self.nc)

            self._record_global_traces()

    def _record_global_traces(self):
        self.traces = {}

        record_trace("t", h, self.traces)

        if self.morphology == self.Morphology.PRE_POST_CELLS:
            self.traces["netcon"] = h.Vector()
            self.traces["netcon_gids"] = h.Vector()
            pc = h.ParallelContext()
            pc.spike_record(-1, self.traces["netcon"], self.traces["netcon_gids"])

    # hard copy is necessary since next simulations override
    def _get_traces(self, result):
        if self.morphology is self.Morphology.SINGLE_CELL:
            convert_and_copy_traces(self.cell.traces, result.traces, "cell_")

        elif self.morphology is self.Morphology.PRE_POST_CELLS:
            convert_and_copy_traces(self.pre_cell.traces, result.traces, "pre_")
            convert_and_copy_traces(self.post_cell.traces, result.traces, "post_")

    def _get_global_traces(self, result):
        result.tvec = np.array(self.traces.pop("t")).copy()
        self.traces.pop("netcon_gids", None)  # we do not need gids for now
        convert_and_copy_traces(self.traces, result.traces, "global_")
