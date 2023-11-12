import logging
from typing import Any, Dict, List, Optional, Union

import aiohttp

from ..utility import ANILIST_API_ENDPOINT

log = logging.getLogger("red.historian.anime")


class AnilistException(Exception):
    """Base exception class for the Anilist API wrapper."""


class AnilistAPIError(AnilistException):
    """Exception due to an error response from the AniList API."""

    def __init__(self, msg: str, status: int, locations: List[Dict[str, Any]]) -> None:
        super().__init__(f"{msg} - Status: {str(status)} - Locations: {locations}")


class AniListClient:
    """Asynchronous wrapper client for the AniList API."""

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

    async def _request(self, query: str, **variables: Union[str, Any]) -> Dict[str, Any]:
        """Makes a request to the AniList API."""
        session = await self._session()
        response = await session.post(
            ANILIST_API_ENDPOINT, json={"query": query, "variables": variables}
        )
        data = await response.json()
        if data.get("errors"):
            raise AnilistAPIError(
                data.get("errors")[0]["message"],
                data.get("errors")[0]["status"],
                data.get("errors")[0].get("locations"),
            )
        return data

    async def media(self, **variables: Union[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """Gets a list of media entries based on the given search variables."""
        data = await self._request(query=Query.media(), **variables)
        if data.get("data")["Page"]["media"]:  # type: ignore
            return data.get("data")["Page"]["media"]  # type: ignore
        return None

    async def character(self, **variables: Union[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """Gets a list of characters based on the given search variables."""
        data = await self._request(query=Query.character(), **variables)
        if data.get("data")["Page"]["characters"]:  # type: ignore
            return data.get("data")["Page"]["characters"]  # type: ignore
        return None

    async def staff(self, **variables: Union[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """Gets a list of staff entries based on the given search variables."""
        data = await self._request(query=Query.staff(), **variables)
        if data.get("data")["Page"]["staff"]:  # type: ignore
            return data.get("data")["Page"]["staff"]  # type: ignore
        return None

    async def studio(self, **variables: Union[str, Any]) -> Union[List[Dict[str, Any]], None]:
        """Gets a list of studios based on the given search variables."""
        data = await self._request(query=Query.studio(), **variables)
        if data.get("data")["Page"]["studios"]:  # type: ignore
            return data.get("data")["Page"]["studios"]  # type: ignore
        return None

    async def genre(self, **variables: Union[str, Any]) -> Union[Dict[str, Any], None]:
        """Gets a dictionary with media entries based on the given genre."""
        data = await self._request(query=Query.genre(), **variables)
        if data:
            return data
        return None

    async def tag(self, **variables: Union[str, Any]) -> Union[Dict[str, Any], None]:
        """Gets a dictionary with media entries based on the given tag."""
        data = await self._request(query=Query.tag(), **variables)
        if data:
            return data
        return None

    async def user(self, **variables: Union[str, Any]) -> Union[Dict[str, Any], None]:
        """Gets a user based on the given search variables."""
        data = await self._request(query=Query.user(), **variables)
        if data.get("data")["Page"]["users"]:  # type: ignore
            return data.get("data")["Page"]["users"][0]  # type: ignore
        return None

    async def schedule(self, **variables: Union[str, Any]) -> Union[Dict[str, Any], None]:
        """Gets a airing schedule based on the given search variables."""
        data = await self._request(query=Query.schedule(), **variables)
        if data.get("data")["Page"]["airingSchedules"]:  # type: ignore
            return data.get("data")["Page"]["airingSchedules"]  # type: ignore
        return None

    async def trending(self, **variables: Union[str, Any]) -> Union[Dict[str, Any], None]:
        """Gets a list of trending media entries."""
        data = await self._request(query=Query.trending(), **variables)
        if data.get("data")["Page"]["media"]:  # type: ignore
            return data.get("data")["Page"]["media"]  # type: ignore
        return None


class Query:
    @classmethod
    def media(cls) -> str:
        MEDIA_QUERY: str = """
        query ($page: Int, $perPage: Int, $search: String, $type: MediaType) {
          Page(page: $page, perPage: $perPage) {
            media(search: $search, type: $type) {
              idMal
              title {
                romaji
                english
              }
              coverImage {
                large
                color
              }
              description
              bannerImage
              format
              status
              type
              meanScore
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              duration
              source
              episodes
              chapters
              volumes
              studios {
                nodes {
                  name
                }
              }
              synonyms
              genres
              trailer {
                id
                site
              }
              externalLinks {
                site
                url
              }
              siteUrl
              isAdult
              nextAiringEpisode {
                episode
                timeUntilAiring
                airingAt
              }
            }
          }
        }
        """
        return MEDIA_QUERY

    @classmethod
    def character(cls) -> str:
        CHARACTER_QUERY: str = """
        query ($page: Int, $perPage: Int, $search: String) {
          Page(page: $page, perPage: $perPage) {
            characters(search: $search) {
              name {
                full
                native
                alternative
              }
              image {
                large
              }
              description
              siteUrl
              media(perPage: 6) {
                nodes {
                  siteUrl
                  title {
                    romaji
                  }
                }
              }
            }
          }
        }
        """
        return CHARACTER_QUERY

    @classmethod
    def staff(cls) -> str:
        STAFF_QUERY: str = """
        query ($page: Int, $perPage: Int, $search: String) {
          Page(page: $page, perPage: $perPage) {
            staff(search: $search) {
              name {
                full
                native
              }
              language
              image {
                large
              }
              description
              siteUrl
              staffMedia(perPage: 6) {
                nodes {
                  siteUrl
                  title {
                    romaji
                  }
                }
              }
              characters(perPage: 6) {
                nodes {
                  id
                  siteUrl
                  name {
                    full
                  }
                }
              }
            }
          }
        }
        """
        return STAFF_QUERY

    @classmethod
    def studio(cls) -> str:
        STUDIO_QUERY: str = """
        query ($page: Int, $perPage: Int, $search: String) {
          Page(page: $page, perPage: $perPage) {
            studios(search: $search) {
              name
              media(sort: POPULARITY_DESC, perPage: 10, isMain: true) {
                nodes {
                  siteUrl
                  title {
                    romaji
                  }
                  format
                  episodes
                  coverImage {
                    large
                  }
                }
              }
              isAnimationStudio
              siteUrl
            }
          }
        }
        """
        return STUDIO_QUERY

    @classmethod
    def genre(cls) -> str:
        GENRE_QUERY: str = """
        query ($page: Int, $perPage: Int, $genre: String, $type: MediaType, $format_in: [MediaFormat]) {
          Page(page: $page, perPage: $perPage) {
            pageInfo {
              lastPage
            }
            media(genre: $genre, type: $type, format_in: $format_in) {
              idMal
              title {
                romaji
                english
              }
              coverImage {
                large
                color
              }
              description
              bannerImage
              format
              status
              type
              meanScore
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              duration
              source
              episodes
              chapters
              volumes
              studios {
                nodes {
                  name
                }
              }
              synonyms
              genres
              trailer {
                id
                site
              }
              externalLinks {
                site
                url
              }
              siteUrl
              isAdult
              nextAiringEpisode {
                episode
                timeUntilAiring
              }
            }
          }
        }
        """
        return GENRE_QUERY

    @classmethod
    def tag(cls) -> str:
        TAG_QUERY: str = """
        query ($page: Int, $perPage: Int, $tag: String, $type: MediaType, $format_in: [MediaFormat]) {
          Page(page: $page, perPage: $perPage) {
            pageInfo {
              lastPage
            }
            media(tag: $tag, type: $type, format_in: $format_in) {
              idMal
              title {
                romaji
                english
              }
              coverImage {
                large
                color
              }
              description
              bannerImage
              format
              status
              type
              meanScore
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              duration
              source
              episodes
              chapters
              volumes
              studios {
                nodes {
                  name
                }
              }
              synonyms
              genres
              trailer {
                id
                site
              }
              externalLinks {
                site
                url
              }
              siteUrl
              isAdult
              nextAiringEpisode {
                episode
                timeUntilAiring
              }
            }
          }
        }
        """
        return TAG_QUERY

    @classmethod
    def user(cls) -> str:
        USER_QUERY: str = """
        query ($page: Int, $perPage: Int, $name: String) {
          Page(page: $page, perPage: $perPage) {
            users(name: $name) {
              name
              avatar {
                large
                medium
              }
              about
              bannerImage
              statistics {
                anime {
                  count
                  meanScore
                  minutesWatched
                  episodesWatched
                }
                manga {
                  count
                  meanScore
                  chaptersRead
                  volumesRead
                }
              }
              favourites {
                anime {
                  nodes {
                    id
                    siteUrl
                    title {
                      romaji
                      english
                      native
                      userPreferred
                    }
                  }
                }
                manga {
                  nodes {
                    id
                    siteUrl
                    title {
                      romaji
                      english
                      native
                      userPreferred
                    }
                  }
                }
                characters {
                  nodes {
                    id
                    siteUrl
                    name {
                      first
                      last
                      full
                      native
                    }
                  }
                }
                staff {
                  nodes {
                    id
                    siteUrl
                    name {
                      first
                      last
                      full
                      native
                    }
                  }
                }
                studios {
                  nodes {
                    id
                    siteUrl
                    name
                  }
                }
              }
              siteUrl
            }
          }
        }
        """
        return USER_QUERY

    @classmethod
    def schedule(cls) -> str:
        SCHEDULE_QUERY: str = """
        query ($page: Int, $perPage: Int, $notYetAired: Boolean, $sort: [AiringSort]) {
          Page(page: $page, perPage: $perPage) {
            airingSchedules(notYetAired: $notYetAired, sort: $sort) {
              timeUntilAiring
              airingAt
              episode
              media {
                id
                idMal
                siteUrl
                title {
                  romaji
                  english
                }
                coverImage {
                  large
                }
                externalLinks {
                  site
                  url
                }
                duration
                format
                isAdult
                trailer {
                  id
                  site
                }
              }
            }
          }
        }
        """
        return SCHEDULE_QUERY

    @classmethod
    def trending(cls) -> str:
        TRENDING_QUERY: str = """
        query ($page: Int, $perPage: Int, $type: MediaType, $sort: [MediaSort]) {
          Page(page: $page, perPage: $perPage) {
            media(type: $type, sort: $sort) {
              idMal
              title {
                romaji
                english
              }
              coverImage {
                large
                color
              }
              description
              bannerImage
              format
              status
              type
              meanScore
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day
              }
              duration
              source
              episodes
              chapters
              volumes
              studios {
                nodes {
                  name
                }
              }
              synonyms
              genres
              trailer {
                id
                site
              }
              externalLinks {
                site
                url
              }
              siteUrl
              isAdult
              nextAiringEpisode {
                episode
                timeUntilAiring
              }
            }
          }
        }
        """
        return TRENDING_QUERY
