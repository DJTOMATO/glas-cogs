from aiohttp import ClientSession
from bs4 import BeautifulSoup
from .functions import scraper

# Cool Kids don't use request
import aiohttp
import discord
from redbot.core import Config, commands

import logging
import re


class Kofi(commands.Cog):
    """Ko-fi Commands"""

    """Support your favourite bot/server!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier="kofi")
        self.config.register_global(kofi_url=None)
        self.kofi_url = None

    async def initialize(self):
        kofi_url = await self.config.kofi_url()
        self.kofi_url = kofi_url

    # Set Kofi URL
    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def setkofi(self, ctx, url):
        """
        Set's the Kofi URL for the bot/server
        """
        await self.config.kofi_url.set(url)
        await ctx.send(f"Kofi URL set to {url}")

    # Get Kofi Goal Info
    # Create and return an embed with the information
    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def kofi(self, ctx):
        """
        Posts ko-fi for Bot/Server
        """
        kofi_url = await self.config.kofi_url()

        if kofi_url is None:
            await ctx.send("Kofi URL is not set. Use the `!seturl` command to set it.")
            return
        results = await scraper(kofi_url)

        name = results.get("Ko-fi User", "No Ko-fi User Found")
        embed = discord.Embed()
        c = results.get("Goal Title", "No Title Found")

        embed.set_author(
            name=f"Ko-fi for {name}",
            url=kofi_url,
            icon_url=results.get(
                "Profile Image URL",
                "https://cdn.discordapp.com/attachments/861428239012069416/1176614114613788842/logey.png",
            ),
        )
        pro = results.get("Current Percentage", "No Percentage Found")
        gres = results.get("Of Goal Total", "No Goal Total Found")
        embed.title = f"Current Goal: {c} \n -- {pro}{gres}! --"
        embed.url = kofi_url

        embed.description = results.get("Goal Description", "No Description Found")

        about = results.get("About User", "No About User Found")
        amount = results.get("Ko-fi Received", "0")
        embed.add_field(
            name="About User",
            value=f"{about} \n\n __So far, this user has received {amount} Ko-fi!__",
        )

        embed.set_image(
            url=results.get(
                "Profile Banner URL",
                "https://cdn.discordapp.com/attachments/861428239012069416/1176614114613788842/logey.png",
            )
        )

        button = discord.ui.Button(label=f"❤️ Support {name} on Ko-fi!", url=kofi_url)

        # Create a view and add the button
        view = discord.ui.View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)
