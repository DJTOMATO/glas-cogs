from random import choice
import discord

from .watamelons import watamelon


async def summon_watamelon(self, ctx, type: str):
    """Summon a Watamelon."""

    
    e = discord.Embed(color=await ctx.embed_color())
    e.title = f"Here's a Random Watamelon {type.title()}! 🍉"
    e.set_image(url=choice(watamelon[type]))
    e.set_footer(
        text="Code by Kuro - Watame did nothing wrong!",
        icon_url="https://files.catbox.moe/42wylc.png",
    )
    await ctx.send(embed=e)
