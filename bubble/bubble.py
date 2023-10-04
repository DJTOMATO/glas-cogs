import discord
import random
from datetime import datetime
from redbot.core import commands
import functools
import asyncio
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path
import aiohttp
from PIL import ImageChops
from aiohttp import ClientSession


class BubbleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def get_last_image_attachment(self, channel):
        async for message in channel.history(limit=10):  # Adjust the limit as needed
            for attachment in message.attachments:
                if any(
                    ext in attachment.filename.lower()
                    for ext in ("png", "jpg", "jpeg", "gif")
                ):
                    return attachment.url

            # Check for image URLs in message content
            for word in message.content.split():
                if word.startswith(("http://", "https://")):
                    # Check if the URL contains a recognized image file extension
                    if any(
                        ext in word.lower() for ext in ("png", "jpg", "jpeg", "gif")
                    ):
                        return word

            # Check for a message containing "!bubble" and an image attachment
            if "!bubble" in message.content.lower() and message.attachments:
                for attachment in message.attachments:
                    if any(
                        ext in attachment.filename.lower()
                        for ext in ("png", "jpg", "jpeg", "gif")
                    ):
                        return attachment.url

        return None

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=["bubble"], cooldown_after_parsing=True)
    async def speech(self, ctx: commands.Context, member: discord.Member = None):
        """Make a Speech bubble..."""
        """Example: !bubble @User"""

        if member:
            avatar = await self.get_avatar(member)
        else:
            # Get the last image attachment or URL with an image in the channel
            image_url = await self.get_last_image_attachment(ctx.channel)

            if not image_url:
                await ctx.send("No image found in the last relevant message.")
                return

            # Get the avatar from the image URL
            avatar = await self.get_avatar_from_url(image_url)

        async with ctx.typing():
            task = functools.partial(self.gen_pic, ctx, avatar)
            image = await self.generate_image(task)

        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    async def generate_image(self, task: functools.partial):
        task = self.bot.loop.run_in_executor(None, task)
        try:
            image = await asyncio.wait_for(task, timeout=60)
        except asyncio.TimeoutError:
            return "An error occurred while generating this image. Try again later."
        else:
            return image

    async def get_avatar(self, member: discord.abc.User):
        avatar = BytesIO()
        display_avatar: discord.Asset = member.display_avatar.replace(
            size=512, static_format="png"
        )
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    async def get_avatar_from_url(self, url: str):
        avatar = BytesIO()
        async with self.session.get(url) as response:
            if response.status != 200:
                raise commands.BadArgument("Invalid image URL.")
            avatar_bytes = await response.read()
            avatar.write(avatar_bytes)
            avatar.seek(0)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def gen_pic(self, ctx, avatar, image_url=None):
        # Load the bubble mask image
        with Image.open(f"{bundled_data_path(self)}/bubble_mask.png") as cardmask:
            cardmask = cardmask.convert("RGBA")

        if avatar is None:
            return "Member avatar not found."

        # Convert the avatar BytesIO object into a PIL.Image object
        with Image.open(avatar) as avatar_img:
            avatar_img = avatar_img.convert("RGBA")

            # Resize the bubble mask to match the size of the avatar image
            cardmask = cardmask.resize(avatar_img.size, Image.LANCZOS)

            # Create a new image with transparent background
            im = Image.new("RGBA", avatar_img.size, (0, 0, 0, 0))

            # Calculate the new position for the bubble mask
            mask_position = (0, -150)

            # Invert the bubble mask
            inverted_mask = ImageChops.invert(cardmask)

            # Apply the inverted bubble mask as a mask on the new image
            im.paste(avatar_img, (0, 0), mask=inverted_mask)

            # Save the final image to a file
            with BytesIO() as fp:
                im.save(fp, "GIF", save_all=True, append_images=[im], loop=0)
                fp.seek(0)

                # Create a Discord file object
                _file = discord.File(fp, "bubble.gif")

            return _file
