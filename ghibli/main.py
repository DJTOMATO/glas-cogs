import asyncio
import logging
import tempfile
import aiohttp
import os
from gradio_client import Client, handle_file
import discord

from redbot.core import Config, commands
from redbot.core.bot import Red
from PIL import Image
import imageio
log = logging.getLogger("glas-cogs.Ghibli")

superghibli_lock = asyncio.Lock()
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

    
    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user) 
    async def superghibli(self, ctx: commands.Context, user_or_url: str = None):
        """Apply the Ghibli transformation 5 times, showing progress as a GIF."""
        # Enforce only one command running at a time
        if superghibli_lock.locked():
            return await ctx.send("Someone else is using this command right now. Please wait for them to finish.")

        async with superghibli_lock:        
            user = None
            image_url = None
            attachment_url = None

            if ctx.message.attachments:
                for att in ctx.message.attachments:
                    if att.content_type and att.content_type.startswith("image"):
                        attachment_url = att.url
                        break

            if not attachment_url and user_or_url:
                try:
                    user = await commands.UserConverter().convert(ctx, user_or_url)
                except Exception:
                    if user_or_url.lower().startswith(("http://", "https://")):
                        image_url = user_or_url
                    else:
                        return await ctx.send("Invalid user or URL provided.")

            target = user or ctx.author
            avatar_url = attachment_url or image_url or target.display_avatar.url

            await ctx.send("Generating your Super Ghibli transformation... Please wait (this may take a bit)!")

            temp_paths = []

            async with ctx.typing():
                async with aiohttp.ClientSession() as session:
                    async with session.get(avatar_url) as resp:
                        if resp.status != 200:
                            return await ctx.send("Failed to download image.")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(await resp.read())
                            input_path = tmp.name
                            temp_paths.append(input_path)

                client = Client("abidlabs/EasyGhibli")
                current_path = input_path

                try:
                    for i in range(5):
                        result = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: client.predict(
                                spatial_img=handle_file(current_path),
                                api_name="/single_condition_generate_image",
                            ),
                        )
                        if not result or not os.path.exists(result):
                            return await ctx.send(f"Failed at transformation step {i + 1}.")

                        current_path = result
                        temp_paths.append(current_path)

                    final_image_path = current_path

                    # Create a GIF from all steps
                    gif_path = tempfile.NamedTemporaryFile(delete=False, suffix=".gif").name
                    frames = []
                    base_size = None

                    for path in temp_paths:
                        img = Image.open(path).convert("RGB")
                        if base_size is None:
                            base_size = img.size
                        else:
                            img = img.resize(base_size, Image.LANCZOS)
                        frames.append(img)
                    frames[0].save(
                        gif_path,
                        save_all=True,
                        append_images=frames[1:],
                        duration=1300,
                        loop=0,
                        format='GIF'
                    )

                except Exception as e:
                    return await ctx.send(f"Error during transformation: {e}")

                # Send the final image and gif
                await ctx.send(
                    content="Here's your final Super Ghibli transformation and the evolution GIF!",
                    files=[
                        discord.File(final_image_path, filename="superghibli_final.png"),
                        discord.File(gif_path, filename="superghibli_evolution.gif"),
                    ],
                )

                # Cleanup
                for path in temp_paths:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                try:
                    os.remove(gif_path)
                except Exception:
                    pass