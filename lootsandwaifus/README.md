# LootAndWaifus Cog

A feature-rich [Red-DiscordBot](https://github.com/Cog-Creators/Red-DiscordBot) cog that fetches, caches, and displays character and item data from the [Loot and Waifus API](https://lootandwaifus.com/api/).

This cog provides comprehensive search functionality for multiple gacha games, complete with interactive embeds, automatic data caching, and fully automated multi-language translation.

## Features

- **Multi-Game Support:** Search for characters, artifacts, and runes across different games.
- **Interactive Disambiguation:** If a search matches multiple results, interactive numbered buttons will prompt the user to specify their choice.
- **On-the-fly Translation:** Dynamic API data (like skill descriptions, stats, and bios) is automatically translated in real-time using the Google Translate API. Translations are persistently cached to guarantee fast loading and avoid API rate limits.
- **Multi-Language Support (i18n):** Full support for English (🇬🇧), Spanish (🇪🇸), Japanese (🇯🇵), Chinese (🇨🇳), and Korean (🇰🇷). Language can be changed globally via bot locale, personally via command, or interactively via flag buttons on the embeds!
- **Fast Local Caching:** API data is stored in memory to prevent spamming the upstream API, ensuring instantaneous search results.

## Commands

- `[p]nikke <query>`
  Search for Goddess of Victory: NIKKE characters.
- `[p]trickcal <query>`
  Search for Trickcal Revive characters, artifacts, and runes.
- `[p]sxs <query>`
  Search for Sword x Staff data.
- `[p]mad <query>`
  Search for MAD characters.
- `[p]lwlang [language_code]`
  Set your personal preferred language for LootAndWaifus embeds (e.g., `es-ES`, `en-US`, `ja-JP`). Leave blank to clear your preference and default to the server's locale.
- `[p]lwrefresh` *(Bot Owner Only)*
  Force a manual refresh of the local API data cache from lootandwaifus.com.

## Installation

Assuming you have a working Redbot instance, you can install this cog by adding the repository and installing it:

```ini
[p]repo add glas-cogs https://github.com/djtomato/glas-cogs
[p]cog install glas-cogs lootandwaifus
[p]load lootandwaifus
```

## Under the Hood: Translation System

To maximize performance and avoid external dependency hell (like `googletrans`), this cog utilizes native asynchronous requests (`aiohttp`) to securely query the `clients5.google.com` translation endpoint (the same one used by the Google Chrome Extension). This ensures 100% native compatibility with Redbot's event loop, zero setup requirements, and total immunity to standard rate-limiting.

All translated strings are cached persistently in Redbot's Config, so the bot will only ever translate a unique string once.

## Credits
Data provided by the [Loot and Waifus API](https://lootandwaifus.com/).
