from .weeed import WeeedBot
from redbot.core import data_manager
from shutil import rmtree

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot):
    cog = WeeedBot(bot)
    await bot.add_cog(cog)
