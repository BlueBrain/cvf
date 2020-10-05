import argparse
import glob
import logging
import os
import subprocess
import sys
from itertools import cycle
from pathlib import Path

import numpy as np
import yaml

from . import utils
from .config import Config
from .run_result import RunResult, Result
from .simulation import Simulation

try:
    import matplotlib.pyplot as pplt
    from matplotlib import colors
except ImportError:
    logging.warning("Matplotlib could no be found. Proceeding without plots...")


# do not import from neuron


class CompareTestResultsError(Exception):
    pass


def cvf_stdrun():

    parser = argparse.ArgumentParser(
        description="Channel-validation-framework standard test run"
    )

    parser.add_argument(
        "-c",
        "--config",
        default="config",
        type=str,
        help="folder in where there are the confic files (i.e. cvf_template.yaml)",
    )
    parser.add_argument(
        "-m",
        "--modignore",
        default="modignore.yaml",
        type=str,
        help="location of the modignore.yaml file",
    )
    parser.add_argument(
        "additional_mod_folders",
        nargs="*",
        default=[],
        type=str,
        help="additional mod folders that are to be processed (non-recursive)",
    )

    args = parser.parse_args()

    results = run(
        configpath=args.config,
        additional_mod_folders=args.additional_mod_folders,
        modignorepath=args.modignore,
    )

    compare(results)

    return 0


def run(
    configpath="config",
    config_protocol_generator=Config.ProtocolGenerator.SI_FIRST_PROTOCOL,
    additional_mod_folders=[],
    modignorepath="modignore.yaml",
    simulators={
        utils.Simulators.NEURON,
        utils.Simulators.CORENEURON_NMODLSYMPY_ANALYTIC,
    },
    base_working_dir="tmp",
    print_config=False,
):
    logging.getLogger().setLevel(logging.INFO)

    # clear the state
    utils.silent_remove([base_working_dir + "_*"])

    configpath = os.path.abspath(configpath)

    modignore = {}
    if modignorepath:
        modignorepath = os.path.abspath(modignorepath)
        with open(modignorepath, "r") as file:
            modignore = yaml.load(file, Loader=yaml.FullLoader)

    out = {}
    for simulator in simulators:

        # prepare working dir
        working_dir = "{}_{}".format(base_working_dir, simulator.name)
        copy_to_working_dir_log = utils.init_working_dir(
            additional_mod_folders, working_dir, modignore["nocompile"]
        )

        subprocess.run(["nrnivmodl", "mod"], cwd=working_dir)
        if simulator is not utils.Simulators.NEURON:
            # TODO: add support for compiling with different sympy options
            subprocess.run(["nrnivmodl-core", "mod"], cwd=working_dir)

        out[simulator] = _simulator_run(
            simulator,
            configpath,
            config_protocol_generator,
            modignore["notest"],
            working_dir,
            print_config,
        )

        out[simulator].extend(
            RunResult(
                result=Result.SKIP,
                modfile=Path(name).stem,
                result_msg=modignore["nocompile"][Path(name).stem],
            )
            for name, is_copied in copy_to_working_dir_log.items()
            if not is_copied
        )

    return out


def _simulator_run(
    simulator,
    configpath,
    config_protocol_generator,
    modignore,
    working_dir,
    print_config,
):
    results = []
    modpaths = glob.glob(os.path.join(working_dir, "mod", "*.mod"))
    for modpath in modpaths:
        name = Path(modpath).stem
        if name not in modignore:
            config = Config(
                configpath, modpath, config_protocol_generator, print_config
            )
            sim = Simulation(
                working_dir,
                config,
            )
            results.extend(sim.run_all_protocols(simulator))
        else:
            results.append(
                RunResult(
                    result=Result.SKIP,
                    modfile=name,
                    result_msg=modignore[name],
                )
            )
    return results


