import re
from bs4 import BeautifulSoup
import aiohttp
import discord
from redbot.core import Config, commands


class Arca(commands.Cog):
    """Automatically embeds Arca.live post contents when links are shared."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=9876543210, force_registration=True
        )
        default_guild = {"enabled": True}
        self.config.register_guild(**default_guild)

    @commands.group()
    @commands.admin_or_permissions(manage_guild=True)
    async def arcaembed(self, ctx: commands.Context):
        """Manage Arca.live embedding settings."""
        if ctx.invoked_subcommand is None:
            current = await self.config.guild(ctx.guild).enabled()
            status = "enabled" if current else "disabled"
            await ctx.send(
                f"Arca.live auto-embedding is currently **{status}** in this server."
            )

    @arcaembed.command(name="toggle")
    async def arcaembed_toggle(self, ctx: commands.Context):
        """Toggle the auto-embed feature on or off for this server."""
        current = await self.config.guild(ctx.guild).enabled()
        new_state = not current
        await self.config.guild(ctx.guild).enabled.set(new_state)
        status = "enabled" if new_state else "disabled"
        await ctx.send(f"Arca.live auto-embedding has been **{status}**.")

    async def _fetch_arca_data(self, target_url: str):
        """Helper to fetch raw HTML and parse title and filtered images using BeautifulSoup."""
        proxy_url = f"https://r.jina.ai/{target_url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(proxy_url, timeout=15) as response:
                if response.status != 200:
                    return None, None, response.status, []
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Arca.live Post"

        # Look strictly inside div.fr-view.article-content.spoiler-filter if available, else fallback to article-body
        container = soup.find("div", class_="fr-view article-content spoiler-filter")
        if not container:
            container = soup.find("div", class_="article-body")

        all_images = []
        if container:
            for img in container.find_all("img"):
                src = img.get("src", "")
                if src.startswith("//"):
                    src = "https:" + src

                # Skip spoiler alert placeholder images
                if "spoiler-alert.png" in src:
                    continue

                if src and src not in all_images:
                    all_images.append(src)

        # Fallback regex search if soup parsing missed any markdown/direct links
        if not all_images:
            content_text = soup.get_text()
            img_matches = re.findall(r"\!\[.*?\]\((https?://[^\)]+)\)", html)
            for img in img_matches:
                if "spoiler-alert.png" not in img and img not in all_images:
                    all_images.append(img)

        return title, all_images, 200, soup

    @arcaembed.command(name="debug")
    @commands.is_owner()
    async def arcaembed_debug(self, ctx: commands.Context, target_url: str):
        """[Owner Only] Test scrape an Arca.live URL and show parsed title and filtered image URLs."""
        if "arca.live/b/" not in target_url:
            return await ctx.send("❌ Please provide a valid `arca.live/b/...` URL.")

        await ctx.typing()
        try:
            title, all_images, status_code, _ = await self._fetch_arca_data(target_url)
        except Exception as e:
            return await ctx.send(
                f"❌ Request failed with exception: `{type(e).__name__}: {e}`"
            )

        if status_code != 200:
            return await ctx.send(
                f"❌ Proxy reader returned HTTP Status Code: `{status_code}`"
            )

        # Select the 3rd image if available, otherwise first valid one
        image_url = None
        if len(all_images) >= 3:
            image_url = all_images[2]
        elif all_images:
            image_url = all_images[0]

        # Build debug response embed
        debug_embed = discord.Embed(
            title="🔍 ArcaEmbed Debug Results",
            color=discord.Color.blue(),
            url=target_url,
        )
        debug_embed.add_field(name="Proxy Status", value=str(status_code), inline=True)
        debug_embed.add_field(name="Extracted Title", value=f"`{title}`", inline=False)
        debug_embed.add_field(
            name="Selected Image URL (Target)",
            value=f"`{image_url}`" if image_url else "Not Found",
            inline=False,
        )

        await ctx.send(embed=debug_embed)

        # Send filtered images (up to 4 from spoiler-filter container)
        limited_images = all_images[:4]
        if limited_images:
            await ctx.send(
                f"📁 **Valid Filtered Image URLs ({len(limited_images)} shown, max 4):**"
            )
            for idx, img in enumerate(limited_images, start=1):
                await ctx.send(f"`{idx}.` {img}")
        else:
            await ctx.send(
                "📁 **Valid Filtered Image URLs:** None found or filtered out"
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not message.guild:
            return

        is_enabled = await self.config.guild(message.guild).enabled()
        if not is_enabled:
            return

        if "arca.live/b/" not in message.content:
            return

        words = message.content.split()
        target_url = None
        for word in words:
            if word.startswith("https://arca.live/b/") or word.startswith(
                "http://arca.live/b/"
            ):
                target_url = word
                break

        if not target_url:
            return

        try:
            title, all_images, status_code, _ = await self._fetch_arca_data(target_url)
            if status_code != 200:
                return
        except Exception:
            return

        image_url = None
        if len(all_images) >= 3:
            image_url = all_images[2]
        elif all_images:
            image_url = all_images[0]

        embed = discord.Embed(title=title, url=target_url, color=discord.Color.red())

        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(
            text="Arca.live",
            icon_url="https://play-lh.googleusercontent.com/i0GJqtGAaiq3BgfEhaA6wj-D8VtB6bUEX744X5zfntN5MxpBHca-Em6C512ASdRVwySXmMzo7qGzcD7j1tXJ",
        )

        try:
            await message.edit(suppress=True)
        except discord.HTTPException:
            pass

        await message.channel.send(embed=embed)
