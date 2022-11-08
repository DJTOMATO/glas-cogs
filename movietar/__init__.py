from .movietar import Movietar


def setup(bot):
    bot.add_cog(Movietar(bot))
