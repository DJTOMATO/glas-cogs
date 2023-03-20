import asyncio
from email.mime import image
import functools
from io import BytesIO
from typing import Literal, Optional

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify
from redbot.core.data_manager import cog_data_path

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

from .converters import FuzzyMember

import moviepy
import moviepy.editor as mpe
from moviepy.editor import CompositeVideoClip, TextClip, VideoFileClip
from moviepy.editor import VideoFileClip


class Movietar(commands.Cog):
    """
    Make a not-funny video
    """

    __version__ = "1.0.0"

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
            image = await self.gen_vid(ctx, avatar)
            fp = cog_data_path(self) / f"clip.mp4"
            file = discord.File(str(fp), filename="clip.mp4")
            try:
                await ctx.send(files=[image])
            except Exception:
                log.error("Error sending Movietar video", exc_info=True)
                pass
            try:
                os.remove(image)
            except Exception:
                log.error("Error deleting Movietar video", exc_info=True)

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
        image_clip = mpe.ImageClip(member_avatar, duration=8).set_start(clip.duration)
        
        # clip = VideoFileClip("/clip.mp4")
        #masked_clip = clip.fx(mpe.vfx.mask_color, color=[0, 1, 0], s=3)
        final_clip = mpe.CompositeVideoClip([image_clip, clip]).set_duration(
            clip.duration
        ).set_pos(("0","0"))

        final_clip.write_videofile(f"{bundled_data_path(self)}/clip.mp4")
        video = mpe.VideoFileClip(f"{bundled_data_path(self)}/clip.mp4")
        image = member_avatar
        final = mpe.CompositeVideoClip([image, video.set_position("center")])
        final.write_videofile("test.mp4")
        return final
