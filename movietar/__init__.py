from .movietar import Movietar


async def setup(bot):
    await bot.add_cog(Movietar(bot))
