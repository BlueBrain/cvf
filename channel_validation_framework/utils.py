import glob
import logging
import os
import shutil
from enum import IntEnum, auto
from pathlib import Path

import numpy as np


# do not import from neuron


class Simulators(IntEnum):
    NEURON = auto()
    CORENEURON_NMODLSYMPY_ANALYTIC = auto()
    CORENEURON_NMODLSYMPY_PADE = auto()
    CORENEURON_NMODLSYMPY_CSE = auto()
    CORENEURON_NMODLSYMPY_CONDUCTANCEC = auto()


class NameGen:
    def __init__(self):
        self.stor = {}

    def __call__(self, name):
        name = name.split("_")[0]
        if name not in self.stor:
            self.stor[name] = 1
            return name
        else:
            self.stor[name] += 1
            return "{}_{}".format(name, self.stor[name] - 1)


def nparray_yamlfy(vec):
    with np.printoptions(precision=3):
        return {"len": len(vec), "array": vec.__str__()}


def yamlfy(obj):

    primitive_types = (float, str, int)
    if isinstance(obj, primitive_types):
        return obj

    if isinstance(obj, Simulators):
        return obj.name

    if hasattr(obj, "yamlfy"):
        return obj.yamlfy()

    if isinstance(obj, list):
        return list(map(yamlfy, obj))

    if isinstance(obj, dict):
        return {
            (k, k.name)[isinstance(k, Simulators)]: yamlfy(v) for k, v in obj.items()
        }

    attributes = [i for i in dir(obj) if not i.startswith("__")]
    out = {}
    for i in attributes:
        val = getattr(obj, i)
        out[i] = yamlfy(val)
    return out


def init_working_dir(additional_mod_folders, working_dir, modignore={}):

    if isinstance(additional_mod_folders, str):
        additional_mod_folders = [additional_mod_folders]

    silent_remove([working_dir])
    os.makedirs(os.path.join(working_dir, "mod"))

    # we add the custom cvf mod files
    if not additional_mod_folders:
        additional_mod_folders.append(os.path.join("mod", "local"))

    additional_mod_folders.append(os.path.join("mod", "cvf"))

    copy_to_working_dir_log = copy_to_working_dir(
        additional_mod_folders, os.path.join(working_dir, "mod"), ".mod", modignore
    )

    logging.info(
        "Copied files in '%s': \n --- \n%s%s",
        working_dir,
        "\n".join([k for k, v in copy_to_working_dir_log.items() if v]),
        "\n --- \n",
    )
    logging.info(
        "Ignored files in '%s': \n --- \n%s%s",
        working_dir,
        "\n".join([k for k, v in copy_to_working_dir_log.items() if not v]),
        "\n --- \n",
    )

    return copy_to_working_dir_log


def std_trace_name(name):
    return "_ref_{}".format(name)


def set_data(d, target):
    if "data" in d:
        for k, v in d["data"].items():
            logging.info("  - {}:{}".format(k, v))
            try:
                setattr(target, k, v)
            except TypeError:
                getattr(target, k)[0] = v


def convert_and_copy_traces(traces, out, prefix=""):
    for key, val in traces.items():
        if len(val):
            out["{}_{}".format(prefix, key)] = np.array(val).copy()


def silent_remove(dirs):
    for dir in dirs:
        filenames = glob.glob(dir)
        for filename in filenames:
            if os.path.exists(filename):
                try:
                    if os.path.isfile(filename):
                        os.remove(filename)
                    else:
                        shutil.rmtree(filename)
                except OSError:
                    pass


def get_step_wave_form(t, v, dt):
    vvec = []
    for t, v in zip(t, v):
        vvec.extend([v] * int(t / dt))

    tvec = np.linspace(0, (len(vvec) - 1) * dt, len(vvec))

    return tvec, vvec


def float2short_str(val):
    if isinstance(val, float) and not np.isnan(val) and not np.isinf(val):
        if not val:
            return "0.0"
        else:
            return "~1.e{}".format(int(np.log10(val)))
    else:
        return str(val)


def fill_or_delete_dictkey(dic, key, key_list):
    if not key_list:
        dic.pop(key, None)
    elif key in dic:
        dic[key] = dict(zip(key_list, [dic[key]] * len(key_list)))
    else:
        dic[key] = key_list


def normalize(mat, normalize_with_min):
    val = (min(mat), max(mat))[normalize_with_min]
    if val:
        mat /= val
    return mat


def smart_merge(map, key, section):
    if key not in map:
        map[key] = section
    elif isinstance(map[key], list):
        if isinstance(map[key], list):
            map[key].extend(section)
        else:
            map[key].append(section)
    elif isinstance(map[key], dict):
        if isinstance(map[key], dict):
            for k, v in section.items():
                smart_merge(map[key], k, v)
        else:
            smart_merge(map[key], "", section)


def compute_mse(a, b):

    if not len(a) + len(b):
        return 0.0

    if len(a) != len(b):
        return float("Inf")

    return ((a - b) ** 2).mean()


def find_first_of_in_file(file, keyword):
    for line in file:
        if line.strip().startswith(keyword):
            return line


def copy_to_working_dir(srcs, dst, ext="", ignoreset={}):
    copy_log = {}

    for src in srcs:

        filepaths = Path(src).glob("*" + ext)

        for filepath in filepaths:

            name = Path(filepath).stem

            is_copied = name.startswith("cvf_") or name not in ignoreset

            if is_copied:
                shutil.copyfile(filepath, os.path.join(dst, name + ext))

            copy_log[str(filepath)] = is_copied

    return copy_log


# used only for development and debugging
#
# I get the attributes of an h object (even if they try to hide them)
def print_ref_attributes(s):
    from neuron import h

    print("--- ATTRIBUTES ---")
    for i in dir(h):
        try:
            a = getattr(h, i)
        except TypeError:

            try:
                print("Attribute: " + i + " - " + getattr(s, "_ref_" + i).__str__())
            except AttributeError:
                pass
    print("--- ATTRIBUTES ---")
