from random import choice
import discord

from .mogos import mogo


async def summon_mogo(self, ctx, type: str):
    """Summon a Mogogo."""
    e = discord.Embed(color=await ctx.embed_color())    
    if type == "random":
        
        if mogo:
            e.title = f"Here's a Random Mogogo!"
            e.set_image(url=get_mogo)
            e.set_footer(
                text="Source: https://fumoapi.herokuapp.com/",
                icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
            )
        else:
            return await ctx.send("There's something wrong with the Ogey API, try again later!")
    else:
        e.title = f"Here's a Random Mogogo {type.title()}!"
        e.set_image(url=choice(mogo[type]))
        e.set_footer(
            text="Code by Kuro",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    await ctx.send(embed=e)
