import datetime
import re
from abc import ABC
from html.parser import HTMLParser
from typing import Any, Dict

from redbot.vendored.discord.ext import menus

ANILIST_API_ENDPOINT = "https://graphql.anilist.co"

ANIMETHEMES_BASE_URL = "https://staging.animethemes.moe/api"

ANIMENEWSNETWORK_NEWS_FEED_ENDPOINT = "https://www.animenewsnetwork.com/newsroom/rss.xml"

CRUNCHYROLL_NEWS_FEED_ENDPOINT = "https://www.crunchyroll.com/newsrss?lang=enEN"


class HTMLFilter(HTMLParser, ABC):
    """
    A simple no deps HTML -> TEXT converter.
    thanks https://stackoverflow.com/a/55825140
    copy pasted from https://gist.github.com/ye/050e898fbacdede5a6155da5b3db078d
    """

    text = ""

    def handle_data(self, data):
        self.text += data


class AniListSearchType:
    Anime = "Anime"
    Manga = "Manga"
    Character = "Character"
    Staff = "Staff"
    Studio = "Studio"


class AniListMediaType:
    Anime = "Anime"
    Manga = "Manga"


class EmbedListMenu(menus.ListPageSource):
    """
    Paginated embed menu.
    """

    def __init__(self, embeds):
        """
        Initializes the EmbedListMenu.
        """
        super().__init__(embeds, per_page=1)

    async def format_page(self, menu, embeds):
        """
        Formats the page.
        """
        return embeds


def get_media_title(data: Dict[str, Any]) -> str:
    """
    Returns the media title.
    """
    if data.get("english") is None or data.get("english") == data.get("romaji"):
        return data.get("romaji")  # type: ignore
    else:
        return "{} ({})".format(data.get("romaji"), data.get("english"))


def get_media_stats(format_: str, type_: str, status: str, mean_score: int) -> str:
    """
    Returns the media stats.
    """
    anime_stats = []
    anime_type = "Type: " + format_media_type(format_) if format_ else "N/A"
    anime_stats.append(anime_type)
    anime_status = "N/A"
    if type_ == "ANIME":
        anime_status = "Status: " + format_anime_status(status)
    elif type_ == "MANGA":
        anime_status = "Status: " + format_manga_status(status)
    anime_stats.append(anime_status)
    anime_score = "Score: " + str(mean_score) if mean_score else "N/A"
    anime_stats.append(anime_score)
    return " | ".join(anime_stats)


def get_char_staff_name(data: Dict[str, Any]) -> str:
    """
    Returns the character/staff name.
    """
    if data.get("full") is None or data.get("full") == data.get("native"):
        name = data.get("native")
    else:
        if data.get("native") is None:
            name = data.get("full")
        else:
            name = "{} ({})".format(data.get("full"), data.get("native"))
    return name  # type: ignore


def format_media_type(media_type: str) -> str:
    """Formats the anilist media type."""
    MediaType = {
        "TV": "TV",
        "MOVIE": "Movie",
        "OVA": "OVA",
        "ONA": "ONA",
        "TV_SHORT": "TV Short",
        "MUSIC": "Music",
        "SPECIAL": "Special",
        "ONE_SHOT": "One Shot",
        "NOVEL": "Novel",
        "MANGA": "Manga",
    }
    return MediaType[media_type]


def format_anime_status(media_status: str) -> str:
    """Formats the anilist anime status."""
    AnimeStatus = {
        "FINISHED": "Finished",
        "RELEASING": "Currently Airing",
        "NOT_YET_RELEASED": "Not Yet Aired",
        "CANCELLED": "Cancelled",
    }
    return AnimeStatus[media_status]


def format_manga_status(media_status: str) -> str:
    """Formats the anilist manga status."""
    MangaStatus = {
        "FINISHED": "Finished",
        "RELEASING": "Publishing",
        "NOT_YET_RELEASED": "Not Yet Published",
        "CANCELLED": "Cancelled",
    }
    return MangaStatus[media_status]


def clean_html(raw_text) -> str:
    """Removes the html tags from a text."""
    clean = re.compile("<.*?>")
    clean_text = re.sub(clean, "", raw_text)
    return clean_text


def format_description(description: str, length: int) -> str:
    """Formats the anilist description."""
    description = clean_html(description)
    # Remove markdown
    description = description.replace("**", "").replace("__", "")
    # Replace spoiler tags
    description = description.replace("~!", "||").replace("!~", "||")
    if len(description) > length:
        description = description[0:length]
        spoiler_tag_count = description.count("||")
        if spoiler_tag_count % 2 != 0:
            return description + "...||"
        return description + "..."
    return description


def format_date(day: int, month: int, year: int) -> str:
    """Formats the anilist date."""
    month = datetime.date(1900, month, 1).strftime("%B")  # type: ignore
    date = f"{month} {str(day)}, {year}"
    return date


def is_adult(data: Dict[str, Any]) -> bool:
    """
    Checks if the media is intended only for 18+ adult audiences.
    """
    if data.get("isAdult") is True:
        return True
    if data.get("is_adult") is True:
        return True
    return data.get("nsfw") is True
