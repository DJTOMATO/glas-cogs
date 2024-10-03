from vtuberwiki import AioVwiki
from redbot.core import commands
import discord
import logging


def trim(txt, limit):
    return txt[:limit] + "..." if len(txt) > limit else txt


class Vwiki(commands.Cog):
    """Vwiki Commands"""

    """Search vtubers at vtuberwiki"""

    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("glas.glas-cogs.Vwiki")

    async def search(self, chuuba: str):
        async with AioVwiki() as vwiki:
            sm = await vwiki.summary(vtuber=f"{chuuba}")
            tr = await vwiki.trivia(vtuber=f"{chuuba}")
            qt = await vwiki.quote(vtuber=f"{chuuba}")
            nm = vwiki.name
            img = vwiki.image
            return sm, tr, qt, nm, img

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def vsearch(self, ctx, *, chuuba: str):

        sm, tr, qt, nm, img = await self.search(chuuba)
        if not nm:
            await ctx.send("No information found. Please try again!")
            return
        max_fchars = 1500
        sm_txt = trim(sm, max_fchars)
        nm = nm.replace("_", " ")
        embed = discord.Embed(title=f"{nm}'s Profile", description=sm_txt)
        embed.set_image(url=img)

        tr_txt = "- " + trim("\n- ".join(tr), max_fchars)
        tr_txt = trim(tr_txt, max_fchars - 700)

        tr_lines = tr_txt.split("\n")
        if tr_lines:
            for idx, line in enumerate(tr_lines):
                if line.startswith("- She likes"):
                    tr_lines[idx] = "__She Likes:__"
                if line.startswith("- She dislikes"):
                    tr_lines[idx] = "__She dislikes:__"
            tr_lines = tr_lines[:-1]
        tr_txt = "\n".join(tr_lines)

        if len(tr) > 15:
            embed.add_field(name="Trivia", value=tr_txt, inline=False)
        if len(qt) > 15:
            qt_txt = "\n- ".join(sorted(trim(x, max_fchars) for x in qt)[:5])
            qt_txt = "- " + qt_txt
            qt_txt = trim(qt_txt, max_fchars)

        if len(qt) > 15:
            embed.add_field(name="Quotes", value=qt_txt, inline=False)

        await ctx.send(embed=embed)
