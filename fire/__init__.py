from .fire import FireCog


async def setup(bot):
    await bot.add_cog(FireCog())
