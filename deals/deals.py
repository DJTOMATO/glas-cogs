import discord
import random
from datetime import datetime
from redbot.core import commands
import logging
from .functions import WebScraper
import asyncio
from aiohttp import ClientConnectorError


def __init__(self, bot):
    self.bot = bot
    self.log = logging.getLogger("glas.glas-cogs.ggdeals")


class Deals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("glas.glas-cogs.ggdeals")

    @commands.command()
    async def deals(
        self,
        ctx,
        *,
        gamename: commands.clean_content(
            fix_channel_mentions=False,
            use_nicknames=False,
            escape_markdown=False,
            remove_markdown=False,
        ) = None,
    ):
        """Returns a list of deals"""
        async with ctx.typing():
            scraper = WebScraper()
            if gamename is None:
                await ctx.send(
                    "You forgot the game name! Please try again. \n\n Example: !deals The Last of Us 2"
                )
                return
            try:
                results = await scraper.scrape(ctx, gamename)
                if results is None:
                    await ctx.send(f"Error: Game {gamename} not found")
                    return
            except ClientConnectorError:
                await ctx.send("Site under maintenance, please try later.")
                return
            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {str(e)}")
                return

            formatted_data, all_deals_details, scraped_game_info = results

            # Create the embed
            embed, embed2 = await scraper.make_embed(
                ctx, formatted_data, all_deals_details, scraped_game_info
            )

            # Send the final embed and remove the "Bot is typing..." status
            await ctx.send(embed=embed)
            await ctx.send(embed=embed2)

            # command that returns text

    @commands.command()
    async def risks(self, ctx):
        """Warns you about risks of using keyshops"""
        warning = (
            "Warning: Before purchasing from keyshops, be aware of the following:\n\n"
            "- Keys may not come directly from the publisher.\n"
            "- Additional fees may appear at checkout for payment methods.\n"
            "- Also, Extra 'order fees' at checkout.\n"
            "- Use reputable vendors on keyshops.\n"
            "- Beware of hidden lower prices.\n"
            "- EU VAT will be added if applicable.\n"
            "- Do not buy purchased gifts, there's risk of Steam accounts ban\n\n"
            "Note: We're not responsible for any purchasing issues; use at your discretion."
        )

        embed = discord.Embed(title="Risks", description=warning)
        embed.set_image(url="https://bae.lena.moe/tHZFfvvP5HRt.jpg")

        await ctx.message.add_reaction("✅")

        try:
            await ctx.author.send(embed=embed)
            dm_message = await ctx.send("ℹ️ Sent you a DM with the risks.")
        except discord.Forbidden:
            await ctx.send(
                "⚠️ I couldn't send you a DM. Please enable DMs from server members to receive the risks."
            )
        else:
            # Schedule a task to delete the message after 10 seconds
            await asyncio.sleep(10)
            await dm_message.delete()
