from enum import Enum, auto

from recordtype import recordtype
from termcolor import colored

from .utils import nparray_yamlfy, float2short_str


class Result(Enum):
    SUCCESS = auto()
    SKIP = auto()
    FAIL = auto()

    def __str__(self):
        col = {Result.SUCCESS: "green", Result.SKIP: "yellow", Result.FAIL: "red"}
        return colored(self.name, col[self])


class RunResult(
    recordtype(
        "RunResult",
        [
            ("result", Result.SUCCESS),
            "result_msg",
            "modfile",
            "protocol",
            "simulator",
            ("tvec", []),
            ("traces", {}),
            ("mse", [-1.0]),
        ],
        default="",
    )
):
    def yamlfy(self):
        return {
            "result": self.result,
            "result_msg": self.result_msg,
            "modfile": self.modfile,
            "protocol": self.protocol,
            "traces": {k: nparray_yamlfy(v) for k, v in self.traces.items()},
            "mse": nparray_yamlfy(self.mse),
        }

    def __str__(self):
        out = "CVF - {} - {}".format(self.result, self.modfile)
        if self.result == Result.SUCCESS:
            out += ", {}, max mse={}\n              - Traces: ".format(
                self.protocol, max(self.mse)
            ) + ", ".join(
                [
                    ": ".join(
                        map(
                            float2short_str,
                            i,
                        )
                    )
                    for i in zip(self.traces, self.mse)
                ]
            )
        elif self.result == Result.SKIP:
            out += ": {}".format(self.result_msg)
        else:
            out += "\n{}".format(self.result_msg)

        return out
