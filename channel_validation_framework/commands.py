import logging
import os
import subprocess
import sys

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

    results = run_tests(
        config_file=config_file, additional_mod_folders=additional_mod_folders,
    )

    compare_test_results(results)

    return 0


from multiprocessing import Process, Queue


def run_tests(
    config_file=None,
    additional_mod_folders=[],
    simulators={
        Simulators.NEURON,
        Simulators.CORENEURON_NMODLSYMPY_ANALYTIC,
        Simulators.CORENEURON_NMODLSYMPY_PADE,
    },
    base_working_dir="tmp",
):
    # clear the state
    silent_remove([base_working_dir + "_*"])

    if config_file:
        config_file = os.abspath(config_file)

    results = {}
    jobs = []
    for simulator in simulators:
        q = Queue()
        p = Process(
            target=_worker_run_tests,
            args=(config_file, additional_mod_folders, simulator, base_working_dir, q),
        )
        jobs.append(p)
        p.start()
        results[simulator] = q.get()

    for p in jobs:
        p.join()

    return results


def _worker_run_tests(
    config_file, additional_mod_folders, simulator, base_working_dir, queue
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
    from neuron import h, gui

    h.nrn_load_dll(
        working_dir + os.sep + "x86_64" + os.sep + ".libs" + os.sep + "libnrnmech.so"
    )
    os.environ["CORENEURONLIB"] = (
        working_dir
        + os.sep
        + "x86_64"
        + os.sep
        + ".libs"
        + os.sep
        + "libcorenrnmech.so"
    )

    from .cell import Cell

    results = []
    for subdir, dirs, files in os.walk(working_dir + os.sep + "mod"):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".mod") and filepath.find("cvf") == -1:
                try:
                    cell0 = Cell(filepath, config_file)
                except Exception as e:
                    results.append(e)
                    continue

                results.extend(cell0.run_all_protocols(simulator))

    queue.put(results)


def compare_test_results(
    results, main_simulator=Simulators.NEURON, rtol=1e-7, atol=0.0, verbose=2
):
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
            mse = ((base_res.trace - test_res.trace) ** 2).mean()

            err = False
            try:
                np.testing.assert_allclose(base_res.trace, test_res.trace, rtol, atol)
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


def plot_test_results(results):
    remove_duplicate_log = set()

    for (simulator, tests), clr in zip(results.items(), dict(colors.BASE_COLORS)):
        for test in tests:
            label = "{}, {}, {}".format(
                test.mechanism, test.stimulus, test.simulator.name
            )
            pplt.plot(
                test.tvec,
                test.trace,
                color=clr,
                label=(label, "")[label in remove_duplicate_log],
            )
            remove_duplicate_log.add(label)

    pplt.xlabel("t (msec)")
    pplt.legend()
    pplt.show()
