import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import logging
import discord
from PIL import Image, ImageDraw, ImageFont
import urllib.parse
import os
import time
import json


async def get_ggdeals_api_prices_by_steamid(bot, steam_app_ids, region=None):
    """
    Fetch price data from gg.deals API by Steam App ID(s) using Red shared API tokens.
    Uses a local file cache per-appid valid for up to 48 hours to avoid rate-limits.
    Returns a dict with a top-level `data` mapping of appid -> price data, and
    may include an `error` key when the remote call failed but cached data exists.
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

    # Cache settings
    TTL = 48 * 3600  # 48 hours
    cache_file = os.path.join(os.path.dirname(__file__), "ggdeals_cache.json")

    # Load existing cache (simple JSON file)
    try:
        with open(cache_file, "r", encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception:
        cache = {}

    now = time.time()
    result_data = {}
    # Decide which ids need fetching (strings for keys)
    requested_ids = [str(i) for i in steam_app_ids]
    ids_to_fetch = []
    for sid in requested_ids:
        entry = cache.get(sid)
        if entry and isinstance(entry, dict) and entry.get("ts") and now - entry.get("ts", 0) < TTL and entry.get("value") is not None:
            result_data[sid] = entry.get("value")
        else:
            ids_to_fetch.append(sid)

    # If anything to fetch from the API, do it (in one request)
    if ids_to_fetch:
        ids_param = ",".join(ids_to_fetch)
        url = f"https://api.gg.deals/v1/prices/by-steam-app-id/?ids={ids_param}&key={api_key}"
        if region:
            url += f"&region={region}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 429:
                        data = await resp.json()
                        err = f"Rate limit exceeded: {data.get('data', {}).get('message', 'Too Many Requests')}."
                        if result_data:
                            return {"error": err, "data": result_data}
                        return {"error": err}
                    if resp.status != 200:
                        err = f"API error: {resp.status} {resp.reason}"
                        if result_data:
                            return {"error": err, "data": result_data}
                        return {"error": err}
                    try:
                        data = await resp.json()
                    except Exception as e:
                        err = f"Failed to parse JSON: {e}"
                        if result_data:
                            return {"error": err, "data": result_data}
                        return {"error": err}

                    if not isinstance(data, dict):
                        err = "API did not return a dict response."
                        if result_data:
                            return {"error": err, "data": result_data}
                        return {"error": err}

                    api_data = data.get("data", {}) or {}
                    # Merge returned data into results and update cache entries individually
                    for appid, val in api_data.items():
                        sid = str(appid)
                        result_data[sid] = val
                        cache[sid] = {"ts": now, "value": val}
            except Exception as e:
                err = f"API request failed: {e}"
                if result_data:
                    return {"error": err, "data": result_data}
                return {"error": err}

    # Persist cache back to disk (best-effort)
    try:
        tmp = cache_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cache, fh)
        os.replace(tmp, cache_file)
    except Exception:
        pass

    return {"data": result_data}


def _normalize_steam_search_query(name):
    if not name:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    return normalized


STEAM_SEARCH_ALIAS_APP_IDS = {
    _normalize_steam_search_query("evil genius 2 deluxe edition"): 700600,
    _normalize_steam_search_query("evil genius 2 world domination deluxe edition"): 700600,
    _normalize_steam_search_query("starpoint gemini warlords gold pack"): 419480,
    _normalize_steam_search_query("starpoint gemini warlords gold pack bundle"): 419480,
    _normalize_steam_search_query("strange brigade deluxe edition"): 312670,
    _normalize_steam_search_query("world end economica episode 01"): 269250,
    _normalize_steam_search_query("world end economica episode.01"): 269250,
}


async def get_steam_app_id_from_name(bot, game_name):
    """
    Try to get the Steam App ID for a given game name using the Steam Storefront search API (undocumented, but used by the Steam website).
    Returns the appid as int, or None if not found.
    This is more accurate for user queries than local fuzzy matching.
    """
    import aiohttp
    import urllib.parse

    normalized_query = _normalize_steam_search_query(game_name)
    if normalized_query in STEAM_SEARCH_ALIAS_APP_IDS:
        return STEAM_SEARCH_ALIAS_APP_IDS[normalized_query]

    query = urllib.parse.quote(game_name)
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=en&cc=US"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    html_headers = headers.copy()
    html_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

    async with aiohttp.ClientSession(headers=headers) as session:
        # Try the JSON storesearch API with retries/backoff for transient 403/429
        api_items = None
        for attempt in range(3):
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except Exception:
                            data = None
                        if data:
                            api_items = data.get("items", [])
                        break
                    if resp.status in (403, 429):
                        await asyncio.sleep(1 + attempt)
                        continue
                    # non-retryable error
                    break
            except Exception:
                await asyncio.sleep(1 + attempt)
                continue

        if api_items:
            if api_items:
                for item in api_items:
                    if item.get("name", "").lower() == game_name.lower():
                        return item.get("id")
                return api_items[0].get("id")

        # Fallback to HTML search results when the API returns no useful items.
        fallback_url = f"https://store.steampowered.com/search/results?term={query}&l=english&cc=US"
        html_text = None
        for attempt in range(3):
            try:
                async with session.get(fallback_url, headers=html_headers) as resp:
                    if resp.status == 200:
                        html_text = await resp.text()
                        break
                    if resp.status in (403, 429):
                        await asyncio.sleep(1 + attempt)
                        continue
                    break
            except Exception:
                await asyncio.sleep(1 + attempt)
                continue

        if not html_text:
            return None

        soup = BeautifulSoup(html_text, "html.parser")
        rows = soup.select(".search_result_row")
        exact_match = None
        partial_match = None
        for row in rows:
            title_el = row.select_one(".title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue
            normalized_title = _normalize_steam_search_query(title)
            row_id = row.get("data-ds-appid") or row.get("data-ds-packageid")
            if not row_id:
                continue
            try:
                row_id = int(row_id)
            except ValueError:
                continue
            if normalized_title == normalized_query:
                exact_match = row_id
                break
            if normalized_query in normalized_title:
                partial_match = partial_match or row_id
        result = exact_match or partial_match
        if result:
            return result

        # As a last resort, try the large Steam app list (cached) for fuzzy matches
        apps = await _get_steam_app_list()
        if not apps:
            return None

        # Try exact normalized match first
        for a in apps:
            name = a.get("name") or ""
            if _normalize_steam_search_query(name) == normalized_query:
                try:
                    return int(a.get("appid"))
                except Exception:
                    continue

        # Then try partial matches (query contained in title)
        for a in apps:
            name = a.get("name") or ""
            if normalized_query in _normalize_steam_search_query(name):
                try:
                    return int(a.get("appid"))
                except Exception:
                    continue

        # Finally try reverse partial (title contained in query)
        for a in apps:
            name = a.get("name") or ""
            if _normalize_steam_search_query(name) in normalized_query:
                try:
                    return int(a.get("appid"))
                except Exception:
                    continue

        return None


async def _get_steam_app_list(cache_ttl=7 * 24 * 3600):
    """Download and cache the Steam app list (from ISteamApps/GetAppList) to speed up lookups.
    Returns a list of dicts with 'appid' and 'name'. Cache TTL default is 7 days.
    """
    cache_file = os.path.join(os.path.dirname(__file__), "steam_app_list.json")
    now = time.time()
    try:
        with open(cache_file, "r", encoding="utf-8") as fh:
            st = json.load(fh)
            if isinstance(st, dict) and st.get("ts") and now - st.get("ts") < cache_ttl and isinstance(st.get("apps"), list):
                return st.get("apps")
    except Exception:
        pass

    url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = resp.read()
            data = json.loads(raw.decode("utf-8", errors="replace"))
            apps = data.get("applist", {}).get("apps", [])
            # Persist cache
            try:
                with open(cache_file + ".tmp", "w", encoding="utf-8") as fh:
                    json.dump({"ts": now, "apps": apps}, fh)
                os.replace(cache_file + ".tmp", cache_file)
            except Exception:
                pass
            return apps
    except Exception:
        return []


    


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


def get_ggdeals_search_url(game_name):
    """Return a gg.deals search URL for the provided game name."""
    if not game_name:
        return "https://gg.deals/"
    return f"https://gg.deals/search/?q={urllib.parse.quote_plus(game_name)}"


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
