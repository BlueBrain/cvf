import logging
import subprocess
import sys
from itertools import cycle
from multiprocessing import Process, Queue

import numpy as np
from termcolor import colored

from .config_parser import Config
from .utils import *

try:
    import matplotlib.pyplot as pplt
    from matplotlib import colors
except ImportError:
    logging.warning("Matplotlib could no be found. Proceeding without plots...")


# do not import from neuron


class CompareTestResultsError(Exception):
    pass


def cvf_in2yaml(config_folder="config"):
    for subdir, dirs, files in os.walk(config_folder):
        for file in files:
            filepath = subdir + os.sep + file
            if file.endswith(".in"):
                config = Config(filepath)
                config.dump_to_yaml()


def cvf_stdrun():

    config_file = sys.argv[1] if len(sys.argv) > 1 else ""
    additional_mod_folders = sys.argv[3:] if len(sys.argv) > 3 else []

    results = run(
        config_file=config_file, additional_mod_folders=additional_mod_folders,
    )

    compare(results)

    return 0


def run(
    config_file=None,
    additional_mod_folders=[],
    simulators={Simulators.NEURON, Simulators.CORENEURON_NMODLSYMPY_ANALYTIC,},
    base_working_dir="tmp",
    fail_on_cell_generation=False,
):
    if isinstance(additional_mod_folders, str):
        additional_mod_folders = [additional_mod_folders]

    # clear the state
    silent_remove([base_working_dir + "_*"])

    if config_file:
        config_file = os.path.abspath(config_file)

    results = {}
    jobs = []
    for simulator in simulators:
        q = Queue()
        p = Process(
            target=_worker_run,
            args=(
                config_file,
                additional_mod_folders,
                simulator,
                base_working_dir,
                fail_on_cell_generation,
                q,
            ),
        )
        jobs.append(p)
        p.start()
        results[simulator] = q.get()

    for p in jobs:
        p.join()

    return results


def _worker_run(
    config_file,
    additional_mod_folders,
    simulator,
    base_working_dir,
    fail_on_cell_generation,
    queue,
):

    # we want to print the info
    logging.getLogger().setLevel(logging.INFO)

    working_dir = "{}_{}_{}".format(base_working_dir, simulator.name, str(os.getpid()))
    os.makedirs(working_dir + os.sep + "mod")

    # we add the custom cvf mod files
    additional_mod_folders.append("mod" + os.sep + "cvf")
    additional_mod_folders.append("mod" + os.sep + "local")
    copy_to_working_dir_log = copy_to_working_dir(
        additional_mod_folders, working_dir + os.sep + "mod", ".mod"
    )
    logging.info(
        "The following files were copied in '%s': \n%s",
        working_dir,
        "".join(copy_to_working_dir_log),
    )

    # call the compilers
    subprocess.run(["nrnivmodl", "mod"], cwd=working_dir)
    if simulator is not Simulators.NEURON:
        # TODO: add support for compiling with different sympy options
        subprocess.run(["nrnivmodl-core", "mod"], cwd=working_dir)

    # Import libraries since they are not in the standard
    from neuron import h

    h.nrn_load_dll(
        os.path.abspath(
            glob.glob(
                working_dir
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
                working_dir
                + os.sep
                + "x86_64"
                + os.sep
                + ".libs"
                + os.sep
                + "libcorenrnmech.*"
            )[0]
        )

    from .cell import Cell

    results = []
    for subdir, dirs, files in os.walk(working_dir + os.sep + "mod"):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".mod") and filepath.find("cvf") == -1:
                if fail_on_cell_generation:
                    cell0 = Cell(filepath, config_file)
                else:
                    try:
                        cell0 = Cell(filepath, config_file)
                    except Exception as e:
                        results.append(e)
                        continue

                results.extend(cell0.run_all_protocols(simulator))

    queue.put(results)


def compare(results, main_simulator=Simulators.NEURON, rtol=1e-6, atol=0.0, verbose=2):
    is_error = False

    remove_duplicate_log = set()
    for simulator, tests in results.items():
        if simulator == main_simulator:
            continue

        print("Compare {} with {}".format(main_simulator.name, simulator.name))

        # avoid mechanisms that are not supported
        if isinstance(tests, Exception):
            print("CVF - {}, {}".format(colored("FAIL", "red"), str(tests)))
            is_error = True
            continue

        for base_res, test_res in zip(results[main_simulator], tests):
            key = base_res.mechanism + base_res.stimulus + simulator.name
            mse = max(
                [
                    compute_mse(base_trace, test_res.traces[trace_name])
                    for trace_name, base_trace in base_res.traces.items()
                ]
            )

            err = False

            try:
                for trace_name, base_trace in base_res.traces.items():
                    test_trace = test_res.traces[trace_name]
                    np.testing.assert_allclose(base_trace, test_trace, rtol, atol)
            except AssertionError as e:
                err = e
                is_error = True

            if verbose == 3 or (
                verbose == 2
                and (isinstance(err, AssertionError) or key not in remove_duplicate_log)
            ):
                print(
                    "CVF - {} - {}, {}, mse={} {}".format(
                        (colored("SUCCESS", "green"), colored("FAIL", "red"))[
                            isinstance(err, AssertionError)
                        ],
                        base_res.mechanism,
                        test_res.stimulus,
                        mse,
                        ("", err)[isinstance(err, AssertionError)],
                    )
                )
                remove_duplicate_log.add(key)

    if is_error:
        raise CompareTestResultsError("Some tests failed")
    elif verbose == 1:
        print("SUCCESS!")


def plot(results):
    remove_duplicate_log = set()

    colit = cycle(dict(colors.BASE_COLORS))

    fign = 0
    for (simulator, tests), col in zip(results.items(), dict(colors.BASE_COLORS)):
        fign += 1
        col = next(colit)
        for test in tests:
            for trace_name, trace_vec in test.traces.items():
                label = "{}, {}, {}, {}".format(
                    test.mechanism, test.stimulus, test.simulator.name, trace_name
                )
                label = (label, "")[label in remove_duplicate_log]

                pplt.figure(0)
                pplt.plot(
                    test.tvec, trace_vec, color=col, label=label,
                )
                remove_duplicate_log.add(label)

                pplt.figure(fign)
                pplt.plot(
                    test.tvec, trace_vec, color=col, label=label,
                )

        pplt.figure(0)
        pplt.xlabel("t (msec)")
        pplt.legend()

        pplt.figure(fign)
        pplt.xlabel("t (msec)")
        pplt.legend()

    pplt.show()
