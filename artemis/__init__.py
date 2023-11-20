from .artemis import Artemis

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot):
    cog = Artemis(bot)
    await cog.initialize()  # Await the initialize method
    await bot.add_cog(cog)
