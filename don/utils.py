from random import choice
import discord

from .dons import don


async def summon_don(self, ctx, type: str):
    """Summon a Don."""
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        get_don = await don_calling_ritual(self)
        if don:
            e.title = f"Here's a Random Don! 🥁"
            e.set_image(url=get_don)
            e.set_footer(
                text="Source: https://fumoapi.herokuapp.com/",
                icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
            )
        else:
            return await ctx.send("There's something wrong with the Don API, try again later!")
    else:
        e.title = f"Here's a Random Don {type.title()}! 🐀"
        e.set_image(url=choice(don[type]))
        e.set_footer(
            text="Source: Taiko Discord - Code by Kuro-Cogs/fumo",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    await ctx.send(embed=e)
