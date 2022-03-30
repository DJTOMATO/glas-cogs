from random import choice
import discord

from .d4dj import d4dj


async def summon_esora(self, ctx, type: str):
    """Summon a Esora."""
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        get_esora = await esora_calling_ritual(self)
        if esora:
            e.title = f"Here's a Random Esora! ✨"
            e.set_image(url=get_esora)
            e.set_footer(
                text="Source: https://d4dj.fandom.com/",
                icon_url="https://bae.lena.moe/ad5bq96j8zln.webp",
            )
        else:
            return await ctx.send("There's something wrong with the D4DJ API, try again later!")
    else:
        e.title = f"Here's a Random Esora {type.title()}! ✨"
        e.set_image(url=choice(esora[type]))
        e.set_footer(
            text="Source: https://d4dj.fandom.com/",
            icon_url="https://bae.lena.moe/ad5bq96j8zln.webp",
        )
    await ctx.send(embed=e)


async def summon_noa(self, ctx, type: str):
    """Summon a noa."""
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        get_noa = await noa_calling_ritual(self)
        if noa:
            e.title = f"Here's a Random noa! 🐀"
            e.set_image(url=get_noa)
            e.set_footer(
                text="Source: https://fumoapi.herokuapp.com/",
                icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
            )
        else:
            return await ctx.send("There's something wrong with the noa API, try again later!")
    else:
        e.title = f"Here's a Random noa {type.title()}! 🐀"
        e.set_image(url=choice(noa[type]))
        e.set_footer(
            text="Source: /hlgg/ - Code by Kuro-Cogs/fumo",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    await ctx.send(embed=e)
