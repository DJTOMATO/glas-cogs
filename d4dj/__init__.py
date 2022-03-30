import aiohttp

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from .utils import summon_esora
from .utils import summon_noa


class D4DJ(commands.Cog):
    """
    Le D4DJ Cog.

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
    async def d4dj(self, ctx):
        """Generates D4DJ Image."""
        pass

    @d4dj.command(aliases=["esoraa"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def esora(self, ctx):
        """Generates a random Esora image."""

        await summon_esora(self, ctx, "image")

    @d4dj.command(aliases=["Noaa"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def noa(self, ctx):
        """Generates a random Noa image."""

        await summon_noa(self, ctx, "image")


def setup(bot):
    bot.add_cog(D4DJ(bot))


__red_end_user_data_statement__ = "This cog does not store any end user data."
