import discord
import random
from datetime import datetime
from redbot.core import commands


class Fire(commands.Cog):
    @commands.command()
    async def fire(self, ctx):
        """Fireworks!

        Launch a firework to celebrate the holidays!"""

        fires = [
            "https://bae.lena.moe/su1e9j2omur0.gif",
            "https://bae.lena.moe/slngy57j7758.gif",
            "https://bae.lena.moe/gja1us7ukcid.gif",
            "https://bae.lena.moe/pw4gzkecys2o.gif",
            "https://bae.lena.moe/ljpi86dgts9m.gif",
            "https://bae.lena.moe/paigsm7dcprp.gif",
            "https://bae.lena.moe/hk1k0dbhu3dr.gif",
            "https://bae.lena.moe/2cew6pwhhdwf.gif",
            "https://bae.lena.moe/zbcadrotd7mu.gif",
        ]

        em = discord.Embed(
            description=f"{ctx.author.mention} has launched a firework!. ¡Happy Holidays!"
        )
        em.color = discord.Color(8599000)
        em.timestamp = datetime.now()
        em.set_image(url=random.choice(fires))
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            await ctx.send("I don't have permission to embed links in this channel.")
            return
        await ctx.send(embed=em)
