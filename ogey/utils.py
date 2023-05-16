from random import choice
import discord

from .ogeys import ogey


async def summon_ogey(self, ctx, type: str):
    """Summon a Ogey."""
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        get_ogey = await ogey_calling_ritual(self)
        if ogey:
            e.title = f"Here's a Random Ogey! 🐀"
            e.set_image(url=get_ogey)
            e.set_footer(
                text="Source: https://fumoapi.herokuapp.com/",
                icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
            )
        else:
            return await ctx.send("There's something wrong with the Ogey API, try again later!")
    else:
        e.title = f"Here's a Random Ogey {type.title()}! 🐀"
        e.set_image(url=choice(ogey[type]))
        e.set_footer(
            text="Code by Kuro",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    await ctx.send(embed=e)
