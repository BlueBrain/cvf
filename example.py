from channel_validation_framework.commands import *

r = run()  # additional_mod_folders="/home/katta/projects/neocortex/mod/v5_CVFsupported"
cvf_print(r)
compare(r)
plot(r)  # warning: this could create too many figures. In this case it raises an error
