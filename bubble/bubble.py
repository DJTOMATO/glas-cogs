import discord
import random
from datetime import datetime
from redbot.core import commands
import functools
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path


class BubbleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=["bubble"], cooldown_after_parsing=True)
    async def speech(self, ctx: commands.Context, member: discord.Member):
        """Make a Speech bubble..."""
        """Example: !bubble @User"""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
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

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def gen_pic(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 325)
        # base canvas
        im = Image.new("RGBA", (420, 610), None)

        cardmask = Image.open(f"{bundled_data_path(self)}/bubble.png", mode="r").convert("RGBA")
        # pasting the pfp
        im.paste(member_avatar, (51, 110), member_avatar)

        # ending
        cardmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "card.png")
        fp.close()
        return _file
