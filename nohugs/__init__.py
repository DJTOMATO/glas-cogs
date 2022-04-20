def setup(bot):
    cmds = ["hug"]
    for cmd_name in cmds:
        old_cmd = bot.get_command(cmd_name)
        if old_cmd:
            bot.remove_command(old_cmd.name)