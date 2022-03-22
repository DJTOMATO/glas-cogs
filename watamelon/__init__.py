import aiohttp

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from .utils import summon_watamelon
 """
    All this code was originally made by Kuro, he's the king .
    """

class Watamelon(commands.Cog):
    """
    Le Watamelon Cog.
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
    async def watamelon(self, ctx):
        """Generates Watamelon Image."""
        pass

    @watamelon.command(aliases=["images"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def image(self, ctx):
        """Generates a random Watamelon image."""

        await summon_watamelon(self, ctx, "image")

    @watamelon.command(aliases=["gifs"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def gif(self, ctx):
        """Generates a random Watamelon GIF."""

        await summon_watamelon(self, ctx, "gif")

    @watamelon.command(aliases=["memes"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme(self, ctx):
        """Generates a random Watamelon meme."""

        await summon_watamelon(self, ctx, "meme")


def setup(bot):
    bot.add_cog(Watamelon(bot))


__red_end_user_data_statement__ = "This cog does not store any end user data."
