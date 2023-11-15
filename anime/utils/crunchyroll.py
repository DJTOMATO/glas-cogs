import logging
from typing import Any, Dict, List, Optional, Union

import aiohttp
from bs4 import BeautifulSoup

from ..utility import CRUNCHYROLL_NEWS_FEED_ENDPOINT

log = logging.getLogger("red.historian.anime")


class CrunchyrollException(Exception):
    """Base exception class for the Crunchyroll RSS feed parser."""


class CrunchyrollFeedError(CrunchyrollException):
    """Exception due to an error response from the Crunchyroll RSS feed."""

    def __init__(self, status: int) -> None:
        super().__init__(status)


class CrunchyrollClient:
    """Asynchronous parser client for the Crunchyroll RSS feed."""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Closes the aiohttp session."""
        if self.session is not None:
            await self.session.close()

    async def _session(self) -> aiohttp.ClientSession:
        """Gets an aiohttp session by creating it if it does not already exist or the previous session is closed."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(self, url: str) -> str:
        """Makes a request to the Crunchyroll RSS feed."""
        session = await self._session()
        response = await session.get(url)
        if response.status == 200:
            data = await response.text()
        else:
            raise CrunchyrollFeedError(response.status)
        return data

    @staticmethod
    async def _parse_feed(text: str, count: int) -> Union[List[Dict[str, Any]], None]:
        """Parses the feed and creates a dictionary for each entry."""
        soup = BeautifulSoup(text, "html.parser")
        items = soup.find_all("item")
        if items:
            data = []
            for item in items:
                if len(data) >= count:
                    break
                feed = {
                    "title": item.find("title").text,  # type: ignore
                    "author": item.find("author").text,  # type: ignore
                    "description": item.find("description").text,  # type: ignore
                    "date": item.find("pubdate").text,  # type: ignore
                    "link": item.find("guid").text,  # type: ignore
                }
                data.append(feed)
            return data
        return None

    async def news(self, count: int) -> Union[List[Dict[str, Any]], None]:
        """Gets a list of anime news."""
        text = await self._request(CRUNCHYROLL_NEWS_FEED_ENDPOINT)
        data = await self._parse_feed(text=text, count=count)
        if data:
            return data
        return None
