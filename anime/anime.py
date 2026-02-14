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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Character)
            if embeds:
                if not ctx.channel.permissions_for(ctx.me).add_reactions:
                    return await ctx.send("I don't have add reactions permission to use menus.")
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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Staff)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                if not ctx.channel.permissions_for(ctx.me).add_reactions:
                    return await ctx.send("I don't have add reactions permission to use menus.")
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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
        async with ctx.channel.typing():
            embeds = await self.anilist_search(ctx, name, AniListSearchType.Studio)
            if embeds:
                if len(embeds) == 1:
                    return await ctx.send(embed=embeds[0])
                if not ctx.channel.permissions_for(ctx.me).add_reactions:
                    return await ctx.send("I don't have add reactions permission to use menus.")
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

    @commands.command(name="animerandom")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rnd(self, ctx: commands.Context, media: str, *, genre: str):
        """
        Displays a random anime or manga of the specified genre.
        """
        async with ctx.channel.typing():
            try:
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
            except Exception as e:
                self.logger.exception(e)
                embed = discord.Embed(
                    title="Error",
                    color=await ctx.embed_color(),
                    description=f"An error occurred while searching for a random {media.lower()} with the genre `{genre}`. Please check the genre name and try again.",
                )
                await ctx.channel.send(embed=embed)


    @commands.command(name="animenext")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _next(self, ctx: commands.Context):
        """
        Displays the next airing anime episodes.
        """
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
                if not ctx.channel.permissions_for(ctx.me).add_reactions:
                    return await ctx.send("I don't have add reactions permission to use menus.")
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

    @commands.command(name="anelast")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def last(self, ctx: commands.Context):
        """
        Displays the most recently aired anime episodes.
        """
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
                if not ctx.channel.permissions_for(ctx.me).add_reactions:
                    return await ctx.send("I don't have add reactions permission to use menus.")
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
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
        name="trending",
        aliases=["trend"],
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trending(self, ctx: commands.Context, media: str):
        """
        Displays the current trending anime or manga on AniList.
        """
        if not ctx.channel.permissions_for(ctx.me).embed_links:
            return await ctx.send("I don't have embed links permission to send an embed.")
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
