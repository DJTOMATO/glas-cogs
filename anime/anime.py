import logging

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.vendored.discord.ext import menus

from .utility import (ANIMETHEMES_BASE_URL, AniListMediaType,
                      AniListSearchType, EmbedListMenu, is_adult)
from .utils import (AniListClient, AnimeNewsNetworkClient, CrunchyrollClient,
                    Finder)


class Anime(Finder, commands.Cog):
    """Search for anime, manga, characters and users using Anilist"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.anilist = AniListClient(session=self.session)
        self.logger = logging.getLogger("red.historian.anime")
        self.animenewsnetwork = AnimeNewsNetworkClient(session=self.session)
        self.crunchyroll = CrunchyrollClient(session=self.session)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.command(name="anime", aliases=["ani"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def anime(self, ctx: commands.Context, *, title: str):
        """
        Searches for an anime with the given title.
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, title, AniListSearchType.Anime)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The anime `{title}` could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="manga")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _manga_info(self, ctx: commands.Context, *, title: str):
        """
        Searches for a manga with the given title.
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, title, AniListSearchType.Manga)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The manga `{title}` could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(
        name="character",
        aliases=["char"],
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def character(self, ctx: commands.Context, *, name: str):
        """
        Searches for a character with the given name.
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Character)
            if embeds:
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The character `{name}` could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="anistaff")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def anistaff(self, ctx: commands.Context, *, name: str):
        """
        Searches for a staff with the given name and displays information about the search results such as description,
        staff roles, and character roles!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Staff)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The staff `{name}` could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="studio")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def studio_(self, ctx: commands.Context, *, name: str):
        """
        Searches for a studio with the given name and displays information about the search results such as the studio
        productions!
        """
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Studio)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The studio `{name}` could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="random")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rnd(self, ctx: commands.Context, media: str, *, genre: str):
        """
        Displays a random anime or manga of the specified genre.
        """
        async with ctx.channel.typing():
            if media.lower() == AniListMediaType.Anime.lower():
                embed = await self.anilist_random(
                    ctx,
                    genre,
                    AniListMediaType.Anime.upper(),
                    ["TV", "MOVIE", "OVA", "ONA", "TV_SHORT", "MUSIC", "SPECIAL"],
                )
                if not embed:
                    embed = discord.Embed(
                        title=f"An anime with the genre `{genre}` could not be found.",
                        color=await ctx.embed_color(),
                    )
                await ctx.channel.send(embed=embed)
            elif media.lower() == AniListMediaType.Manga.lower():
                embed = await self.anilist_random(
                    ctx,
                    genre,
                    AniListMediaType.Manga.upper(),
                    ["MANGA", "ONE_SHOT", "NOVEL"],
                )
                if not embed:
                    embed = discord.Embed(
                        title=f"A manga with the genre `{genre}` could not be found.",
                        color=await ctx.embed_color(),
                    )
                await ctx.channel.send(embed=embed)
            else:
                try:
                    ctx.command.reset_cooldown(ctx)
                except AttributeError:
                    pass
                raise commands.BadArgument(
                    f"{media} is not a valid media type. Choose one from anime/manga."
                )

    @commands.command(name="themes")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def themes(self, ctx: commands.Context, *, anime: str):
        """
        Searches for the openings and endings of the given anime and displays them.
        """
        async with ctx.channel.typing():
            try:
                async with self.session.get(
                    ANIMETHEMES_BASE_URL + "/search/",
                    params={
                      "q":anime, 
                      "include[anime]": "animethemes.animethemeentries.videos,animethemes.song.artists,images"
                    },
                    headers={
                      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
                    }
                ) as resp:
                    data = await resp.json()
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title="Error",
                    color=await ctx.embed_color(),
                    description=f"An error occurred while loading the embed for the theme.",
                )
                await ctx.send(embed=embed)
                return
            if data.get("search").get("anime"):
                embeds = []
                for page, entry in enumerate(data.get("search").get("anime")):
                    try:
                        embed = await self.get_themes_embed(
                            entry, page + 1, len(data.get("search").get("anime"))
                        )
                        if not isinstance(ctx.channel, discord.channel.DMChannel):
                            if (
                                is_adult(entry.get("animethemes")[0]["animethemeentries"][0])
                                and not ctx.channel.is_nsfw()
                            ):
                                embed = discord.Embed(
                                    title="Error",
                                    color=await ctx.embed_color(),
                                    description=f"Adult content. No NSFW channel.",
                                )
                                embed.set_footer(
                                    text=f"Provided by https://animethemes.moe/ • Page {page + 1}/"
                                    f'{len(data.get("search").get("anime"))}'
                                )
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the anime.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://animethemes.moe/ • Page "
                            f'{page + 1}/{len(data.get("search").get("anime"))}'
                        )
                    embeds.append(embed)
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"No themes for the anime `{anime}` found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="theme")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def theme(self, ctx: commands.Context, theme: str, *, anime: str):
        """
        Displays a specific opening or ending of the given anime.
        Theme could be ED or OP.
        """
        async with ctx.channel.typing():
            try:
                async with self.session.get(
                    ANIMETHEMES_BASE_URL + "/search/",
                    params={
                      "q":anime, 
                      "include[anime]": "animethemes.animethemeentries.videos,animethemes.song.artists,images"
                    },
                    headers={
                      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
                    }
                ) as resp:
                    data = await resp.json()
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title="Error",
                    color=await ctx.embed_color(),
                    description=f"An error occurred while loading the embed for the theme.",
                )
                await ctx.send(embed=embed)
                return
            if data.get("search").get("anime"):
                anime_ = data.get("search").get("anime")[0]
                for entry in anime_.get("animethemes"):
                    if (
                        theme.upper() == entry.get("slug")
                        or (theme.upper() == "OP" and entry.get("slug") == "OP1")
                        or (theme.upper() == "ED" and entry.get("slug") == "ED1")
                        or (theme.upper() == "OP1" and entry.get("slug") == "OP")
                        or (theme.upper() == "ED1" and entry.get("slug") == "ED")
                    ):
                        try:
                            embed = await self.get_theme_embed(anime_, entry)
                            if not isinstance(ctx.channel, discord.channel.DMChannel):
                                if (
                                    is_adult(entry.get("animethemeentries")[0])
                                    and not ctx.channel.is_nsfw()
                                ):
                                    embed = discord.Embed(
                                        title="Error",
                                        color=await ctx.embed_color(),
                                        description=f"Adult content. No NSFW channel.",
                                    )
                                    embed.set_footer(text=f"Provided by https://animethemes.moe/")
                                    return await ctx.channel.send(embed=embed)
                        except Exception as e:
                            self.logger.exception(e)
                            embed = discord.Embed(
                                title="Error",
                                color=await ctx.embed_color(),
                                description=f"An error occurred while loading the embed for the theme.",
                            )
                            embed.set_footer(text=f"Provided by https://animethemes.moe/")
                            return await ctx.channel.send(embed=embed)
                        return await ctx.channel.send(
                            content=f"https://animethemes.moe/video/{entry.get('animethemeentries')[0]['videos'][0]['basename']}",
                            embed=embed,
                        )
                embed = discord.Embed(
                    title=f"Cannot find `{theme.upper()}` for the anime `{anime}`.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"No theme for the anime `{anime}` found.", color=await ctx.embed_color()
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="next")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _next(self, ctx: commands.Context):
        """
        Displays the next airing anime episodes.
        """
        async with ctx.channel.typing():
            try:
                data = await self.anilist.schedule(
                    page=1, perPage=15, notYetAired=True, sort="TIME"
                )
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title=f"An error occurred while searching for the next airing episodes. Try again.",
                    color=await ctx.embed_color(),
                )
                return await ctx.channel.send(embed=embed)
            if data is not None and len(data) > 0:
                embeds = []
                for page, anime in enumerate(data):
                    try:
                        embed = await self.get_next_embed(anime, page + 1, len(data))  # type: ignore
                        if not isinstance(ctx.channel, discord.channel.DMChannel):
                            if (
                                is_adult(anime.get("media"))  # type: ignore
                                and not ctx.channel.is_nsfw()
                            ):
                                embed = discord.Embed(
                                    title="Error",
                                    color=await ctx.embed_color(),
                                    description=f"Adult content. No NSFW channel.",
                                )
                                embed.set_footer(
                                    text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                                )
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the next airing episode.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                        )
                    embeds.append(embed)
                if len(embeds) == 1:
                    return await ctx.channel.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The next airing episodes could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="last")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def last(self, ctx: commands.Context):
        """
        Displays the most recently aired anime episodes.
        """
        async with ctx.channel.typing():
            try:
                data = await self.anilist.schedule(
                    page=1, perPage=15, notYetAired=False, sort="TIME_DESC"
                )
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title=f"An error occurred while searching for the most recently aired episodes. Try again.",
                    color=await ctx.embed_color(),
                )
                return await ctx.channel.send(embed=embed)
            if data is not None and len(data) > 0:
                embeds = []
                for page, anime in enumerate(data):
                    try:
                        embed = await self.get_last_embed(anime, page + 1, len(data))  # type: ignore
                        if not isinstance(ctx.channel, discord.channel.DMChannel):
                            if (
                                is_adult(anime.get("media"))  # type: ignore
                                and not ctx.channel.is_nsfw()
                            ):
                                embed = discord.Embed(
                                    title="Error",
                                    color=await ctx.embed_color(),
                                    description=f"Adult content. No NSFW channel.",
                                )
                                embed.set_footer(
                                    text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                                )
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the recently aired episode.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                        )
                    embeds.append(embed)
                if len(embeds) == 1:
                    return await ctx.channel.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The most recently aired episodes could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(name="aninews")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def aninews(self, ctx: commands.Context):
        """
        Displays the latest anime news from Anime News Network.
        """
        async with ctx.channel.typing():
            try:
                data = await self.animenewsnetwork.news(count=15)
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title=f"An error occurred while searching for the Anime News Network news. Try again.",
                    color=await ctx.embed_color(),
                )
                return await ctx.channel.send(embed=embed)
            if data is not None and len(data) > 0:
                embeds = []
                for page, news in enumerate(data):
                    try:
                        embed = await self.get_aninews_embed(news, page + 1, len(data))
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the Anime News Network news.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://www.animenewsnetwork.com/ • Page {page + 1}/{len(data)}"
                        )
                    embeds.append(embed)
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The Anime News Network news could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(
        name="crunchynews",
        aliases=["crnews"],
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def crunchynews(self, ctx: commands.Context):
        """
        Displays the latest anime news from Crunchyroll.
        """
        async with ctx.channel.typing():
            try:
                data = await self.crunchyroll.news(count=15)
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title=f"An error occurred while searching for the Crunchyroll news. Try again.",
                    color=await ctx.embed_color(),
                )
                return await ctx.channel.send(embed=embed)
            if data is not None and len(data) > 0:
                embeds = []
                for page, news in enumerate(data):
                    try:
                        embed = await self.get_crunchynews_embed(news, page + 1, len(data))
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the Crunchyroll news.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://www.crunchyroll.com/ • Page {page + 1}/{len(data)}"
                        )
                    embeds.append(embed)
                if len(embeds) == 1:
                    return await ctx.channel.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"The Crunchyroll news could not be found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)

    @commands.command(
        name="trending",
        aliases=["trend"],
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trending(self, ctx: commands.Context, media: str):
        """
        Displays the current trending anime or manga on AniList.
        """
        async with ctx.channel.typing():
            if media.lower() == AniListMediaType.Anime.lower():
                type_ = AniListMediaType.Anime.upper()
            elif media.lower() == AniListMediaType.Manga.lower():
                type_ = AniListMediaType.Manga.upper()
            else:
                try:
                    ctx.command.reset_cooldown(ctx)
                except AttributeError:
                    pass
                raise commands.BadArgument(
                    f"{media} is not a valid media type. Choose one from anime/manga."
                )
            try:
                data = await self.anilist.trending(
                    page=1, perPage=10, type=type_, sort="TRENDING_DESC"
                )
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title=f"An error occurred while searching for the trending {type_.lower()}. "
                    f"Try again.",
                    color=await ctx.embed_color(),
                )
                return await ctx.channel.send(embed=embed)
            if data is not None and len(data) > 0:
                embeds = []
                for page, entry in enumerate(data):
                    try:
                        embed = await self.get_media_embed(entry, page + 1, len(data))  # type: ignore
                        if not isinstance(ctx.channel, discord.channel.DMChannel):
                            if is_adult(entry) and not ctx.channel.is_nsfw():  # type: ignore
                                embed = discord.Embed(
                                    title="Error",
                                    color=await ctx.embed_color(),
                                    description=f"Adult content. No NSFW channel.",
                                )
                                embed.set_footer(
                                    text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                                )
                    except Exception as e:
                        self.logger.exception(e)
                        embed = discord.Embed(
                            title="Error",
                            color=await ctx.embed_color(),
                            description=f"An error occurred while loading the embed for the "
                            f"{type_.lower()}.",
                        )
                        embed.set_footer(
                            text=f"Provided by https://anilist.co/ • Page {page + 1}/{len(data)}"
                        )
                    embeds.append(embed)
                if len(embeds) == 1:
                    return await ctx.channel.send(embed=embeds[0])
                menu = menus.MenuPages(
                    source=EmbedListMenu(embeds), clear_reactions_after=True, timeout=30
                )
                await menu.start(ctx)
            else:
                embed = discord.Embed(
                    title=f"No trending {type_.lower()} found.",
                    color=await ctx.embed_color(),
                )
                await ctx.channel.send(embed=embed)
