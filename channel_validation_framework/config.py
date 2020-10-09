"""
Module to parse Config
"""
import logging
import os
from enum import Enum, auto
from pathlib import Path

import yaml
import numpy as np

from .mod import Mod
from .utils import NameGen, NoAliasDumper


class ConfigParserError(Exception):
    pass


class Config(dict):
    """
    When in cvf_protocols there are multiple protocols
    and the mod file has multiple inputs we can create a
    table of Single Input (SI) possible scenarios.
    For example, imagine this table:

             v | ica | cai
    -----------------------
    wiggle |   |     |
    -----------------------
    ramp   |   |     |

    there is a different protocol for each table cell
    given that we restrict to single input protocols

    Protocol generator enumerates the most common setups
    we could want from this table
    """

    class ProtocolGenerator(Enum):
        SI_FULL = auto()
        SI_FIRST_INPUT = auto()
        SI_FIRST_PROTOCOL = auto()

    # Standard simulation scenarios
    class SimulationScenario(Enum):
        SINGLE_SEC = auto()  # one cell, one mechanism
        PRE_POST_SEC = auto()  # emitter, receiver

    # Section names in case config is generated
    section_names = {
        SimulationScenario.SINGLE_SEC: ["soma"],
        SimulationScenario.PRE_POST_SEC: ["pre", "post"],
    }

    # returns scenario and section names
    def simulation_scenario(self):

        mech_type, _ = self.mod.mechanism()

        if self.mod.is_net_receive():
            ss = self.SimulationScenario.PRE_POST_SEC
        else:
            ss = self.SimulationScenario.SINGLE_SEC

        return ss, self.section_names[ss]

    # Read the file and fill config
    def __init__(self, confpath, modpath, protocol_generator, print_config=False):
        self.protocol_generator = protocol_generator
        self.confpath = confpath
        self.mod = Mod(modpath)

        if os.path.isfile(self.confpath):
            self.update(self._read_from_yaml(confpath))

        elif os.path.isdir(self.confpath):
            self.confpath = os.path.join(
                self.confpath, Path(self.mod.modpath).stem + ".yaml"
            )
            if os.path.isfile(self.confpath):
                self.update(self._read_from_yaml(self.confpath))
            else:
                confdir = os.path.dirname(self.confpath)
                self._autogen(
                    self._read_from_yaml(os.path.join(confdir, "cvf_template.yaml")),
                    self._read_from_yaml(os.path.join(confdir, "cvf_protocols.yaml")),
                )

                logging.info(
                    "config object for <{}> successfully auto-generated".format(
                        self.mod.modpath
                    )
                )

        if print_config:
            self.dump_to_yaml()

    def _read_from_yaml(self, confpath):
        with open(confpath, "r") as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def dump_to_yaml(self, confpath=None):
        if not confpath:
            confpath = os.path.join(
                "config", Path(self.mod.modpath).stem + "_autogen.yaml"
            )

        with open(confpath, "w") as file:
            yaml.dump(dict(self), file, Dumper=NoAliasDumper)

    def __str__(self):
        return (
            "\nCONFIG FILE:\n --- \nconfpath: "
            + self.confpath
            + "\n\n"
            + yaml.dump(dict(self), Dumper=NoAliasDumper)
            + " --- \n"
        )

    def tstop(self, protocol):

        return next(
            max(
                [
                    (sum(var["t_steps"]) for var in sec_data["inputs"].values())
                    for sec_name, sec_data in self[protocol]["sections"].items()
                    if "inputs" in sec_data
                ]
            )
        )

    @staticmethod
    def _correct_trace(y, var_type):
        if var_type == "(mM)":
            return [0.00001 * (i > 0) * i for i in y]
        else:
            return y

    @staticmethod
    def _unpack_trace(y):
        out = []
        leading_y_ramp_idx = [idx for idx, x in enumerate(y) if isinstance(x, list)]
        if len(leading_y_ramp_idx):
            leading_y_ramp_idx = leading_y_ramp_idx[0]
            leading_y_ramp = y[leading_y_ramp_idx]
            y_run = y.copy()
            for y_step in np.arange(
                leading_y_ramp[0], leading_y_ramp[2], leading_y_ramp[1]
            ):
                y_run[leading_y_ramp_idx] = y_step.tolist()
                out.append(y_run.copy())
        else:
            out.append(y)

        return out

    @staticmethod
    def _unpack_protocols(protocols):
        out = {}

        name_gen = NameGen()

        for name, traces in protocols.items():
            t_steps = traces["t_steps"]
            y_steps = Config._unpack_trace(traces["y_steps"])
            if len(y_steps) == 1:
                out[name] = {"t_steps": t_steps, "y_steps": y_steps[0]}
            else:
                for trace in y_steps:
                    out[name_gen(name)] = {"t_steps": t_steps, "y_steps": trace}

        return out

    # fill the template with mod data

    def _autogen_inputs(self):
        std_input = ("v", {"unit": "(mV)"})
        # items in read that are not in write. If e*** the correct input is probably v
        inputs = {
            std_input[0]
            if "unit" in v and v["unit"] == std_input[1]["unit"]
            else k: std_input[1]
            if "unit" in v and v["unit"] == std_input[1]["unit"]
            else v
            for k, v in self.mod.get_useion_read().items()
            if (k not in self.mod.get_useion_write() and "value" not in v)
        }

        if not inputs:
            inputs[std_input[0]] = std_input[1]
        return inputs

    def _autogen_mechanisms(self, template):
        mech_type, mech_name = self.mod.mechanism()
        useion_read = self.mod.get_useion_read()

        # mechanisms
        mechanisms = {"type": mech_type}

        if useion_read.items():
            mech_data = {
                k: template["mechanisms"]["data"][v["unit"]]
                for k, v in useion_read.items()
                if "value" not in v
            }
            if mech_data:
                mechanisms["data"] = mech_data
        if self.mod._is_setRNG():
            mechanisms["rng"] = template["mechanisms"]["rng"]

        return {mech_name: mechanisms}

    def _autogen_record_traces(self):
        mech_type, mech_name = self.mod.mechanism()
        useion_write = self.mod.get_useion_write()

        # record traces
        record_traces = list(useion_write)
        nonspecific_currents = self.mod.get_nonspecific_current()
        if mech_type == "SUFFIX":
            nonspecific_currents = [i + "_" + mech_name for i in nonspecific_currents]
        record_traces.extend(nonspecific_currents)

        return record_traces

    def _autogen(self, template, protocols):

        inputs = self._autogen_inputs()
        unpacked_protocols = Config._unpack_protocols(protocols)
        simulation_scenario, section_names = self.simulation_scenario()

        mechanisms = self._autogen_mechanisms(template)
        data_global = template["global"]
        data = template["sections"]["data"]
        record_traces = self._autogen_record_traces()

        name_gen = NameGen()
        for input_var, input_data in inputs.items():
            for protocol_name, protocol_traces in unpacked_protocols.items():
                t_steps = protocol_traces["t_steps"]
                y_steps = Config._correct_trace(
                    protocol_traces["y_steps"], input_data["unit"]
                )
                input = {input_var: {"t_steps": t_steps, "y_steps": y_steps}}

                pname = name_gen(protocol_name)

                scenario = {}
                scenario["global"] = data_global
                if simulation_scenario == self.SimulationScenario.PRE_POST_SEC:
                    scenario["sections"] = {
                        section_names[0]: {"data": data, "inputs": input},
                        section_names[1]: {
                            "data": data,
                            "mechanisms": mechanisms,
                            "record_traces": record_traces,
                        },
                    }

                    # netcons
                    scenario["netcons"] = {
                        "nc": {
                            "source": {section_names[0]: "v"},
                            "target": section_names[1],
                            "data": template["netcons"]["data"],
                        }
                    }
                elif simulation_scenario == self.SimulationScenario.SINGLE_SEC:
                    scenario["sections"] = {
                        section_names[0]: {
                            "data": data,
                            "mechanisms": mechanisms,
                            "record_traces": record_traces,
                            "inputs": input,
                        }
                    }

                self[pname] = scenario

                if self.protocol_generator == self.ProtocolGenerator.SI_FIRST_PROTOCOL:
                    break
            if self.protocol_generator == self.ProtocolGenerator.SI_FIRST_INPUT:
                break
