from channel_validation_framework import commands

# conf = get_conf()
# for i in conf:
#     print(i)
#     i.dump_to_yaml()

r = commands.run(print_config=True)
commands.cvf_print(r)
commands.compare(r, is_fail_on_error=False)
commands.plot(
    r
)  # warning: this could create too many figures. In this case it raises an error
