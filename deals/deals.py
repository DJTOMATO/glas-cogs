import discord
import random
from datetime import datetime
from redbot.core import commands
import logging
from .functions import (
    get_steam_app_id_from_name,
    get_ggdeals_api_prices_by_steamid,
    get_steam_game_details,
    get_ggdeals_bundles_by_steam_app_id,
)
import html

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
            if gamename is None:
                await ctx.send(
                    "You forgot the game name! Please try again. \n\n Example: !deals The Last of Us 2"
                )
                return
            steam_app_id = await get_steam_app_id_from_name(self.bot, gamename)
            if not steam_app_id:
                await ctx.send(f"Error: Game {gamename} not found on Steam.")
                return
            # Use the API to get deals/prices
            try:
                api_result = await get_ggdeals_api_prices_by_steamid(
                    self.bot, [steam_app_id]
                )
            except ClientConnectorError:
                await ctx.send("Site under maintenance, please try later.")
                return
            except Exception as e:
                await ctx.send(f"An unexpected error occurred: {str(e)}")
                return
            # Create the embed
            # Use the Steam game title if available
            title = gamename
            steam_details = await get_steam_game_details(steam_app_id)
            if steam_details and steam_details.get("name"):
                title = steam_details["name"]
            embed = discord.Embed(title=f"Deals for {title}")
            api_game_data = None
            if api_result and "data" in api_result:
                api_data = api_result["data"]
                api_game_data = api_data.get(str(steam_app_id)) or api_data.get(
                    int(steam_app_id)
                )
            if api_game_data:
                # Fetch Steam game details for image, description, genres, reviews, release date
                steam_details = await get_steam_game_details(steam_app_id)
                if steam_details:
                    if steam_details.get("image"):
                        embed.set_image(url=steam_details["image"])
                    if steam_details.get("description"):
                        desc = html.unescape(steam_details["description"])
                        embed.add_field(
                            name="Description",
                            value=desc[:1024],
                            inline=False,
                        )
                    if steam_details.get("genres"):
                        embed.add_field(
                            name="Genres",
                            value=", ".join(steam_details["genres"]),
                            inline=True,
                        )
                    if steam_details.get("release_date"):
                        embed.add_field(
                            name="Release Date",
                            value=steam_details["release_date"],
                            inline=True,
                        )
                    if steam_details.get("reviews"):
                        embed.add_field(
                            name="Steam Reviews",
                            value=str(steam_details["reviews"]),
                            inline=True,
                        )
                # Add link to all deals at the top
                if steam_details and steam_details.get("name"):
                    deals_url = f"https://gg.deals/game/{steam_details['name'].replace(' ', '-')}"
                else:
                    deals_url = f"https://gg.deals/game/{gamename.replace(' ', '-')}"

                warning = (
                    "Buying from keyshops it may have risks type ``{prefix}risks`` for details."
                ).format(prefix=ctx.clean_prefix)
                embed.add_field(
                    name="Check all deals in current shops",
                    value=f"[Clicking here]({deals_url}) \n\n{warning}",
                    inline=False,
                )
                # Add prices/fees at the bottom
                if api_game_data:
                    prices = api_game_data.get("prices", {})
                    currency = prices.get("currency", "-")
                    currency = f" {currency}" if currency != "-" else ""

                    def valid_price(val):
                        return val not in (0, 0.0, "0", "0.0", "0.00", 0.00, None)

                    current_retail = prices.get("currentRetail", "-")
                    if valid_price(current_retail):
                        embed.add_field(
                            name="Current Retail",
                            value=f"${current_retail}{currency}",
                            inline=True,
                        )

                    current_keyshops = prices.get("currentKeyshops", "-")
                    if valid_price(current_keyshops):
                        embed.add_field(
                            name="Current Keyshops",
                            value=f"${current_keyshops}{currency}",
                            inline=True,
                        )

                    historical_retail = prices.get("historicalRetail", "-")
                    if valid_price(historical_retail):
                        embed.add_field(
                            name="Historical Retail",
                            value=f"${historical_retail}{currency}",
                            inline=True,
                        )

                    historical_keyshops = prices.get("historicalKeyshops", "-")
                    if valid_price(historical_keyshops):
                        embed.add_field(
                            name="Historical Keyshops",
                            value=f"${historical_keyshops}{currency}",
                            inline=True,
                        )
            elif api_result and "error" in api_result:
                embed.add_field(
                    name="API error",
                    value=api_result["error"],
                    inline=False,
                )
            else:
                embed.description = "No deals found."
            await ctx.send(embed=embed)
            # Optionally, you can also send a message if no Steam details were found
            if not steam_details:
                await ctx.send("ℹ️ No extra Steam info found for this game.")

            # Fetch bundle data from GG.deals and send as a separate embed if bundles exist
            bundles_result = await get_ggdeals_bundles_by_steam_app_id(
                self.bot, [steam_app_id]
            )
            bundle_info = None
            if bundles_result and "data" in bundles_result:
                bundle_info = bundles_result["data"].get(
                    str(steam_app_id)
                ) or bundles_result["data"].get(int(steam_app_id))
            if bundle_info and bundle_info.get("bundles"):
                bundle_lines = []
                for bundle in bundle_info["bundles"][:3]:  # Show up to 3 bundles
                    bundle_title = bundle.get("title", "?")
                    bundle_url = bundle.get("url")
                    date_from = bundle.get("dateFrom")
                    date_to = bundle.get("dateTo")
                    # Format dates to YYYY-MM-DD only
                    if date_from:
                        date_from = date_from.split(" ")[0]
                    if date_to:
                        date_to = date_to.split(" ")[0]
                    tiers = bundle.get("tiers", [])
                    tier_lines = []
                    for tier in tiers:
                        price = tier.get("price")
                        currency = tier.get("currency")
                        games_count = tier.get("gamesCount")
                        tier_desc = f"{price} {currency}"
                        if games_count:
                            tier_desc += f" ({games_count} games)"
                        tier_lines.append(tier_desc)
                    tier_str = ", ".join(tier_lines)
                    if bundle_url:
                        bundle_line = f"[{bundle_title}]({bundle_url}) | {tier_str}"
                    else:
                        bundle_line = f"{bundle_title} | {tier_str}"
                    if date_from:
                        bundle_line += f"\nFrom: {date_from}"
                    if date_to:
                        bundle_line += f" to {date_to}"
                    bundle_lines.append(bundle_line)
                bundle_embed = discord.Embed(title="Bundles")
                bundle_embed.description = "\n\n".join(bundle_lines)
                await ctx.send(embed=bundle_embed)
            elif bundle_info and not bundle_info.get("bundles"):
                await ctx.send("No bundles found for this game.")
            elif bundles_result and "error" in bundles_result:
                await ctx.send(f"Bundles API error: {bundles_result['error']}")

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