def compare(
    results,
    main_simulator=utils.Simulators.NEURON,
    rtol=1e-5,
    atol=1e-8,
    verbose=2,
    is_fail_on_error=True,
):
    logging.getLogger().setLevel(logging.INFO)
    is_error = False

    remove_duplicate_log = set()
    for simulator, tests in sorted(results.items()):
        if simulator == main_simulator:
            continue

        logging.info("Compare {} with {}".format(main_simulator.name, simulator.name))

        for base_res, test_res in zip(results[main_simulator], tests):

            if test_res.result is Result.SUCCESS:
                key = base_res.modfile + base_res.protocol + simulator.name
                test_res.mse = [
                    utils.compute_mse(base_trace, test_res.traces[trace_name])
                    for trace_name, base_trace in base_res.traces.items()
                ]

                try:
                    for trace_name, base_trace in base_res.traces.items():
                        test_trace = test_res.traces[trace_name]
                        np.testing.assert_allclose(base_trace, test_trace, rtol, atol)
                except AssertionError as e:
                    test_res.result = Result.FAIL
                    test_res.result_msg = str(e)
                    is_error = True

            if verbose == 3 or (
                verbose == 2
                and (
                    test_res.result is not Result.SUCCESS
                    or key not in remove_duplicate_log
                )
            ):
                print(test_res)

            if test_res.result is Result.SUCCESS:
                remove_duplicate_log.add(key)

    if is_error and is_fail_on_error:
        raise CompareTestResultsError("Some tests failed")
    elif verbose == 1:
        logging.info("SUCCESS!")


def plot(results):
    logging.getLogger().setLevel(logging.INFO)

    def plot_switcher(ifig, t, v, col, label, is_spiketrain, is_log=False):
        if len(v) == 0:
            return

        pplt.figure(ifig)
        if is_spiketrain:
            pplt.stem(
                v, [1] * len(v), linefmt=col, label=label, use_line_collection=True
            )
        elif is_log:
            pplt.plot(
                t,
                np.log10(abs(v)),
                color=col,
                label=label,
            )
        else:
            pplt.plot(
                t,
                v,
                color=col,
                label=label,
            )

    remove_duplicate_log = set()

    colit = cycle(dict(colors.BASE_COLORS))

    i_fig = 1
    for (simulator, tests), col in zip(
        sorted(results.items()), dict(colors.BASE_COLORS)
    ):
        if len(results) > 1:
            col = next(colit)
        for test in tests:
            if test.result is not Result.SUCCESS:
                continue

            for trace_name, trace_vec in test.traces.items():

                if len(results) == 1:
                    col = next(colit)

                is_spiketrain = "netcon" in trace_name

                label = "{}, {}, {}, {}".format(
                    test.modfile, test.protocol, test.simulator.name, trace_name
                )

                no_double_label = (label, "")[label in remove_duplicate_log]
                remove_duplicate_log.add(label)

                plot_switcher(
                    0, test.tvec, trace_vec, col, no_double_label, is_spiketrain
                )

                plot_switcher(
                    1,
                    test.tvec,
                    trace_vec,
                    col,
                    no_double_label,
                    is_spiketrain,
                    is_log=True,
                )

                i_fig += 1
                if i_fig > 20:
                    logging.error("Too many figures! I strike!")
                    return

                plot_switcher(i_fig, test.tvec, trace_vec, col, label, is_spiketrain)

        pplt.figure(0)
        pplt.title("cumulative")
        pplt.figure(1)
        pplt.title("cumulative")
        pplt.ylabel("log10(|y|)")

        for i in range(0, i_fig + 1):
            pplt.figure(i)

            pplt.xlabel("t (msec)")
            pplt.legend()

    pplt.show()


def get_conf(
    configpath="config",
    additional_mod_folders=[],
    working_dir="tmp",
    protocol_generator=Config.ProtocolGenerator.SI_FIRST_PROTOCOL,
):

    utils.init_working_dir(additional_mod_folders, working_dir)
    modpaths = glob.glob(os.path.join(working_dir, "mod", "*.mod"))

    conf = []
    for modpath in modpaths:
        if modpath.find("cvf") == -1:
            conf.append(Config(configpath, modpath, protocol_generator))

    return conf


def cvf_print(results):
    print(yaml.dump(utils.yamlfy(results)))
