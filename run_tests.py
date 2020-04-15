# This is supposed to be called by run_tests.sh

from channel_validation_framework.cell import Cell
from channel_validation_framework.utils import find_first_of_in_file

import os

if __name__ == "__main__":

    CONFIG_FILE_PATH = "./configs/kv.in"
    mod_root = "mod"

    for subdir, dirs, files in os.walk(mod_root):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".mod") and filepath.find("custom") == -1:
                # TODO: this way of picking up the suffix could be dangerous
                f = open(filepath, "r")
                find_first_of_in_file(f, "NEURON")
                mechanism_name = find_first_of_in_file(f, "SUFFIX").split()[1]
                f.close()

                cell0 = Cell(CONFIG_FILE_PATH, mechanism_name)
                cell0.run_all_protocols()


quit()


# @pytest.mark.parametrize("res, tol", _run(tol))
# def test_mod(res, tol):
#     assert res.err < tol
