from channel_validation_framework import commands

r = commands.run(print_config=False, clear_working_dir=True)
commands.cvf_print(r)
commands.compare(r, is_fail_on_error=False)
commands.plot(r)
