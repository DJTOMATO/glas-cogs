import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
import discord
from PIL import Image, ImageDraw, ImageFont


async def get_ggdeals_api_prices_by_steamid(bot, steam_app_ids, region=None):
    """
    Fetch price data from gg.deals API by Steam App ID(s) using Red shared API tokens.
    Returns a dict of {appid: price_data or None}.
    """
    api_tokens = await bot.get_shared_api_tokens("ggdeals")
    api_key = api_tokens.get("api_key")
    if not api_key:
        return {
            "error": "The gg.deals API key has not been set. Please set it with `[p]set api ggdeals api_key,<your_key>`\n If you need it, obtain it from https://gg.deals/settings/."
        }
    steamapi = await bot.get_shared_api_tokens("steam")
    api_key_steam = steamapi.get("api_key")
    if not api_key_steam:
        return {
            "error": "The Steam API key has not been set. Please set it with `[p]set api steam api_key,<your_key>`\n If you need it, obtain it from https://steamcommunity.com/dev/apikey."
        }

    ids = ",".join(str(i) for i in steam_app_ids)
    url = f"https://api.gg.deals/v1/prices/by-steam-app-id/?ids={ids}&key={api_key}"
    if region:
        url += f"&region={region}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    return {
                        "error": f"Rate limit exceeded: {data.get('data', {}).get('message', 'Too Many Requests')}."
                    }
                if resp.status != 200:
                    return {"error": f"API error: {resp.status} {resp.reason}"}
                # Always return a dict, even if data is missing
                try:
                    data = await resp.json()
                except Exception as e:
                    return {"error": f"Failed to parse JSON: {e}"}
                if not isinstance(data, dict):
                    return {"error": "API did not return a dict response."}
                return data
        except Exception as e:
            return {"error": f"API request failed: {e}"}


async def get_steam_app_id_from_name(bot, game_name):
    """
    Try to get the Steam App ID for a given game name using the Steam Storefront search API (undocumented, but used by the Steam website).
    Returns the appid as int, or None if not found.
    This is more accurate for user queries than local fuzzy matching.
    """
    import aiohttp
    import urllib.parse

    query = urllib.parse.quote(game_name)
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=en&cc=US"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            items = data.get("items", [])
            if not items:
                return None
            # Return the first result's appid
            return items[0].get("id")


async def get_steam_game_details(appid):
    """
    Fetch game details (image, description, genres, reviews, release date) from the Steam API.
    Returns a dict with the relevant info or None if not found.
    """
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            if not data or not data.get(str(appid), {}).get("success"):
                return None
            game_data = data[str(appid)]["data"]
            return {
                "image": game_data.get("header_image"),
                "description": game_data.get("short_description"),
                "genres": [g["description"] for g in game_data.get("genres", [])],
                "release_date": game_data.get("release_date", {}).get("date"),
                "reviews": game_data.get("recommendations", {}).get("total"),
                "name": game_data.get("name"),
            }


async def get_ggdeals_bundles_by_steam_app_id(bot, steam_app_ids, region=None):
    """
    Fetch bundle data from gg.deals API by Steam App ID(s) using Red shared API tokens.
    Returns a dict of {appid: bundle_data or None}.
    """
    api_tokens = await bot.get_shared_api_tokens("ggdeals")
    api_key = api_tokens.get("api_key")
    if not api_key:
        return {
            "error": "The gg.deals API key has not been set. Please set it with `[p]set api ggdeals api_key,<your_key>`\n If you need it, obtain it from https://gg.deals/settings/."
        }
    ids = ",".join(str(i) for i in steam_app_ids)
    url = f"https://api.gg.deals/v1/bundles/by-steam-app-id/?ids={ids}&key={api_key}"
    if region:
        url += f"&region={region}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 429:
                    data = await resp.json()
                    return {
                        "error": f"Rate limit exceeded: {data.get('data', {}).get('message', 'Too Many Requests')}."
                    }
                if resp.status != 200:
                    return {"error": f"API error: {resp.status} {resp.reason}"}
                try:
                    data = await resp.json()
                except Exception as e:
                    return {"error": f"Failed to parse JSON: {e}"}
                if not isinstance(data, dict):
                    return {"error": "API did not return a dict response."}
                return data
        except Exception as e:
            return {"error": f"API request failed: {e}"}
