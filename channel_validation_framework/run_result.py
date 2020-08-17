from recordtype import recordtype

from .utils import nparray_yamlfy


class RunResult(
    recordtype(
        "RunResult",
        [
            "mechanism",
            "stimulus",
            "simulator",
            "t_steps",
            "v_steps",
            ("tvec", []),
            ("traces", {}),
        ],
        default="",
    )
):
    def yamlfy(self):
        return {
            "mechanism": self.mechanism,
            "stimulus": self.stimulus,
            "tvec": nparray_yamlfy(self.t_steps),
            "vvec": nparray_yamlfy(self.v_steps),
            "traces": {k: nparray_yamlfy(v) for k, v in self.traces.items()},
        }
