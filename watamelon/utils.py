from random import choice
import discord

from .watamelons import watamelon


""" async def gensokyo_status(self) -> bool:
    ""Watamelon API Status""
    async with self.session.get("https://fumoapi.herokuapp.com/random") as response:
        if response.status == 200:
            return True
        else:
            return False

async def watamelon_calling_ritual(self):
    ""Watamelon API Call.""
    if await gensokyo_status(self):
        async with self.session.get("https://fumoapi.herokuapp.com/random") as response:
            get_fumo = await response.json()
            return get_fumo["URL"]
    else:
        return """


async def summon_watamelon(self, ctx, type: str):
    """Summon a Watamelon."""
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        get_watamelon = await watamelon_calling_ritual(self)
        if watamelon:
            e.title = f"Here's a Random Watamelon! 🍉"
            e.set_image(url=get_watamelon)
            e.set_footer(
                text="Source: https://fumoapi.herokuapp.com/",
                icon_url="https://files.catbox.moe/42wylc.png",
            )
        else:
            return await ctx.send(
                "There's something wrong with the Watamelon API, try again later!"
            )
    else:
        e.title = f"Here's a Random Watamelon {type.title()}! 🍉"
        e.set_image(url=choice(watamelon[type]))
        e.set_footer(
            text="Source: /watamelon/ - Code by Kuro-Cogs/fumo",
            icon_url="https://files.catbox.moe/42wylc.png",
        )
    await ctx.send(embed=e)
