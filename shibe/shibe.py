# get a random shiba inu pic
# originally made by https://github.com/grayconcaves/FanCogs/


# Discord
import discord

# Red
from redbot.core import commands

# Libs
import aiohttp

class Shibe(commands.Cog):
    """Shibe commands"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.shibapi = "https://dog.ceo/api/breed/shiba/images/random"

    
    @commands.command()
    async def shibe(self, ctx):
        """Get a random shiba inu picture"""
        try:
            async with self.session.get(self.shibapi) as s:
                shibe = await s.json()
                if shibe["status"] == "success":
                    await ctx.send(shibe["message"])
                else:
                    await ctx.send("Failed to fetch a shiba inu picture.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")


    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
