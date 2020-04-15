import numpy as np
from neuron import h


def get_step_wave_form(t, v):
    vvec = []
    for t, v in zip(t, v):
        vvec.extend([v] * int(t / h.dt))

    tvec = np.linspace(h.dt, len(vvec) * h.dt, len(vvec))

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


def find_first_of_in_file(file, keyword):
    for line in file:
        if line.strip().startswith(keyword):
            return line
