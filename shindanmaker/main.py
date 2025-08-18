from redbot.core import commands
from redbot.core.bot import Red
import discord
import asyncio
import random

from .shindan_helper import get_shindan_title
from shindan_cli import shindan
import re


class ShindanMaker(commands.Cog):
    """ShindanMaker integration for Discord embeds (text + emojis + link)."""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs)"
    __version__ = "0.0.7"

    def __init__(self, bot: Red):
        self.bot: Red = bot

    @commands.command(name="shindan")
    async def shindan_command(
        self,
        ctx: commands.Context,
        shindan_id: int,
        user: discord.Member = None,
        wait: bool = False,
        link: bool = True,
        hashtag: bool = True,
    ):
        """Generate a ShindanMaker result for a user (or self) with styling."""
        target = user or ctx.author
        target_name = str(target.display_name)
        avatar_url = getattr(target.display_avatar, "url", None)

        await ctx.typing()

        # Fetch result using CLI
        try:
            result = await asyncio.to_thread(
                shindan, shindan_id, target_name, wait=wait
            )
        except Exception as e:
            return await ctx.send(f"❌ Failed to generate shindan: {e}")

        # Get title separately
        try:
            shindan_title = await asyncio.to_thread(get_shindan_title, shindan_id)
        except Exception:
            shindan_title = "Shindan Result"

        # Random pastel-ish color
        color = discord.Color.from_rgb(
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255),
        )
        # Clean result lines: remove URLs and strip
        lines = [
            re.sub(r"https?://\S+", "", line).replace("\xa0", " ").strip()
            for line in result.get("results", [])
            if line.strip()
        ]

        # Combine all lines as paragraphs
        remaining_text = "\n\n".join(lines)

        embed = discord.Embed(
            title=f"📝 {shindan_title}",
            description=f"```\n{remaining_text}\n```",
            color=color,
        )
        embed.set_thumbnail(url=avatar_url)
        # Shindan link
        if link:
            shindan_url = result.get(
                "shindan_url", f"https://en.shindanmaker.com/{shindan_id}"
            )
            embed.add_field(
                name="🔗 Shindan Link",
                value=f"[Click here]({shindan_url})",
                inline=False,
            )

        embed.set_footer(text=f"ShindanMaker ID: {shindan_id}")

        await ctx.send(embed=embed)
