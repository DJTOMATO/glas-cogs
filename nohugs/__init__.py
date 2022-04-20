# Please note that cog load order is not guaranteed, so it's not guaranteed to work every time, even thought my initial tests and reboots seemed to work. Just keep this in mind

def setup(bot):
    cmds = ["hug"]
    for cmd_name in cmds:
        old_cmd = bot.get_command(cmd_name)
        if old_cmd:
            bot.remove_command(old_cmd.name)