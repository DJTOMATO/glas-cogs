from .pokefusion import PokeFusion


async def setup(bot):
    await bot.add_cog(PokeFusion())
