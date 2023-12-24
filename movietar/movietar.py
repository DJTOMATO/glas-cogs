import asyncio
from email.mime import image
import functools
from io import BytesIO
from typing import Literal, Optional
import logging
import tempfile
import pathlib
from moviepy.editor import ImageClip
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify
from redbot.core.data_manager import cog_data_path
import moviepy.editor
from concurrent.futures import ThreadPoolExecutor

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]
import io
from .converters import FuzzyMember
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip
from moviepy.video.fx import all as vfx  # Import all video effects
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.all import resize, mask_color
from moviepy.video.VideoClip import ImageClip
from threading import Thread

logging.captureWarnings(False)
log = logging.getLogger("red.glas-cogs.movietar")


class Movietar(commands.Cog):
    """
    Make trash videos with your avatar
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=82345678897346,
            force_registration=True,
        )
        self.log = logging.getLogger("red.glas-cogs.movietar")
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["crimee"], cooldown_after_parsing=True)
    async def crimenes(self, ctx, *, member: FuzzyMember = None):
        """Se busca urgentemente.."""
        if not member:
            member = ctx.author
        videotype = "crimes.mp4"
        pos = (0, 147)
        avisize = (300, 300)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="crimenes.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["cuatrok"], cooldown_after_parsing=True)
    async def fourk(self, ctx, *, member: FuzzyMember = None):
        """Caught in 4k.."""
        if not member:
            member = ctx.author
        videotype = "4k.mp4"
        pos = (30, 20)
        avisize = (150, 150)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="4k.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["powa"], cooldown_after_parsing=True)
    async def heman(self, ctx, *, member: FuzzyMember = None):
        """I've got the power.."""
        if not member:
            member = ctx.author
        videotype = "heman.mp4"
        pos = (200, 20)
        avisize = (150, 150)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="heman.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["lis"], cooldown_after_parsing=True)
    async def blame(self, ctx, *, member: FuzzyMember = None):
        """I've gotta blame somebody.."""
        if not member:
            member = ctx.author
        videotype = "blame.mp4"
        pos = (210, 40)
        avisize = (150, 150)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="blame.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["finsupp"], cooldown_after_parsing=True)
    async def bernie(self, ctx, *, member: FuzzyMember = None):
        """Financial Support.."""
        if not member:
            member = ctx.author
        videotype = "bernie.mp4"
        pos = (170, 85)
        avisize = (190, 190)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="bernie.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["conss"], cooldown_after_parsing=True)
    async def cons(self, ctx, *, member: FuzzyMember = None):
        """There are consequences.."""
        if not member:
            member = ctx.author
        videotype = "cons.mp4"
        pos = (175, 35)
        avisize = (185, 185)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="cons.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["afeeling"], cooldown_after_parsing=True)
    async def feeling(self, ctx, *, member: FuzzyMember = None):
        """We're talking about facts.."""
        if not member:
            member = ctx.author
        videotype = "facts.mp4"
        pos = (155, 30)
        avisize = (180, 180)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="facts.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["nooooo"], cooldown_after_parsing=True)
    async def nogod(self, ctx, *, member: FuzzyMember = None):
        """No god please.."""
        if not member:
            member = ctx.author
        videotype = "nogod.mp4"
        pos = (90, 15)
        avisize = (250, 250)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="nogod.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["whatplace"], cooldown_after_parsing=True)
    async def place(self, ctx, *, member: FuzzyMember = None):
        """What has this place become.."""
        if not member:
            member = ctx.author
        videotype = "place.mp4"
        pos = (215, 210)
        avisize = (170, 170)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="place.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["mikes"], cooldown_after_parsing=True)
    async def mike(self, ctx, *, member: FuzzyMember = None):
        """MM eating mike's.."""
        if not member:
            member = ctx.author
        videotype = "mike.mp4"
        pos = (80, 60)
        avisize = (190, 190)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="mike.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["harina"], cooldown_after_parsing=True)
    async def flour(self, ctx, *, member: FuzzyMember = None):
        """Just flour.."""
        if not member:
            member = ctx.author
        videotype = "flour.mp4"
        pos = (150, 0)
        avisize = (185, 185)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="flour.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["wtff"], cooldown_after_parsing=True)
    async def wtf(self, ctx, *, member: FuzzyMember = None):
        """Korone..."""
        if not member:
            member = ctx.author
        videotype = "wtf.mp4"
        pos = (5, 30)
        avisize = (200, 200)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="wtf.mp4")
                await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(aliases=["chuhh"], cooldown_after_parsing=True)
    async def chuh(self, ctx, *, member: FuzzyMember = None):
        """chuh..."""
        if not member:
            member = ctx.author
        videotype = "huh.mp4"
        pos = (0, 0)
        avisize = (640, 360)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(tmpdirname)
                file = folder / f"{ctx.message.id}final.mp4"
                image = await self.gen_vidgs(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )
                file = discord.File(file, filename="huh.mp4")
            await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command(aliases=["herewego"], cooldown_after_parsing=True)
    async def awshit(self, ctx, *, member: FuzzyMember = None):
        """CJ....."""
        if not member:
            member = ctx.author
        videotype = "awshit.mp4"
        pos = (0, 0)
        avisize = (640, 360)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(tmpdirname)
                file = folder / f"{ctx.message.id}final.mp4"

                image = await self.gen_vidas(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )
                file = discord.File(file, filename="aws.mp4")
            await ctx.send(file=file)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["lolazo"], cooldown_after_parsing=True)
    async def lold(self, ctx, *, member: FuzzyMember = None):
        """Lol'd at you..."""
        if not member:
            member = ctx.author
        videotype = "mlol.mp4"
        pos = (23, 15)
        avisize = (100, 100)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vidt(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="lold.mp4")
                await ctx.send(file=file)


    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["lalone"], cooldown_after_parsing=True)
    async def akira(self, ctx, *, member: FuzzyMember = None):
        """leave me alone at you..."""
        if not member:
            member = ctx.author
        videotype = "akira.mp4"
        pos = (0, 0)
        avisize = (100, 100)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            with tempfile.TemporaryDirectory() as tmpdirname:
                folder = pathlib.Path(
                    tmpdirname
                )  # cant tell if it returns a string or a path object
                file = folder / f"{ctx.message.id}final.mp4"
                image = self.gen_vid_akira(
                    ctx, avatar, file, folder, videotype, pos, avisize
                )  # just generates the video
                file = discord.File(file, filename="akira.mp4")
                await ctx.send(file=file)


    # ads
    async def generate_image(self, ctx: commands.Context, task: functools.partial):
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
            size=1024, static_format="png"
        )
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.Resampling.LANCZOS)
        return image

    def gen_vid(self, ctx, member_avatar, fp, folder, videotype, pos, avisize):
        member_avatar = self.bytes_to_image(member_avatar, 300)
        clip = VideoFileClip(f"{bundled_data_path(self) / videotype}")
        clip = clip.volumex(1.0)
        numpydata = np.asarray(member_avatar)
        cat = (
            ImageClip(numpydata)
            .set_duration(clip.duration)
            .resize((avisize))
            .set_position((pos))
        )
        clip = CompositeVideoClip([clip, cat])
        data = clip.write_videofile(
            str(fp),
            threads=1,
            preset="superfast",
            verbose=False,
            logger=None,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(folder / f"{ctx.message.id}finals.mp4")
            # ffmpeg_params=['-struct -2'],
        )
        path = fp
        return data

    async def gen_vidgs(self, ctx, member_avatar, fp, folder, videotype, pos, avisize):
        # Define a function for video processing

        def process_video(member_avatar, fp, folder):
            ayylmao = "huh.mp4"
            video_path = bundled_data_path(self) / ayylmao
            video = VideoFileClip(str(video_path))
            video = video.set_duration(10)
            # Resize video to 600x600
            video = video.resize(height=400)
            image = Image.open(member_avatar)

            # Resize Avatar
            member_avatar = self.bytes_to_image(member_avatar, 600)
            image_array = np.array(member_avatar)
            image_clip = (
                ImageClip(image_array, transparent=False)
                .set_start(0)
                .set_position(("center", "center"))
            )
            image_clip = image_clip.set_duration(10)

            # Create a color mask based on green color
            mask_color_value = [2, 195, 10]
            mask_threshold = 100
            mask_s = 3

            # Apply the color mask to the video clip
            masked_clip = video.fx(resize, height=400).fx(
                mask_color, color=mask_color_value, thr=mask_threshold, s=mask_s
            )

            # Set the position
            masked_clip = masked_clip.set_position((-500, 0), relative=False)

            # Composite the clips
            final_clip = CompositeVideoClip([image_clip, masked_clip.set_duration(10)])

            # Write the final result to a file
            final_clip.write_videofile(
                str(fp),
                threads=8,
                preset="superfast",
                verbose=False,
                logger=None,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(folder / f"{ctx.message.id}finals.mp4"),
            )

        # Use a ThreadPoolExecutor to run the process_video function
        with ThreadPoolExecutor() as executor:
            await ctx.bot.loop.run_in_executor(
                executor, process_video, member_avatar, fp, folder
            )

        return fp

    async def gen_vidas(self, ctx, member_avatar, fp, folder, videotype, pos, avisize):
        # Define a function for video processing

        def process_video(member_avatar, fp, folder):
            # Video
            ayylmao = "awshit.mp4"
            video_path = bundled_data_path(self) / ayylmao
            video = VideoFileClip(str(video_path))
            video = video.set_duration(2.72)
            video = video.resize(height=400)
            image = Image.open(member_avatar)

            # Resize Avatar
            member_avatar = self.bytes_to_image(member_avatar, 600)
            member_avatar = member_avatar.convert("RGB")
            image_array = np.array(member_avatar)
            image_clip = (
                ImageClip(image_array).set_start(0).set_pos(("center", "center"))
            )
            image_clip = image_clip.set_duration(2.72)

            def chroma_key(video_path, color=[0, 255, 0], thr=1, s=1):
                video = video_path

                # Create a mask based on the specified color
                mask = vfx.mask_color(video, color=color, thr=thr, s=s)

                # Apply the mask to the video
                masked_video = CompositeVideoClip(
                    [video.set_position("center"), mask.set_position("center")]
                )

                # Set the duration to match the original video
                masked_video = masked_video.set_duration(video.duration)

                # Write the final result to a file
                return masked_video

            # final_clip = CompositeVideoClip(
            #     [
            #         image_clip,
            #         masked_clip,
            #     ]
            # )
            final_clip = chroma_key(video)
            # Write the final result to a file
            final_clip.write_videofile(
                str(fp),
                threads=8,
                preset="superfast",
                verbose=False,
                logger=None,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(folder / f"{ctx.message.id}finals.mp4"),
            )

        # Use a ThreadPoolExecutor to run the process_video function
        with ThreadPoolExecutor() as executor:
            await ctx.bot.loop.run_in_executor(
                executor, process_video, member_avatar, fp, folder
            )

        return fp

    def gen_vidt(self, ctx, member_avatar, fp, folder, videotype, pos, avisize):
        member_avatar = self.bytes_to_image(member_avatar, 300)
        clip = VideoFileClip(f"{bundled_data_path(self) / videotype}")
        duration = clip.duration

        clip = clip.volumex(1.0)
        pos = (40, 20)
        numpydata = np.asarray(member_avatar)
        cat = (
            ImageClip(numpydata)
            .set_start(0)
            .set_duration(7.2)
            .resize((avisize))
            .set_position((pos))
        )
        clip = CompositeVideoClip([clip, cat])
        avisize = (150, 150)
        pos = (0, 0)
        cat2 = (
            ImageClip(numpydata)
            .set_start(12)
            .set_duration(3.3)
            .resize((avisize))
            .set_position((pos))
        )

        clip = CompositeVideoClip([clip, cat2])

        data = clip.write_videofile(
            str(fp),
            threads=1,
            preset="superfast",
            verbose=False,
            logger=None,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(folder / f"{ctx.message.id}finals.mp4")
            # ffmpeg_params=['-struct -2'],
        )
        path = fp
        return data

    def gen_vid_akira(self, ctx, member_avatar, fp, folder, videotype, pos, avisize):
        member_avatar = self.bytes_to_image(member_avatar, 360)
        clip = VideoFileClip(f"{bundled_data_path(self) / videotype}")
        duration = clip.duration
        avisize = (640, 360)
        clip = clip.volumex(1.0)
        pos = (0, 0)
        numpydata = np.asarray(member_avatar)
        cat = (
            ImageClip(numpydata)
            .set_start(2.83)
            .set_duration(0.76)
            .resize((avisize))
            .set_position((pos))
        )
        clip = CompositeVideoClip([clip, cat])
        avisize = (640, 360)
        pos = (0, 0)
                # Apply a burn effect
        enhancer = ImageEnhance.Contrast(member_avatar)
        burned_image = enhancer.enhance(0.5)  # Reduce contrast to simulate burn

        # Apply additional effects for a more damaged look
        burned_image = burned_image.filter(ImageFilter.GaussianBlur(radius=5))
        burned_image = burned_image.convert("RGB")

        numpydata2 = np.asarray(burned_image)
        cat2 = (
            ImageClip(numpydata2)
            .set_start(5.2)
            .set_duration(0.52)
            .resize((avisize))
            .set_position((pos))
        )

        clip = CompositeVideoClip([clip, cat2])

        data = clip.write_videofile(
            str(fp),
            threads=1,
            preset="superfast",
            verbose=False,
            logger=None,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=str(folder / f"{ctx.message.id}finals.mp4")
            # ffmpeg_params=['-struct -2'],
        )
        path = fp
        return data
