from .valentine import Valentine

__red_end_user_data_statement__ = (
    "This cog stores user ids for counting amount of letters received only."
)


async def setup(bot):
    await bot.add_cog(Valentine())
