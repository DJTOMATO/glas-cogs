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
    """A cog for finding game deals from various storefronts."""
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("glas.glas-cogs.ggdeals")

    @commands.command(cooldown_after_parsing=True)
    @commands.bot_has_permissions(embed_links=True)
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
            # Check if the bot has embed_links permission before sending embed

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
    async def deallist(self, ctx):
        """Read the invoking message for a list of game titles, fetch the lowest key price for each, and return a CSV + formatted list.

        Usage examples:
        - Multi-line list after the command:
            !deallist
            * Game One
            * Game Two

        - Single-line comma/semicolon separated:
            !deallist Game One, Game Two
        """
        raw = ctx.message.content or ""
        # Parse game titles from message
        lines = raw.splitlines()
        items = []
        if len(lines) > 1:
            # Everything after the first line is treated as an item list
            for ln in lines[1:]:
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("*"):
                    ln = ln.lstrip("*").strip()
                items.append(ln)
        else:
            # single-line: try to capture the remainder after the command invocation
            parts = raw.split(None, 1)
            rest = parts[1].strip() if len(parts) > 1 else ""
            if rest:
                # try common separators
                sep_found = False
                for sep in ["\n", ";", ",", "|"]:
                    if sep in rest:
                        items = [p.strip().lstrip("*").strip() for p in rest.split(sep) if p.strip()]
                        sep_found = True
                        break
                if not sep_found:
                    items = [rest]

        if not items:
            await ctx.send(
                "I couldn't find any games in your message. Please put a list of games after the command, one per line or comma-separated."
            )
            return

        # Show typing while resolving ids, calling APIs and building CSV/message
        async with ctx.typing():
            # Resolve Steam app ids concurrently
            lookup_tasks = [get_steam_app_id_from_name(self.bot, title) for title in items]
            try:
                steam_ids = await asyncio.gather(*lookup_tasks)
            except Exception as e:
                await ctx.send(f"Error while resolving games: {e}")
                return

            # Map titles to steam ids (None if not found)
            title_to_steam = {title: sid for title, sid in zip(items, steam_ids)}

            # Prepare list of ids to query (unique, filter None)
            ids_to_query = [sid for sid in {sid for sid in steam_ids if sid}]

            api_result = None
            if ids_to_query:
                try:
                    api_result = await get_ggdeals_api_prices_by_steamid(self.bot, ids_to_query)
                except ClientConnectorError:
                    await ctx.send("Price service unavailable (maintenance). Try later.")
                    return
                except Exception as e:
                    await ctx.send(f"Unexpected error fetching prices: {e}")
                    return

            # Build results (also collect numeric values for total when possible)
            rows = []  # list of tuples (title, price_text, price_num_or_None, currency_str)
            data = api_result.get("data") if api_result else {}
            for title, sid in title_to_steam.items():
                if not sid:
                    rows.append((title, "NOT FOUND", None, None))
                    continue
                api_game_data = None
                if data:
                    api_game_data = data.get(str(sid)) or data.get(int(sid))
                if not api_game_data:
                    rows.append((title, "N/A", None, None))
                    continue
                prices = api_game_data.get("prices", {}) or {}
                # Prefer current keyshops price (lowest key price)
                price_val = prices.get("currentKeyshops")
                # Fallback to currentRetail
                if price_val in (None, "", 0, 0.0):
                    price_val = prices.get("currentRetail")
                if price_val in (None, "", 0, 0.0):
                    rows.append((title, "N/A", None, None))
                else:
                    # Determine currency
                    currency = prices.get("currency") or ""
                    # Attempt to parse numeric value
                    price_num = None
                    try:
                        # Some APIs return strings or numbers; normalize
                        price_num = float(str(price_val).replace(",", "").strip())
                    except Exception:
                        price_num = None
                    currency_display = f" {currency}" if currency else ""
                    rows.append((title, f"${price_val}{currency_display}", price_num, currency))

            # Compute total if currencies are consistent across numeric entries
            numeric_values = [r[2] for r in rows if r[2] is not None]
            currencies = {r[3] for r in rows if r[2] is not None and r[3] is not None}
            total_text = None
            if numeric_values:
                if len(currencies) <= 1:
                    total_value = sum(numeric_values)
                    currency_label = (next(iter(currencies)) or "").strip()
                    currency_suffix = f" {currency_label}" if currency_label else ""
                    total_text = f"${total_value:.2f}{currency_suffix}"
                else:
                    # Mixed currencies - can't meaningfully sum
                    total_text = "(mixed currencies, total unavailable)"
            rows.sort(key=lambda r: (r[2] is None, r[2]))
            names_only = [title for title, _, _, _ in rows]
            names_only_msg = "\n - ".join(names_only)
            # Create CSV
            import io

            csv_lines = ["title,price"]
            for t, p, _, _ in rows:
                # Escape double quotes and wrap title in quotes if comma in title
                safe_title = t.replace('"', '""')
                if "," in safe_title or "\n" in safe_title:
                    safe_title = f'"{safe_title}"'
                csv_lines.append(f"{safe_title},{p}")
            if total_text:
                csv_lines.append(f"TOTAL,{total_text}")

            csv_text = "\n".join(csv_lines)

            # Build formatted message
            formatted_lines = [f"{t} — {p}" for t, p, _, _ in rows]
            if total_text:
                formatted_lines.append("")
                formatted_lines.append(f"Total value: {total_text}")
            formatted_msg = "\n".join(formatted_lines)

            # Create embed (sending is done after typing context)
            embed = discord.Embed(title="Deal list: lowest key prices", description=formatted_msg)
            await ctx.send("**Games sorted by lowest price:**\n" + names_only_msg)
        # send CSV + embed (outside typing context)
        try:
            # send CSV as file
            fp = io.BytesIO(csv_text.encode("utf-8"))
            fp.seek(0)
            file = discord.File(fp, filename="deals.csv")
            await ctx.send(embed=embed, file=file)
        except Exception:
            # If sending file fails, just send the text
            await ctx.send(formatted_msg)

    @commands.command()
    @commands.bot_has_permissions(add_reactions=True)
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
        embed.set_image(url="https://bae.lena.moe/KHHRKQE1FoJl.jpg")

        # Check if the bot has add_reactions permission
 
        try:
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            pass

        try:
            await ctx.author.send(embed=embed)
            # Use ctx.tick() to handle reactions gracefully instead of manual sleep/delete
            dm_message = await ctx.send("ℹ️ Sent you a DM with the risks.")
            # Delete the message after 10 seconds using delete_after
            await dm_message.delete(delay=10)
        except discord.Forbidden:
            await ctx.send(
                "⚠️ I couldn't send you a DM. Please enable DMs from server members to receive the risks."
            )
