"""
Module to parse Mod files to auto-generate Config
"""

import yaml

from .utils import smart_merge


class ModParserError(Exception):
    pass


class Mod:

    supported_keywords = {
        "SUFFIX",
        "USEION",
        "GLOBAL",
        "RANGE",
        "POINT_PROCESS",
        "READ",
        "WRITE",
        "NONSPECIFIC_CURRENT",
    }

    def __str__(self):
        return "\n filepath: " + self.filepath + "\n\n" + yaml.dump(self.data)

    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}

        with open(self.filepath, "r") as file_iter:
            for line in file_iter:
                if line.startswith("NEURON"):
                    smart_merge(self.data, "NEURON", self._parse_section(file_iter))

                    break

    def _parse_section(self, file_iter):

        info = {}

        for line in file_iter:
            line = line.split(":", 1)[0].replace(",", " ").strip()
            if len(line) == 0 or line.startswith(":"):
                continue

            if line.startswith("}"):
                break

            parsed_line = line.split()
            if parsed_line[0] in self.supported_keywords:
                res = self._parse_line(parsed_line[1:])
                smart_merge(info, parsed_line[0], res)

        return info

    def _parse_line(self, parsed_line):

        if not any([x for x in parsed_line if x in self.supported_keywords]):
            return parsed_line

        info = {}
        key = ""

        for ii in parsed_line[1:]:
            if ii in self.supported_keywords:
                key = ii
            else:
                smart_merge(info, key, [ii])

        return info
