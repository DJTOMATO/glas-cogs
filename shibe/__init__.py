from .shibe import Shibe


async def setup(bot):
    await bot.add_cog(Shibe(bot))