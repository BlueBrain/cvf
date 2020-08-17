"""
Module to parse Config
"""
import logging
import os

import numpy as np
import yaml

from .utils import fill_or_delete_dictkey


class ConfigParserError(Exception):
    pass


class Config(dict):
    # Read the file and fill config
    # I know there are some if-else. However, with this small number of sections (2)
    # it is ok IMO

    def __init__(self, filepath=None, mod=None):
        self.filepath = filepath
        self.mod = mod
        # self._data = {}

        if filepath is None and mod is None:
            raise ConfigParserError(
                "No config_file_path nor mod! I do not know how to build this cell!"
            )

        if filepath is None or not os.path.isfile(filepath):
            logging.info(
                'Config file not found. Automatic extrapolation from mod file "{}"'.format(
                    mod.filepath
                )
            )
            self._autogenerate()
            logging.info("SUCCESS!")
        else:
            if filepath.endswith(".in"):
                self._read_raw_in()
                self._purify_raw_in()
            elif filepath.endswith(".yaml"):
                self._read_from_yaml()

    def _autogenerate(self):
        # try template
        self.filepath = "config" + os.sep + "template.yaml"
        self._read_from_yaml()
        self._fill_template()

    # fill the template with mod data
    def _fill_template(self):
        # useion
        fill_or_delete_key = "WRITE"
        fill_or_delete_dictkey(
            self["channel"]["USEION"],
            fill_or_delete_key,
            self.mod["NEURON"].get("USEION", {}).get(fill_or_delete_key, {}),
        )

        fill_or_delete_key = "READ"
        fill_or_delete_dictkey(
            self["channel"]["USEION"],
            fill_or_delete_key,
            self.mod["NEURON"].get("USEION", {}).get(fill_or_delete_key, {}),
        )

        fill_or_delete_key = "NONSPECIFIC_CURRENT"
        fill_or_delete_dictkey(
            self["channel"],
            fill_or_delete_key,
            self.mod["NEURON"].get(fill_or_delete_key, {}),
        )

    def _read_from_yaml(self):
        with open(self.filepath, "r") as file:
            self.update(yaml.load(file, Loader=yaml.FullLoader))

    def _read_raw_in(self):
        with open(self.filepath, "r") as file_iter:
            for line in file_iter:
                parsed_line = line.strip().split()
                if len(parsed_line) == 0 or parsed_line[0].startswith("#"):
                    continue
                elif len(parsed_line) == 2:
                    section_data = self._parse_section(file_iter)
                    if parsed_line[0] == "Channel":
                        if isinstance(section_data, ConfigParserError):
                            raise ConfigParserError(
                                "Invalid data in Channel {}: {}".format(
                                    parsed_line[1], str(section_data)
                                )
                            )
                        self["channel"] = section_data

                    elif parsed_line[0] == "Stimulus":
                        if isinstance(section_data, ConfigParserError):
                            raise ConfigParserError(
                                "Invalid data in Stimulus {}: {}".format(
                                    parsed_line[1], str(section_data)
                                )
                            )
                        if "stimulus" in self:
                            self["stimulus"][parsed_line[1]] = section_data
                        else:
                            self["stimulus"] = {parsed_line[1]: section_data}

                    else:
                        logging.warning("Skipped unknown config section: {}", line)
                        self._skip_section(file_iter)
                else:
                    raise ConfigParserError("Malformed section: {}".format(line))

    # Rules for converting to std format
    def _purify_raw_in(self):

        # suffix
        try:
            self["channel"]["SUFFIX"] = self["channel"].pop("suffix")
        except KeyError:
            pass

        # useion
        try:
            read = {self["channel"]["revName"]: self["channel"]["revValue"]}
            write = [self["channel"]["current"]]
            self["channel"]["USEION"] = {"READ": read, "WRITE": write}

            del [
                self["channel"]["revName"],
                self["channel"]["revValue"],
                self["channel"]["current"],
            ]
        except KeyError:
            pass

        # stimulus
        try:
            for stimulus_name in self["stimulus"]:
                [t_steps, v_steps] = self._extract_steps_from_stimulus(stimulus_name)
                self["stimulus"][stimulus_name]["t_steps"] = t_steps
                self["stimulus"][stimulus_name]["v_steps"] = v_steps
        except KeyError:
            pass

    def dump_to_yaml(self, filepath=None):
        if filepath == None:
            filepath = os.path.splitext(self.filepath)[0] + ".yaml"

        with open(filepath, "w") as file:
            yaml.dump(self._data, file)

    def __str__(self):
        return "\n filepath: " + self.filepath + "\n\n" + yaml.dump(self)

    @staticmethod
    def _skip_section(file_iter):
        for line in file_iter:
            if line.strip().startswith("}"):
                break

    @staticmethod
    def _parse_section(file_iter):
        info = {}

        # skip {
        line = file_iter.readline()
        if line.find("{") != -1:
            pass
        else:
            return ConfigParserError("Expected: '{{', found: {}".format(line))

        for line in file_iter:
            line = line.strip()
            if not line or line[0] == "#":
                continue
            if line == "}":
                break
            if line == "{":
                return ConfigParserError("Section not closed")
            parts = line.split()
            if len(parts) != 2:
                return ConfigParserError(line)
            try:
                value = float(parts[1])
            except ValueError:
                try:
                    value = [float(item) for item in parts[1].split(":")]
                except ValueError:
                    value = parts[1]

            info[parts[0]] = value

        return info

    def _extract_steps_from_stimulus(self, stimulus_name):

        t = []
        v = []
        map0 = self["stimulus"][stimulus_name]

        # extract tsteps
        n = 1
        while "thold" + str(n) in map0.keys():
            t.append(map0["thold" + str(n)])
            n += 1

        # ramp particular case
        if "vhold" and "vmax" in map0.keys():
            vmin = map0["vhold"]
            vmax = map0["vmax"]
            v = np.linspace(vmin, vmax, len(t)).tolist()
            del map0["vhold"]
            del map0["vmax"]
        else:
            n = 1
            while "vhold" + str(n) in map0.keys():
                v.append(map0["vhold" + str(n)])
                n += 1

        delete_keys = [k for k, v in map0.items() if "hold" in k]
        for i in delete_keys:
            del map0[i]

        return t, v
