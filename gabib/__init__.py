from .gabib import Gabib

async def setup(bot):
    await bot.add_cog(Gabib(bot))
