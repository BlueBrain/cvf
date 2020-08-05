"""
Module to parse Mod files to auto-generate Config
"""

import yaml

from .utils import smart_merge
import os


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
        "VALENCE",
        "NONSPECIFIC_CURRENT",
    }

    def __str__(self):
        return "\n filepath: " + self.filepath + "\n\n" + yaml.dump(self.data)

    def __init__(self, filepath):
        self.filepath = filepath
        self.data = {}

        with open(self.filepath, "r") as file_iter:
            for line in file_iter:
                line = self._purify_line(line)
                if not line:
                    continue

                if line.startswith("NEURON"):
                    smart_merge(self.data, "NEURON", self._parse_section(file_iter))

                    break

    def _purify_line(self, line):
        return line.split(":", 1)[0].replace(",", " ").strip()

    def _parse_section(self, file_iter):

        info = {}

        for line in file_iter:
            line = self._purify_line(line)
            if not line:
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
                try:
                    smart_merge(info, key, [float(ii)])
                except ValueError:
                    smart_merge(info, key, [ii])

        return info


def mod_crawler(modfolders, ff):
    if isinstance(modfolders, str):
        modfolders = [modfolders]
    for folder in modfolders:
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                filepath = subdir + os.sep + file
                if file.endswith(".mod"):
                    try:
                        m = Mod(filepath)
                    except Exception as e:
                        print(filepath)
                        print(e)
                        continue

                    if ff(m):
                        print(filepath)
                        print(m)
