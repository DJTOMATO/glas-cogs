import asyncio
import functools
import json
import logging
import re
from datetime import datetime, timezone
from textwrap import shorten
from typing import Optional
from urllib.parse import quote_plus, urlencode

import aiohttp
import discord
import js2py
from bs4 import BeautifulSoup
from html2text import html2text as h2t
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, text_to_file
from redbot.vendored.discord.ext import menus

from .utils import ResultMenu, Source, get_card, get_query, nsfwcheck, s
from .yandex import Yandex
from ddgs import DDGS


logger = logging.getLogger("red.duckduckgo")

# TODO Add optional way to use from duckduckgo search api


class Duckduckgo(Yandex, commands.Cog):
    """
    A Simple duckduckgo search with image support as well
    """

    __version__ = "0.0.4"
    __authors__ = ["epic guy", "ow0x", "fixator10", "Glas"]

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.options = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        }
        self.link_regex = re.compile(
            r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*(?:\.png|\.jpe?g|\.gif))"
        )
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        authors = "Authors: " + ", ".join(self.__authors__)
        return f"{pre_processed}\n\n{authors}\nCog Version: {self.__version__}"

    @commands.group(invoke_without_command=True, aliases=["google"])
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def duckduckgo(self, ctx, *, query: Optional[str] = None):
        """duckduckgo search your query from Discord channel."""
        if not query:
            return await ctx.send("Please enter something to search")

        isnsfw = nsfwcheck(ctx)
        async with ctx.typing():
            response, kwargs = await self.get_result(query, nsfw=isnsfw)
            pages = []
            groups = [response[n : n + 3] for n in range(0, len(response), 3)]
            for num, group in enumerate(groups, 1):
                emb = discord.Embed(
                    title="duckduckgo Search: {}".format(
                        query[:44] + "\N{HORIZONTAL ELLIPSIS}" if len(query) > 45 else query
                    ),
                    color=await ctx.embed_color(),
                    url=kwargs["redir"],
                )
                for result in group:
                    desc = (f"{result.url}\n" if result.url else "") + f"{result.desc}"[:800]
                    emb.add_field(
                        name=f"{result.title}",
                        value=desc or "Nothing",
                        inline=False,
                    )
                emb.description = f"Page {num} of {len(groups)}"
                emb.set_footer(
                    text=f"Safe Search: {not isnsfw} | " + kwargs["stats"].replace("\n", " ")
                )
                if "thumbnail" in kwargs:
                    emb.set_thumbnail(url=kwargs["thumbnail"])

                if "image" in kwargs and num == 1:
                    emb.set_image(url=kwargs["image"])
                pages.append(emb)
        if pages:
            await ResultMenu(source=Source(pages, per_page=1)).start(ctx)
        else:
            await ctx.send("No results.")

    @duckduckgo.command()
    async def autofill(self, ctx, *, query: str):
        """Responds with a list of the duckduckgo Autofill results for a particular query."""

        params = {"client": "firefox", "hl": "en", "q": query}
        async with ctx.typing():
            # This “API” is a bit of a hack; it was only meant for use by
            # duckduckgo’s own products. and hence it is undocumented.
            # Attribution: https://shreyaschand.com/blog/2013/01/03/duckduckgo-autocomplete-api/
            base_url = "https://suggestqueries.duckduckgo.com/complete/search"
            try:
                async with self.session.get(base_url, params=params) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    data = json.loads(await response.read())
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if not data[1]:
                return await ctx.send("Could not find any results.")

            await ctx.send("\n".join(data[1]))

    @duckduckgo.command()
    async def doodle(self, ctx, month: Optional[int] = None, year: Optional[int] = None):
        """Responds with duckduckgo doodles of the current month.

        Or doodles of specific month/year if `month` and `year` values are provided.
        """
        month = month or datetime.now(timezone.utc).month
        year = year or datetime.now(timezone.utc).year

        async with ctx.typing():
            base_url = f"https://www.duckduckgo.com/doodles/json/{year}/{month}"
            try:
                async with self.session.get(base_url) as response:
                    if response.status != 200:
                        return await ctx.send(f"https://http.cat/{response.status}")
                    output = await response.json()
            except asyncio.TimeoutError:
                return await ctx.send("Operation timed out.")

            if not output:
                return await ctx.send("Could not find any results.")

            pages = []
            for data in output:
                em = discord.Embed(colour=await ctx.embed_color())
                em.title = data.get("title", "Doodle title missing")
                img_url = data.get("high_res_url")
                if img_url and not img_url.startswith("https:"):
                    img_url = "https:" + data.get("high_res_url")
                if not img_url:
                    img_url = "https:" + data.get("url")
                em.set_image(url=img_url)
                date = "-".join(str(x) for x in data.get("run_date_array")[::-1])
                em.set_footer(text=f"{data.get('share_text')}\nDoodle published on: {date}")
                pages.append(em)

        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        else:
            await ResultMenu(source=Source(pages, per_page=1)).start(ctx)

    @duckduckgo.command(aliases=["img"])
    async def image(self, ctx, *, query: Optional[str] = None):
        """Search duckduckgo images from discord"""
        if not query:
            await ctx.send("Please enter some image name to search")
        else:
            isnsfw = nsfwcheck(ctx)
            async with ctx.typing():
                response, kwargs = await self.get_result(query, images=True, nsfw=isnsfw)
                size = len(response)

                class ImgSource(menus.ListPageSource):
                    async def format_page(self, menu, page):
                        return (
                            discord.Embed(
                                title=f"Pages: {menu.current_page+1}/{size}",
                                color=await ctx.embed_color(),
                                description="Some images might not be visible.",
                                url=kwargs["redir"],
                            )
                            .set_image(url=page)
                            .set_footer(text=f"Safe Search: {not isnsfw}")
                        )

            if size > 0:
                await ResultMenu(source=ImgSource(response, per_page=1)).start(ctx)
            else:
                await ctx.send("No result")

    @duckduckgo.command(aliases=["rev"], enabled=True)
    async def reverse(self, ctx, *, url: Optional[str] = None):
        """Attach or paste the url of an image to reverse search, or reply to a message which has the image/embed with the image"""
        if query := get_query(ctx, url):
            pass
        else:
            return await ctx.send_help()

        encoded = {
            "rpt": "imageview",
            "url": query,
            "format": "json",
            "request": {
                "blocks": [
                    {"block": "extra-content", "params": {}, "version": 2},
                    {"block": "i-global__params:ajax", "params": {}, "version": 2},
                    {"block": "suggest2-history", "params": {}, "version": 2},
                    {"block": "cbir-intent__image-link", "params": {}, "version": 2},
                    {"block": "content_type_search-by-image", "params": {}, "version": 2},
                    {"block": "serp-controller", "params": {}, "version": 2},
                    {"block": "cookies_ajax", "params": {}, "version": 2},
                    {"block": "advanced-search-block", "params": {}, "version": 2},
                ],
                "metadata": {
                    "bundles": {"lb": "n?O/G?b*G$"},
                    "assets": {
                        "las": "justifier-height=1;thumb-underlay=1;justifier-setheight=1;fitimages-height=1;justifier-fitincuts=1;react-with-dom=1;720.0=1;616.0=1;6022a8.0=1;0e3c2c.0=1;464.0=1;da4144.0=1"
                    },
                    "version": "0x32f8444edac",
                    "extraContent": {"names": ["i-react-ajax-adapter"]},
                },
            },
        }

        async with ctx.typing():
            async with self.session.get(
                "https://yandex.com/images/search?" + urlencode(encoded),
                headers=self.options,
            ) as resp:
                text = await resp.read()
                redir_url = resp.url
            prep = functools.partial(self.yandex_reverse_search, text)
            result = await self.bot.loop.run_in_executor(None, prep)
            if result:
                result = json.loads(result)["tags"]
                emb = discord.Embed(
                    title="Yandex Reverse Image Search",
                    description=f"[`Cliek here to View in Browser`]({redir_url})\n",
                    color=await ctx.embed_color(),
                )
                emb.add_field(
                    name="Results",
                    value="\n".join(
                        map(lambda x: f"[{x['text']}]({'https://yandex.com'+x['url']})", result)
                    ),
                )
                emb.set_footer(text="Powered by Yandex")
                emb.set_thumbnail(url=query)
                await ctx.send(embed=emb)
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Yandex Reverse Image Search",
                        description="[`" + ("Nothing relevant found") + f"`]({redir_url})",
                        color=await ctx.embed_color(),
                    ).set_thumbnail(url=query)
                )

    @commands.is_owner()
    @duckduckgo.command(hidden=True)
    async def debug(self, ctx, url: str):
        async with self.session.get(url, headers=self.options) as resp:
            text = await resp.text()
        raw_html = BeautifulSoup(text, "html.parser")
        data = raw_html.prettify()
        await ctx.send(file=text_to_file(data, filename="duckduckgo_debug.html"))

    async def get_result(self, query, images=False, nsfw=False):
        """Fetch the data"""
        ddgs = DDGS()
        safesearch = 'off' if nsfw else 'moderate'
        if images:
            results = ddgs.images(query, safesearch=safesearch)
            fin = [r['image'] for r in results[:20]]  # limit to 20
            kwargs = {}
        else:
            results = ddgs.text(query, safesearch=safesearch)
            fin = [s(r['href'], r['title'], r['body']) for r in results]
            kwargs = {"stats": f"About {len(results)} results"}
        redir = f"https://duckduckgo.com/?q={quote_plus(query)}"
        kwargs["redir"] = redir
        return fin, kwargs

    def yandex_reverse_search(self, text):
        soup = BeautifulSoup(text, features="html.parser")
        if sidebar := soup.find(
            "div",
            class_="cbir-search-by-image-page__section cbir-search-by-image-page__section_name_tags",
        ):
            if check := sidebar.find("div", {"data-state": True}):
                return check["data-state"]
