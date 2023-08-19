from .sekai import Sekai


async def setup(bot):
    await bot.add_cog(Sekai(bot))
