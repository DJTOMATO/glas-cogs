import discord
from redbot.core.bot import Red

from .anime import Anime


async def setup(bot: Red):
    cog = Anime(bot)
    await discord.utils.maybe_coroutine(bot.add_cog, cog)
