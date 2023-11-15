import discord
import random
from datetime import datetime
from redbot.core import commands
import urllib.parse


class GoogleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lmgtfy_endpoint = "https://lmgtfy.lena.moe"

    @commands.command()
    async def googleit(self, ctx, option: str = None, value: str = None, *args: str):
        """
        Google it!

        To search: !googleit "text" or !googleit text
        To set or display endpoint: !googleit endpoint url or !googleit endpoint
        """
        if option == "endpoint":
            if not value:
                await self._display_endpoint(ctx)
            else:
                await self._set_endpoint(ctx, value)
        else:
            # Assume it's a search
            search_string = ctx.message.clean_content[
                len(ctx.prefix) + len(ctx.invoked_with) + 1 :
            ]
            await self._search(ctx, search_string)

    async def _search(self, ctx, search_string):
        images = [
            "https://media.tenor.com/KhQvEDtumlUAAAAC/here-it-is-americas-got-talent.gif",
            "https://media.tenor.com/bWRm7AHxOwUAAAAd/you-see-jabrils.gif",
            "https://media.tenor.com/70Jj39J1vrAAAAAC/give.gif",
            "https://media.tenor.com/4FK8LHl8w4EAAAAC/come-to-me-dr-evil.gif",
            "https://media.tenor.com/fjDNU3SrgCAAAAAC/loeya-here.gif",
        ]
        encoded_search_string = urllib.parse.quote(search_string)
        lmgtfy_link = f"{self.lmgtfy_endpoint}/lmgtfy/search?q={encoded_search_string}&btnK=Google+Search"
        em = discord.Embed(
            description=f"Hey! Here's what you asked for, [Click here!]({lmgtfy_link})"
        )
        em.color = discord.Color(8599000)
        em.timestamp = datetime.now()
        em.set_image(url=random.choice(images))
        await ctx.send(embed=em)

    async def _set_endpoint(self, ctx, endpoint_value):
        self.lmgtfy_endpoint = endpoint_value
        await ctx.send(f"LMGTFY endpoint set to: {endpoint_value}")

    async def _display_endpoint(self, ctx):
        await ctx.send(f"Current LMGTFY endpoint: {self.lmgtfy_endpoint}")
