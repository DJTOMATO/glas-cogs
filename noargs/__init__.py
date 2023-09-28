from .noargs import NoArgs

async def setup(bot):
    cog = NoArgs(bot)
    await bot.add_cog(cog)
