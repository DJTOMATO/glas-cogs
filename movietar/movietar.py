from .converters import FuzzyMember
import aiohttp
import discord
import asyncio
import moviepy
import moviepy.editor as mpe
import functools
from PIL import Image, ImageDraw, ImageFont
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify
from datetime import datetime
from redbot.core import commands
from moviepy.editor import VideoFileClip
from email.mime import image
from io import BytesIO
from typing import Literal, Optional


class Movietar(commands.Cog):
    """
    Make images from avatars!
    """

    __version__ = "1.1.1"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=82345678897346,
            force_registration=True,
        )
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["movie"], cooldown_after_parsing=True)
    async def movietar(self, ctx, *, member: FuzzyMember = None):
        """Makes a video with your avatar.."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_vid, ctx, avatar)
            image = await self.generate_image(ctx, task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    async def generate_image(self, ctx: commands.Context, task: functools.partial):
        task = self.bot.loop.run_in_executor(None, task)
        try:
            image = await asyncio.wait_for(task, timeout=60)
        except asyncio.TimeoutError:
            return "An error occurred while generating this image. Try again later."
        else:
            return image

    async def get_avatar(self, member: discord.User):
        avatar = BytesIO()
        await member.avatar_url_as(static_format="png").save(avatar, seek_begin=True)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.ANTIALIAS)
        return image

    def gen_vid(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 300)

        clip = VideoFileClip(f"{bundled_data_path(self)}/clip.mp4")
        # clip = VideoFileClip("/clip.mp4")
        masked_clip = clip.fx(mpe.vfx.mask_color, color=[0, 1, 0], s=3)
        final_clip = mpe.CompositeVideoClip([member_avatar, masked_clip]).set_duration(
            clip.duration
        )

        final_clip.write_videofile(f"{bundled_data_path(self)}/test.mp4")
        # final_clip.write_videofile("/test.mp4")
        video = mp.VideoFileClip(f"{bundled_data_path(self)}/test.mp4")
        # video = mp.VideoFileClip("/test.mp4")
        image = member_avatar

        final = mp.CompositeVideoClip([image, video.set_position("center")])
        # final.write_videofile("final.mp4")

        return final
