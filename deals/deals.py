import discord
import random
from datetime import datetime
from redbot.core import commands
import logging
from .functions import WebScraper, get_steam_app_id_from_name

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
            # Scrape first to get all info and possibly the steamid from the website
            results = None
            steam_app_id = None
            try:
                results = await scraper.scrape(ctx, gamename)
                if results is None:
                    await ctx.send(f"Error: Game {gamename} not found")
                    return
                # Unpack the new return value
                if len(results) == 4:
                    (
                        formatted_data,
                        all_deals_details,
                        scraped_game_info,
                        steam_app_id,
                    ) = results
                else:
                    formatted_data, all_deals_details, scraped_game_info = results
            except ClientConnectorError:
                await ctx.send("Site under maintenance, please try later.")
                return
            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {str(e)}")
                return
            # If not found in scrape, try fallback
            if not steam_app_id:
                steam_app_id = await get_steam_app_id_from_name(self.bot, gamename)
                # await ctx.send(f"Steam ID after search is :{steam_app_id}")
            api_result = None
            if steam_app_id:
                # await ctx.send(f"Steam ID is :{steam_app_id}")
                api_result = await scraper.get_ggdeals_api_prices_by_steamid(
                    self.bot, [steam_app_id]
                )
                # self.log.warning(f"API result for {steam_app_id}: {api_result}")
                # Debug: log keys if data exists
                # if api_result and "data" in api_result:
                # self.log.warning(
                #    f"API data keys: {list(api_result['data'].keys())}"
                # )
            # Create the embed
            embed, embed2 = await scraper.make_embed(
                ctx, formatted_data, all_deals_details, scraped_game_info
            )
            # If API data is available, add it to the first embed
            api_game_data = None
            if api_result and "data" in api_result:
                # Try both string and int keys for steam_app_id
                api_data = api_result["data"]
                api_game_data = api_data.get(str(steam_app_id))
                if not api_game_data:
                    api_game_data = api_data.get(int(steam_app_id))
            if api_game_data:
                prices = api_game_data.get("prices", {})
                currency = prices.get("currency", "-")
                currency = f" {currency}" if currency != "-" else ""
                embed2.add_field(
                    name="Current Retail",
                    value=f"${prices.get('currentRetail', '-')}{currency}",
                    inline=True,
                )
                embed2.add_field(
                    name="Current Keyshops",
                    value=f"${prices.get('currentKeyshops', '-')}{currency}",
                    inline=True,
                )
                embed2.add_field(
                    name="Historical Retail",
                    value=f"${prices.get('historicalRetail', '-')}{currency}",
                    inline=True,
                )
                embed2.add_field(
                    name="Historical Keyshops",
                    value=f"${prices.get('historicalKeyshops', '-')}{currency}",
                    inline=True,
                )
            elif api_result and "error" in api_result:
                embed2.add_field(
                    name="gg.deals API error",
                    value=api_result["error"],
                    inline=False,
                )
            # Send the final embed and remove the "Bot is typing..." status
            await ctx.send(embed=embed)
            await ctx.send(embed=embed2)

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
