import os
import subprocess

import logging
import numpy as np
from termcolor import colored

from .utils import silent_remove, Simulators
from .utils import Simulators


try:
    import matplotlib.pyplot as pplt
except ImportError:
    logging.warning("Matplotlib could no be found. Proceeding without plots...")

# do not import from neuron


class CompareTestResultsError(Exception):
    pass


def cvf_run_and_compare_tests(mod_folder="mod", config_file="configs/kv.in"):
    simulators = [Simulators.NEURON, Simulators.CORENEURON]
    results = run_tests(
        mod_folder=mod_folder, config_file=config_file, simulators=simulators
    )
    compare_test_results(results)

    return 0


def run_tests(mod_folder, config_file, simulators):

    silent_remove("enginemech.o")
    silent_remove("nrnivmech_install.sh")
    silent_remove("x86_64")

    subprocess.call(["nrnivmodl", mod_folder])
    subprocess.call(["nrnivmodl-core", mod_folder])

    # Import neuron after nrnivmodl* so that libraries are not loaded twice/not loaded
    from .cell import Cell
    from .utils import find_first_of_in_file

    results = []
    for subdir, dirs, files in os.walk(mod_folder):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".mod") and filepath.find("custom") == -1:
                f = open(filepath, "r")
                find_first_of_in_file(f, "NEURON")
                mechanism_name = find_first_of_in_file(f, "SUFFIX").split()[1]
                f.close()

                cell0 = Cell(config_file, mechanism_name)
                results.extend(cell0.run_all_protocols(simulators))

    return results


def compare_test_results(results, rtol=1e-7, atol=0.0, verbose=2):
    is_error = False

    remove_duplicate_log = set()
    for result_all_sim in results:

        # check meaningful comparison
        assert len(result_all_sim) == 2

        nrn_res = result_all_sim[0]
        corenrn_res = result_all_sim[1]

        # check meaningful comparison
        assert nrn_res.mechanism == corenrn_res.mechanism
        assert nrn_res.stimulus == corenrn_res.stimulus
        assert nrn_res.simulator == Simulators.NEURON
        assert corenrn_res.simulator == Simulators.CORENEURON

        key = nrn_res.mechanism + nrn_res.stimulus
        mse = ((nrn_res.trace - corenrn_res.trace) ** 2).mean()

        err = False
        try:
            np.testing.assert_allclose(nrn_res.trace, corenrn_res.trace, rtol, atol)
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
                    nrn_res.mechanism,
                    nrn_res.stimulus,
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
    colors = {Simulators.NEURON: "r", Simulators.CORENEURON: "b"}

    for result_all_sim in results:
        for result in result_all_sim:
            label = "{}, {}, {}".format(
                result.mechanism, result.stimulus, result.simulator.name
            )
            pplt.plot(
                result.tvec,
                result.trace,
                color=colors[result.simulator],
                label=(label, "")[label in remove_duplicate_log],
            )
            remove_duplicate_log.add(label)

    pplt.xlabel("t (msec)")
    pplt.legend()
    pplt.show()
