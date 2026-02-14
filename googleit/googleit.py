import discord
import random
from redbot.core import commands, Config
from redbot.core.utils import chat_formatting
import urllib.parse


class GoogleIt(commands.Cog):
    """
    A cog to provide "Let Me Google That For You" links.
    """

    IMAGES = [
        "https://media.tenor.com/KhQvEDtumlUAAAAC/here-it-is-americas-got-talent.gif",
        "https://media.tenor.com/bWRm7AHxOwUAAAAd/you-see-jabrils.gif",
        "https://media.tenor.com/70Jj39J1vrAAAAAC/give.gif",
        "https://media.tenor.com/4FK8LHl8w4EAAAAC/come-to-me-dr-evil.gif",
        "https://media.tenor.com/fjDNU3SrgCAAAAAC/loeya-here.gif",
    ]

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=246813579, force_registration=True
        )
        self.config.register_global(lmgtfy_endpoint="https://cog-creators.github.io")

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    async def googleit(self, ctx: commands.Context, *, query: str = None):
        """
        Google it!

        To search: [p]googleit <your search query>
        To set endpoint: [p]googleit setendpoint <url>
        To show endpoint: [p]googleit showendpoint
        """

        if ctx.invoked_subcommand is None:
            if not query:
                await ctx.send_help(ctx.command)
                return

            search_string = query.strip()
            if not search_string:
                await ctx.send_help(ctx.command)
                return
            await self._search(ctx, search_string)

    async def _search(self, ctx, search_string):


        encoded_search_string = urllib.parse.quote(search_string)
        current_endpoint = await self.config.lmgtfy_endpoint()
        lmgtfy_link = f"{current_endpoint}/lmgtfy/search?q={encoded_search_string}&btnK=Google+Search"

        em = discord.Embed(
            description=f"Hey! Here's what you asked for, [Click here!]({lmgtfy_link})"
        )
        em.color = discord.Color(8599000)
        em.timestamp = discord.utils.utcnow()
        em.set_image(url=random.choice(self.IMAGES))
        await ctx.send(embed=em)

    @googleit.command(name="setendpoint")
    @commands.is_owner()
    async def setendpoint(self, ctx: commands.Context, endpoint_url: str):
        """
        Sets the endpoint for LMGTFY!

        Example:
        [p]googleit setendpoint https://cog-creators.github.io

        """
        if not endpoint_url.startswith("http://") and not endpoint_url.startswith(
            "https://"
        ):
            await ctx.send(
                "Please provide a valid URL starting with http:// or https://"
            )
            return
        await self.config.lmgtfy_endpoint.set(endpoint_url)
        await ctx.send(
            f"LMGTFY endpoint set to: {chat_formatting.inline(endpoint_url)}"
        )

    @googleit.command(name="showendpoint")
    @commands.is_owner()
    async def showendpoint(self, ctx: commands.Context):
        """
        Displays the endpoint for LMGTFY!

        Example:
        [p]googleit showendpoint
        """
        current_endpoint = await self.config.lmgtfy_endpoint()
        await ctx.send(
            f"Current LMGTFY endpoint: {chat_formatting.inline(current_endpoint)}"
        )
