import logging
import os
import subprocess
import sys

import numpy as np
from termcolor import colored

from .config_parser import Config
from .utils import Simulators, silent_remove, copy_to_working_dir

try:
    import matplotlib.pyplot as pplt
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


def run_tests(
    config_file=None,
    additional_mod_folders=[],
    simulators=[Simulators.NEURON, Simulators.CORENEURON],
    working_dir="mod/tmp",
):
    # we want to print the info
    logging.getLogger().setLevel(logging.INFO)

    # clean the state
    silent_remove(["enginemech.o", "nrnivmech_install.sh", "x86_64", working_dir])
    os.mkdir(working_dir)

    # we add the custom cvf mod files
    additional_mod_folders.append("mod/cvf")
    additional_mod_folders.append("mod/local")
    copy_to_working_dir_log = copy_to_working_dir(
        additional_mod_folders, working_dir, ".mod"
    )
    logging.info(
        "The following files were copied in '%s': \n%s",
        working_dir,
        "".join(copy_to_working_dir_log),
    )

    # call the compilers
    subprocess.call(["nrnivmodl", working_dir])
    subprocess.call(["nrnivmodl-core", working_dir])

    # Import neuron after nrnivmodl* so that libraries are not loaded twice/not loaded
    from .cell import Cell

    results = []
    for subdir, dirs, files in os.walk(working_dir):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".mod") and filepath.find("cvf") == -1:
                try:
                    cell0 = Cell(filepath, config_file)
                except Exception as e:
                    results.append(e)
                    continue

                results.extend(cell0.run_all_protocols(simulators))

    return results


def compare_test_results(results, rtol=1e-7, atol=0.0, verbose=2):
    is_error = False

    remove_duplicate_log = set()
    for result_all_sim in results:

        # avoid mechanisms that are not supported
        if isinstance(result_all_sim, Exception):
            print("CVF - {}, {}".format(colored("FAIL", "red"), str(result_all_sim)))
            is_error = True
            continue

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
