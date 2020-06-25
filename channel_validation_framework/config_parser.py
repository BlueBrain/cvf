"""
Module to parse Configs
"""
import logging

import numpy as np


class ConfigParserError(Exception):
    pass


class Config:

    stimulus = {}

    # Read the file and fill config
    # I know there are some if-else. However, with this small number of sections (2)
    # it is ok IMO
    def __init__(self, filepath):
        with open(filepath, "r") as file_iter:
            for line in file_iter:
                parsed_line = line.strip().split()
                if len(parsed_line) == 0 or parsed_line[0].startswith("#"):
                    continue
                elif len(parsed_line) == 2:

                    if parsed_line[0] == "Channel":
                        self.channel = parsed_line[1]
                        section_data = self._parse_section(file_iter)
                        if isinstance(section_data, ConfigParserError):
                            raise ConfigParserError(
                                "Invalid data in Channel {}: {}".format(
                                    parsed_line[1], str(section_data)
                                )
                            )
                        self.channel_data = section_data

                    elif parsed_line[0] == "Stimulus":
                        section_data = self._parse_section(file_iter)
                        if isinstance(section_data, ConfigParserError):
                            raise ConfigParserError(
                                "Invalid data in Stimulus {}: {}".format(
                                    parsed_line[1], str(section_data)
                                )
                            )
                        self.stimulus[parsed_line[1]] = section_data

                    else:
                        logging.warning("Skipped unknown config section: {}", line)
                        self._skip_section(file_iter)
                else:
                    raise ConfigParserError("Malformed section: {}".format(line))

    def __str__(self):
        return "\n".join(self.__dict__)

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
        map0 = self.stimulus[stimulus_name]

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
