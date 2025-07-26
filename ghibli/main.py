import asyncio
import logging
import tempfile
import aiohttp
import os
from gradio_client import Client, handle_file
import discord

from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("glas-cogs.Ghibli")


class Ghibli(commands.Cog):
    """Ghibli Avatar Generator"""

    __author__ = "[Glas](https://github.com/djtomato/glas-cogs/)"
    __version__ = "0.0.2"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot

    @commands.command()
    async def ghibli(self, ctx: commands.Context, user_or_url: str = None):
        """Generate a Ghibli-style image from your avatar, a mentioned user's avatar, an image URL, or an attached image.\nUsage: [p]ghibli [user|image_url] or attach an image."""
        user = None
        image_url = None
        attachment_url = None
        # Check for image attachment
        if ctx.message.attachments:
            for att in ctx.message.attachments:
                if att.content_type and att.content_type.startswith("image"):
                    attachment_url = att.url
                    break
        # Try to resolve as user mention or ID
        if not attachment_url and user_or_url:
            try:
                user = await commands.UserConverter().convert(ctx, user_or_url)
            except Exception:
                if user_or_url.lower().startswith(
                    "http://"
                ) or user_or_url.lower().startswith("https://"):
                    image_url = user_or_url
                else:
                    return await ctx.send("Invalid user or URL provided.")
        target = user or ctx.author
        avatar_url = attachment_url or image_url or target.display_avatar.url
        await ctx.send("Generating your Ghibli-style image, please wait...")
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status != 200:
                        return await ctx.send("Failed to download image.")
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".png"
                    ) as tmp:
                        tmp.write(await resp.read())
                        tmp_path = tmp.name
            try:
                client = Client("abidlabs/EasyGhibli")
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.predict(
                        spatial_img=handle_file(tmp_path),
                        api_name="/single_condition_generate_image",
                    ),
                )
            except Exception as e:
                os.remove(tmp_path)
                return await ctx.send(f"API error: {e}")
            os.remove(tmp_path)
            # The result is the path to the generated image
            gen_path = result
            if not gen_path or not os.path.exists(gen_path):
                return await ctx.send("Failed to generate image.")
            await ctx.send(file=discord.File(gen_path, filename="ghibli.png"))

    async def cog_load(self) -> None:
        pass

    async def cog_unload(self) -> None:
        pass
