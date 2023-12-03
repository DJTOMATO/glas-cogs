import discord
import random
from datetime import datetime
from redbot.core import commands
import logging
from .functions import WebScraper
import asyncio


def __init__(self, bot):
    self.bot = bot

    self.log = logging.getLogger("glas.glas-cogs.ggdeals")


class Deals(commands.Cog):
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
        ) = None
    ):
        """Returns a list of deals"""
        # Send a "Bot is typing..." status
        async with ctx.typing():
            # Perform your async task
            scraper = WebScraper()
            results = await scraper.scrape(gamename)
            formatted_data, all_details_details, scraped_game_info = results

            # Create the embed
            embed, embed2 = await scraper.make_embed(
                ctx, formatted_data, all_details_details, scraped_game_info
            )

            # Send the final embed and remove the "Bot is typing..." status
            await ctx.send(embed=embed)
            await ctx.send(embed=embed2)

    # command that returns text

    @commands.command()
    async def risks(self, ctx):
        """Warns you about buying in keyshops"""
        warning = "Before you buy in keyshops, make sure you read about all the associated risks.\n\n- Unknown source of the key\nMajority of keys in the store do not come directly from the publisher.\n\n- Obligatory payment fee at checkout\nAn extra fee will be added at checkout for all available payment methods.\n\n- Optional payment fee at checkout\nAn extra fee will be added at checkout for some payment methods. The remaining options are free of charge.\n\n- Obligatory 'order fee' at checkout\nAn 'order fee' will be added on top of the price displayed in the store when you reach the checkout.\n\n- Marketplace\nA marketplace is an eBay-like platform where multiple vendors sell their keys. Make sure you select a vendor with a good reputation and many successful transactions.\n\n- Best price is hidden\nThe store promotes more expensive offers, even though a lower price is available if you scroll down.\n\n- EU VAT added at checkout\nThe store will ask you about your country of origin at checkout. Once you select an EU country, EU VAT will be added to the final price.\n\n- Paid 'buyer protection'\nTrading Steam gifts is against the T&C of Steam. Purchasing them from keyshops might put your Steam account at risk.\n\n\n We do not hold accountable for issues you may encounter while purchasing, we just provide you a source of deals based on Web browsing, Final discretion is advised."

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
