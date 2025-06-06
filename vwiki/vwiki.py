from .aiovwiki import AioVwiki
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
            all_data = await vwiki.all(f"{chuuba}")

            return sm, tr, qt, nm, img, all_data

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def vsearch(self, ctx, *, chuuba: str):
        """Search vtubers at vtuberwiki

        Example: [p]vsearch Usada Pekora"""
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            await ctx.send("I don't have permission to embed links in this channel.")
            return
        sm, tr, qt, nm, img, all_data = await self.search(chuuba)
        if not nm:
            await ctx.send("No information found. Please try again!")
            return
        max_fchars = 1500
        sm_txt = trim(sm, max_fchars)
        nm = nm.replace("_", " ")
        embed = discord.Embed(title=f"{nm}'s Profile", description=sm_txt)
        embed.set_image(url=img)

        all_data = all_data.copy()
        self.log.warning(f"All data: {all_data}")
        # Example structure of all_data['infobox_details']:
        # {'Debut Date': 'YouTube: 2019/07/17', 'Channel': [{'text': 'YouTube', 'url': '...'}, ...], ... }

        # Add infobox details to the embed
        infobox_details_data = all_data.get("infobox_details")
        if infobox_details_data and isinstance(infobox_details_data, dict):
            self.log.debug(f"Processing infobox_details: {infobox_details_data}")
            for key, value in infobox_details_data.items():
                field_value_str = ""
                if isinstance(value, str):
                    field_value_str = value
                elif isinstance(value, list):  # Expected for 'Channel', 'Website', etc.
                    link_display_parts = []
                    for item_in_list in value:
                        if (
                            isinstance(item_in_list, dict)
                            and item_in_list.get("text")
                            and item_in_list.get("url")
                        ):
                            link_display_parts.append(
                                f"[{item_in_list['text']}]({item_in_list['url']})"
                            )
                        elif isinstance(
                            item_in_list, str
                        ):  # Fallback for a list of simple strings
                            link_display_parts.append(item_in_list)
                    if link_display_parts:
                        field_value_str = "\n".join(link_display_parts)

                if field_value_str:  # Only add field if there's a value to show
                    embed.add_field(
                        name=str(key), value=trim(field_value_str, 1024), inline=True
                    )

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
