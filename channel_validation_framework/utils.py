import os
import shutil
from enum import Enum, auto

import numpy as np

import glob


# do not import from neuron


class Simulators(Enum):
    NEURON = auto()
    CORENEURON_NMODLSYMPY_ANALYTIC = auto()
    CORENEURON_NMODLSYMPY_PADE = auto()
    CORENEURON_NMODLSYMPY_CSE = auto()
    CORENEURON_NMODLSYMPY_CONDUCTANCEC = auto()


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

    tvec = np.linspace(dt, len(vvec) * dt, len(vvec))

    return tvec, vvec


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
