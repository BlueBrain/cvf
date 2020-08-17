import glob
import os
import shutil
from enum import IntEnum, auto

import numpy as np


# do not import from neuron


class Simulators(IntEnum):
    NEURON = auto()
    CORENEURON_NMODLSYMPY_ANALYTIC = auto()
    CORENEURON_NMODLSYMPY_PADE = auto()
    CORENEURON_NMODLSYMPY_CSE = auto()
    CORENEURON_NMODLSYMPY_CONDUCTANCEC = auto()


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


def std_trace_name(name):
    return "_ref_{}".format(name)


def record_trace(name, from_obj, traces, is_std=True):
    from neuron import h

    traces[name] = h.Vector()
    if is_std:
        traces[name].record(getattr(from_obj, std_trace_name(name)))
    else:
        traces[name].record(getattr(from_obj, name))


def convert_and_copy_traces(traces, out, prefix=""):
    for key, val in traces.items():
        out[prefix + key] = np.array(val).copy()


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


def get_V_steps(v):
    out = []
    leading_v_ramp_idx = [idx for idx, x in enumerate(v) if isinstance(x, list)]
    if len(leading_v_ramp_idx):
        leading_v_ramp_idx = leading_v_ramp_idx[0]
        leading_v_ramp = v[leading_v_ramp_idx]
        v_run = v.copy()
        for v_step in np.arange(
            leading_v_ramp[0], leading_v_ramp[2], leading_v_ramp[1]
        ):
            v_run[leading_v_ramp_idx] = v_step
            out.append(v_run.copy())
    else:
        out.append(v)

    return out


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


def copy_to_working_dir(srcs, dst, ext=None):
    copy_log = set()
    for src in srcs:
        if os.path.exists(src):
            try:
                if os.path.isfile(src) and (
                    ext is None or os.path.splitext(src)[1] == ext
                ):
                    copy_log.add(shutil.copyfile(src, dst))
                elif os.path.isdir(src):
                    for subdir, dirs, files in os.walk(src):
                        for file in files:
                            if ext is None or os.path.splitext(file)[1] == ext:
                                copy_log.add(shutil.copy(subdir + os.sep + file, dst))
            except OSError:
                pass

    return copy_log
