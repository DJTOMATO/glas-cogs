import aiohttp

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from .utils import summon_don


class Don(commands.Cog):
    """
    Le Don Cog.

    All this code was originally made by Kuro, he's the king .

    """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    __author__ = humanize_list(["Kuro"])
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
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def don(self, ctx):
        """Generates Don Image."""
        pass

    @don.command(aliases=["images"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def image(self, ctx):
        """Generates a random Don image."""

        await summon_don(self, ctx, "image")

    @don.command(aliases=["gifs"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def gif(self, ctx):
        """Generates a random Don GIF."""

        await summon_don(self, ctx, "gif")


def setup(bot):
    bot.add_cog(Don(bot))


__red_end_user_data_statement__ = "This cog does not store any end user data."
