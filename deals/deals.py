import asyncio
from datetime import datetime
import html
import io
import json
import logging
import os
import random
import re
import unicodedata
from aiohttp import ClientConnectorError

import discord
from redbot.core import app_commands, commands

from .functions import (
    get_ggdeals_api_prices_by_steamid,
    get_ggdeals_bundles_by_steam_app_id,
    get_ggdeals_search_url,
    get_steam_app_id_from_name,
    get_steam_game_details,
)


def _ggdeals_game_slug(title):
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii").lower()
    title = re.sub(r"['’‘`´]", "", title)
    title = re.sub(r"(?<=[a-z])\.(?=[a-z])", "", title)
    title = title.replace("&", " ")
    return re.sub(r"[^a-z0-9]+", "-", title).strip("-")


class _NoopTyping:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class _InteractionContext:
    def __init__(self, interaction):
        self.interaction = interaction
        self.messages = []

    def typing(self):
        return _NoopTyping()

    async def send(self, *args, **kwargs):
        content = args[0] if args else kwargs.pop("content", None)
        self.messages.append({"content": content, **kwargs})

    async def flush(self):
        contents = []
        embeds = []
        for message in self.messages:
            content = message.get("content")
            if content:
                content = str(content)
                if content == "No bundles found for this game." and embeds:
                    embeds[-1].add_field(name="Bundles", value=content, inline=False)
                else:
                    contents.append(content)
            embed = message.get("embed")
            if embed is not None:
                if isinstance(embed, (list, tuple)):
                    embeds.extend(embed)
                else:
                    embeds.append(embed)
            embeds.extend(message.get("embeds", []) or [])
        await self.interaction.edit_original_response(
            content="\n\n".join(contents) if contents else None,
            embeds=embeds,
        )


