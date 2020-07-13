"""
Module to parse Config
"""
import logging
import yaml
from enum import Enum


class ModParserError(Exception):
    pass


class Mod:

    data = {}

    def __init__(self, filepath):
        self.filepath = filepath

        with open(self.filepath, "r") as file_iter:
            is_neuron_section = False
            for line in file_iter:
                parsed_line = line.strip().replace(",", "").split()
                if len(parsed_line) == 0 or parsed_line[0].startswith(":"):
                    continue

                if parsed_line[0] == "NEURON":
                    is_neuron_section = True
                if is_neuron_section:
                    if parsed_line[0] == "SUFFIX":
                        self.data["SUFFIX"] = parsed_line[1]
                    elif parsed_line[0] == "USEION":
                        self.data["USEION"] = self._parse_useion(parsed_line)
                    if parsed_line[0] == "}":
                        break

    def __str__(self):
        return "\n filepath: " + self.filepath + "\n\n" + yaml.dump(self.data)

    @staticmethod
    def _parse_useion(splitted_line):

        controller = Enum("Controller", "OFF READ WRITE")

        info = {"READ": [], "WRITE": []}

        c = controller.OFF
        for ii in splitted_line:
            if ii == "READ":
                c = controller.READ
            elif ii == "WRITE":
                c = controller.WRITE
            elif c is controller.READ:
                info["READ"].append(ii)
            elif c is controller.WRITE:
                info["WRITE"].append(ii)

        return info
