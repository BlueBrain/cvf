"""
Module to parse Config
"""
import logging
import os

import numpy as np
import yaml


class ConfigParserError(Exception):
    pass


class Config:
    # Read the file and fill config
    # I know there are some if-else. However, with this small number of sections (2)
    # it is ok IMO

    data = {}

    def __init__(self, filepath=None, mod=None):
        self.filepath = filepath

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
            self._read_useion_template(mod)
            logging.info("SUCCESS!")
        else:
            if filepath.endswith(".in"):
                self._read_from_in()
            elif filepath.endswith(".yaml"):
                self._read_from_yaml()

    def _read_useion_template(self, mod):
        # try useion template
        self.filepath = "config" + os.sep + "template_useion.yaml"
        self._read_from_yaml()

        # fill the template with mod data
        try:
            self.data["channel"]["suffix"] = mod.data["NEURON"]["SUFFIX"]
            self.data["channel"]["current"] = mod.data["NEURON"]["USEION"]["WRITE"][0]
            self.data["channel"]["revName"] = mod.data["NEURON"]["USEION"]["READ"][0]
        except IndexError or KeyError:
            raise ConfigParserError(
                'Automatic extrapolation from mod file "{}" not supported'.format(
                    mod.filepath
                )
            )

    def _read_from_yaml(self):
        with open(self.filepath, "r") as file:
            self.data = yaml.load(file, Loader=yaml.FullLoader)

    def _read_from_in(self):
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
                        self.data["channel"] = section_data

                    elif parsed_line[0] == "Stimulus":
                        if isinstance(section_data, ConfigParserError):
                            raise ConfigParserError(
                                "Invalid data in Stimulus {}: {}".format(
                                    parsed_line[1], str(section_data)
                                )
                            )
                        if "stimulus" in self.data:
                            self.data["stimulus"][parsed_line[1]] = section_data
                        else:
                            self.data["stimulus"] = {parsed_line[1]: section_data}

                    else:
                        logging.warning("Skipped unknown config section: {}", line)
                        self._skip_section(file_iter)
                else:
                    raise ConfigParserError("Malformed section: {}".format(line))

    def dump_to_yaml(self, filepath=None):
        if filepath == None:
            filepath = os.path.splitext(self.filepath)[0] + ".yaml"

        with open(filepath, "w") as file:
            yaml.dump(self.data, file)

    def __str__(self):
        return "\n filepath: " + self.filepath + "\n\n" + yaml.dump(self.data)

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

    def extract_steps_from_stimulus(self, stimulus_name):
        t = []
        v = []
        map0 = self.data["stimulus"][stimulus_name]

        # extract tsteps
        n = 1
        while "thold" + str(n) in map0.keys():
            t.append(map0["thold" + str(n)])
            n += 1

        # ramp particular case
        if "vhold" and "vmax" in map0.keys():
            vmin = map0["vhold"]
            vmax = map0["vmax"]
            v = np.linspace(vmin, vmax, len(t))
        else:
            n = 1
            while "vhold" + str(n) in map0.keys():
                v.append(map0["vhold" + str(n)])
                n += 1

        return t, v