class Deals(commands.Cog):
    """A cog for finding game deals from various storefronts."""

    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("glas.glas-cogs.ggdeals")

    @app_commands.command(
        name="deals",
        description="Find current prices and bundles for a Steam game.",
    )
    @app_commands.describe(gamename="The game title to search for (or comma-separated titles)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def deals_slash(self, interaction: discord.Interaction, gamename: str):
        await interaction.response.defer(thinking=True)
        if "," in gamename:
            titles = [title.strip() for title in gamename.split(",") if title.strip()]
            if not titles:
                await interaction.edit_original_response(
                    content="Please enter one or more game titles separated by commas.",
                    embed=None,
                )
                return
            try:
                embed = await self._build_deallist_embed(titles)
            except ClientConnectorError:
                await interaction.edit_original_response(
                    content="Price service unavailable (maintenance). Try later.",
                    embed=None,
                )
                return
            except Exception as e:
                await interaction.edit_original_response(
                    content=f"Unexpected error fetching prices: {e}",
                    embed=None,
                )
                return
            await interaction.edit_original_response(content=None, embed=embed)
            return

        command_context = _InteractionContext(interaction)
        try:
            await self.deals.callback(self, command_context, gamename=gamename)
        except Exception as e:
            await command_context.send(f"An unexpected error occurred: {e}")
        await command_context.flush()

    async def _build_deallist_embed(self, titles):
        steam_ids = await asyncio.gather(
            *(get_steam_app_id_from_name(self.bot, title) for title in titles)
        )
        ids_to_query = list({steam_id for steam_id in steam_ids if steam_id})
        api_result = None
        if ids_to_query:
            api_result = await get_ggdeals_api_prices_by_steamid(self.bot, ids_to_query)

        data = api_result.get("data", {}) if isinstance(api_result, dict) else {}
        rows = []

        def parse_price(val):
            try:
                return float(str(val).replace(",", "").strip())
            except Exception:
                return None

        def is_valid_price(val):
            return val not in (0, 0.0, "0", "0.0", "0.00", 0.00, None, "")

        for title, steam_id in zip(titles, steam_ids):
            if not steam_id:
                rows.append((title, "NOT FOUND", None, None))
                continue
            game_data = data.get(str(steam_id)) or data.get(int(steam_id))
            if not game_data:
                rows.append((title, "N/A", None, None))
                continue
            prices = game_data.get("prices", {}) or {}
            retail_price = prices.get("currentRetail")
            keyshops_price = prices.get("currentKeyshops")

            retail_value = parse_price(retail_price)
            keyshops_value = parse_price(keyshops_price)
            price_val = None
            price_source = None
            if retail_value is not None and keyshops_value is not None:
                if retail_value <= keyshops_value:
                    price_val = retail_value
                    price_source = "Official store"
                else:
                    price_val = keyshops_value
                    price_source = "Keyshops"
            elif retail_value is not None:
                price_val = retail_value
                price_source = "Official store"
            elif keyshops_value is not None:
                price_val = keyshops_value
                price_source = "Keyshops"

            if not is_valid_price(price_val):
                rows.append((title, "N/A", None, None))
                continue

            currency = prices.get("currency") or ""
            currency_display = f" {currency}" if currency else ""
            price_text = f"${price_val:.2f}{currency_display}"
            if price_source == "Official store":
                price_text += " (official store cheapest)"
            rows.append((title, price_text, price_val, currency))

        numeric_values = [row[2] for row in rows if row[2] is not None]
        currencies = {row[3] for row in rows if row[2] is not None and row[3] is not None}
        total_text = None
        if numeric_values:
            if len(currencies) <= 1:
                total_value = sum(numeric_values)
                currency_label = (next(iter(currencies)) or "").strip()
                currency_suffix = f" {currency_label}" if currency_label else ""
                total_text = f"${total_value:.2f}{currency_suffix}"
            else:
                total_text = "(mixed currencies, total unavailable)"

        rows.sort(key=lambda row: (row[2] is None, row[2]))
        formatted_lines = [f"{title} — {price}" for title, price, _, _ in rows]
        if total_text:
            formatted_lines.extend(["", f"Total value: {total_text}"])
        description = "\n".join(formatted_lines)
        if len(description) > 4096:
            description = description[:4093] + "..."
        return discord.Embed(
            title="Deal list: lowest key prices",
            description=description or "No games were found.",
        )

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
                game_slug_title = (
                    steam_details["name"]
                    if steam_details and steam_details.get("name")
                    else gamename
                )
                deals_url = f"https://gg.deals/game/{_ggdeals_game_slug(game_slug_title)}/"

                if isinstance(ctx, _InteractionContext):
                    embed.add_field(
                        name="Check all deals in current shops",
                        value=f"[Clicking here]({deals_url})",
                        inline=False,
                    )
                else:
                    warning = (
                        "Buying from keyshops it may have risks type ``{prefix}risks`` for details."
                    ).format(prefix=ctx.clean_prefix)
                    embed.add_field(
                        name="Check all deals in current shops",
                        value=f"[Clicking here]({deals_url}) \n\n{warning}",
                        inline=False,
                    )
                # Add prices/fees at the bottom
                prices = api_game_data.get("prices", {})
                currency = prices.get("currency", "-")
                currency = f" {currency}" if currency != "-" else ""

                def valid_price(val):
                    return val not in (0, 0.0, "0", "0.0", "0.00", 0.00, None)

                current_retail = prices.get("currentRetail", "-")
                current_keyshops = prices.get("currentKeyshops", "-")

                def parse_price(val):
                    try:
                        return float(str(val).replace(",", "").strip())
                    except Exception:
                        return None

                retail_value = parse_price(current_retail)
                keyshops_value = parse_price(current_keyshops)

                if valid_price(current_retail):
                    embed.add_field(
                        name="Current Retail",
                        value=f"${current_retail}{currency}",
                        inline=True,
                    )

                if valid_price(current_keyshops):
                    embed.add_field(
                        name="Current Keyshops",
                        value=f"${current_keyshops}{currency}",
                        inline=True,
                    )

                if retail_value is not None or keyshops_value is not None:
                    if retail_value is not None and keyshops_value is not None:
                        if retail_value <= keyshops_value:
                            best_value = retail_value
                            best_name = "Official store"
                            note = "Official store is cheaper than keyshops."
                        else:
                            best_value = keyshops_value
                            best_name = "Keyshops"
                            note = "Keyshops are currently cheaper than the official store."
                    elif retail_value is not None:
                        best_value = retail_value
                        best_name = "Official store"
                        note = "Only official store pricing is available."
                    else:
                        best_value = keyshops_value
                        best_name = "Keyshops"
                        note = "Only keyshop pricing is available."

                    embed.add_field(
                        name="Best price",
                        value=f"${best_value:.2f}{currency} ({best_name})",
                        inline=True,
                    )
                    embed.add_field(
                        name="Note",
                        value=note,
                        inline=False,
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
                search_url = get_ggdeals_search_url(title)
                embed.description = (
                    "No deals found for this Steam App ID. "
                    f"Try searching by name on gg.deals: {search_url}"
                )

            await ctx.send(embed=embed)

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
        lines = raw.splitlines()
        items = []
        if len(lines) > 1:
            for ln in lines[1:]:
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("*"):
                    ln = ln.lstrip("*").strip()
                items.append(ln)
        else:
            parts = raw.split(None, 1)
            rest = parts[1].strip() if len(parts) > 1 else ""
            if rest:
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

        async with ctx.typing():
            steam_ids = []
            batch_size = 5
            batch_delay = 2.0
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                lookup_tasks = [get_steam_app_id_from_name(self.bot, title) for title in batch]
                try:
                    batch_ids = await asyncio.gather(*lookup_tasks)
                except Exception as e:
                    await ctx.send(f"Error while resolving games: {e}")
                    return
                steam_ids.extend(batch_ids)
                if i + batch_size < len(items):
                    await asyncio.sleep(batch_delay)

            title_to_steam = {title: sid for title, sid in zip(items, steam_ids)}
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

            def is_valid_price(val):
                return val not in (0, 0.0, "0", "0.0", "0.00", 0.00, None, "")

            rows = []
            data = api_result.get("data") if api_result else {}
            for title, sid in title_to_steam.items():
                if not sid:
                    rows.append((title, None, "NOT FOUND (no steam id)", None, None, "no_steam_id"))
                    continue
                api_game_data = None
                if data:
                    api_game_data = data.get(str(sid)) or data.get(int(sid))
                if not api_game_data:
                    rows.append((title, sid, "NO DEALS", None, None, "no_deals"))
                    continue
                prices = api_game_data.get("prices", {}) or {}
                retail_price = prices.get("currentRetail")
                keyshops_price = prices.get("currentKeyshops")

                def parse_price(val):
                    try:
                        return float(str(val).replace(",", "").strip())
                    except Exception:
                        return None

                retail_value = parse_price(retail_price)
                keyshops_value = parse_price(keyshops_price)
                price_val = None
                price_source = None
                if retail_value is not None and keyshops_value is not None:
                    if retail_value <= keyshops_value:
                        price_val = retail_value
                        price_source = "Official store"
                    else:
                        price_val = keyshops_value
                        price_source = "Keyshops"
                elif retail_value is not None:
                    price_val = retail_value
                    price_source = "Official store"
                elif keyshops_value is not None:
                    price_val = keyshops_value
                    price_source = "Keyshops"

                if not is_valid_price(price_val):
                    rows.append((title, sid, "N/A", None, None, "no_price_value"))
                else:
                    currency = prices.get("currency") or ""
                    currency_display = f" {currency}" if currency else ""
                    price_text = f"${price_val:.2f}{currency_display}"
                    if price_source == "Official store":
                        price_text += " (official store cheapest)"
                    rows.append((title, sid, price_text, price_val, currency, "ok"))

            numeric_values = [r[3] for r in rows if r[3] is not None]
            currencies = {r[4] for r in rows if r[3] is not None and r[4] is not None}
            total_text = None
            if numeric_values:
                if len(currencies) <= 1:
                    total_value = sum(numeric_values)
                    currency_label = (next(iter(currencies)) or "").strip()
                    currency_suffix = f" {currency_label}" if currency_label else ""
                    total_text = f"${total_value:.2f}{currency_suffix}"
                else:
                    total_text = "(mixed currencies, total unavailable)"

            rows.sort(key=lambda r: (r[3] is None, r[3]))
            names_only = [r[0] for r in rows]
            names_only_msg = "\n".join(f"- {name}" for name in names_only)

            csv_lines = ["title,appid,price"]
            for t, appid, p, _, _, _status in rows:
                safe_title = t.replace('"', '""')
                if "," in safe_title or "\n" in safe_title:
                    safe_title = f'"{safe_title}"'
                appid_cell = str(appid) if appid is not None else ""
                csv_lines.append(f"{safe_title},{appid_cell},{p}")
            if total_text:
                csv_lines.append(f"TOTAL,,{total_text}")

            csv_text = "\n".join(csv_lines)

            formatted_lines = [f"{t} — {p}" for t, _, p, _, _, _ in rows]
            if total_text:
                formatted_lines.append("")
                formatted_lines.append(f"Total value: {total_text}")
            formatted_msg = "\n".join(formatted_lines)

            embed = discord.Embed(title="Deal list: lowest key prices", description=formatted_msg)
            embed.set_footer(text="Prices obtained from https://gg.deals")
            await ctx.send("**Games sorted by lowest price:**\n```\n" + names_only_msg + "\n```")

        try:
            fp = io.BytesIO(csv_text.encode("utf-8"))
            fp.seek(0)
            file = discord.File(fp, filename="deals.csv")
            await ctx.send(embed=embed, file=file)
        except Exception:
            await ctx.send(formatted_msg)

    @commands.command()
    @commands.is_owner()
    async def deallist_debug(self, ctx):
        """Owner-only: resolve appids and fetch raw gg.deals API results for debugging."""
        raw = ctx.message.content or ""
        lines = raw.splitlines()
        items = []
        if len(lines) > 1:
            for ln in lines[1:]:
                ln = ln.strip()
                if not ln:
                    continue
                if ln.startswith("*"):
                    ln = ln.lstrip("*").strip()
                items.append(ln)
        else:
            parts = raw.split(None, 1)
            rest = parts[1].strip() if len(parts) > 1 else ""
            if rest:
                sep_found = False
                for sep in ["\n", ";", ",", "|"]:
                    if sep in rest:
                        items = [p.strip().lstrip("*").strip() for p in rest.split(sep) if p.strip()]
                        sep_found = True
                        break
                if not sep_found:
                    items = [rest]

        if not items:
            await ctx.send("No games found to debug. Put a list after the command.")
            return

        await ctx.send("Resolving Steam IDs (may take a moment)...")
        steam_ids = []
        batch_size = 5
        batch_delay = 1.0
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            lookup_tasks = [get_steam_app_id_from_name(self.bot, title) for title in batch]
            try:
                batch_ids = await asyncio.gather(*lookup_tasks)
            except Exception as e:
                await ctx.send(f"Error while resolving games: {e}")
                return
            steam_ids.extend(batch_ids)
            if i + batch_size < len(items):
                await asyncio.sleep(batch_delay)

        title_to_steam = {title: sid for title, sid in zip(items, steam_ids)}
        ids_to_query = [sid for sid in {sid for sid in steam_ids if sid}]

        api_result = None
        if ids_to_query:
            try:
                api_result = await get_ggdeals_api_prices_by_steamid(self.bot, ids_to_query)
            except Exception as e:
                await ctx.send(f"Error fetching gg.deals API: {e}")
                return

        report = {
            "title_to_steam": title_to_steam,
            "api_result": api_result,
        }

        fp = io.BytesIO(json.dumps(report, indent=2).encode("utf-8"))
        fp.seek(0)
        file = discord.File(fp, filename="deallist_debug.json")
        await ctx.send("Debug report:", file=file)

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

        try:
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            pass

        try:
            await ctx.author.send(embed=embed)
            dm_message = await ctx.send("ℹ️ Sent you a DM with the risks.")
            await dm_message.delete(delay=10)
        except discord.Forbidden:
            await ctx.send(
                "⚠️ I couldn't send you a DM. Please enable DMs from server members to receive the risks."
            )

    @commands.command()
    @commands.is_owner()
    async def clearcache(self, ctx):
        """Clear local gg.deals and Steam app list caches."""
        base = os.path.dirname(__file__)
        files = [os.path.join(base, "ggdeals_cache.json"), os.path.join(base, "steam_app_list.json")]
        removed = []
        for f in files:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    removed.append(os.path.basename(f))
            except Exception:
                pass
        if removed:
            await ctx.send(f"Removed cache files: {', '.join(removed)}")
        else:
            await ctx.send("No cache files found.")
