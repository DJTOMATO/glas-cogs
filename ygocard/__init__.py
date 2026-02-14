from .ygocard import YgoCard


async def setup(bot):
    await bot.add_cog(YgoCard(bot))
