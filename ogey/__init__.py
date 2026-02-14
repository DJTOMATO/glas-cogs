import aiohttp

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from .utils import summon_ogey


class Ogey(commands.Cog):
    """
    Le ogey Cog.

    All this code was originally made by Kuro, he's the king .

    """

    def __init__(self, bot):
        self.bot = bot

    __author__ = humanize_list(["Kuro", "Glas"])
    __version__ = "1.1.3"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return (
            f"{pre_processed}\n\n"
            f"`Cog Author  :` {self.__author__}\n"
            f"`Cog Version :` {self.__version__}"
        )

    def cog_unload(self):
        pass

    @commands.group()
    async def ogey(self, ctx):
        """Generates Ogey Image."""
        pass

    @ogey.command(aliases=["images"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def image(self, ctx):
        """Generates a random Ogey image."""

        await summon_ogey(self, ctx, "image")

    @ogey.command(aliases=["gifs"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def gif(self, ctx):
        """Generates a random Ogey GIF."""

        await summon_ogey(self, ctx, "gif")


__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


async def setup(bot):
    await bot.add_cog(Ogey(bot))
