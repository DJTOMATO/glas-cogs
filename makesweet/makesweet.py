import discord
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess
import io
from io import BytesIO
import tempfile
from .converters import FuzzyMember
import pathlib
from redbot.core.data_manager import bundled_data_path
from redbot.core.data_manager import cog_data_path
from redbot.core import commands, data_manager

import shutil
import asyncio


class MakeSweet(commands.Cog):
    """MakeSweet Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()

    async def generate_image(self, ctx, zip_template, user, gif_output):

        # If Heartlocked is used, create the text to be used as second image
        if "heart-locket.zip" in zip_template:
            text_image = self.create_text_image(f"    {user.name} \n   my beloved")
            temp_text_dir = data_manager.cog_data_path(self) / "text_images"
            temp_text_dir.mkdir(
                parents=True, exist_ok=True
            )  # Create the directory if it doesn't exist

            temp_text_path = temp_text_dir / f"text_{user.id}.png"
            text_image.save(temp_text_path, "PNG")

        if user.avatar.is_animated():
            avatar_format = "gif"
            # Create a temporary directory for the avatar frames
            temp_avatar_dir = data_manager.cog_data_path(self) / "avatars"
            temp_avatar_dir.mkdir(
                parents=True, exist_ok=True
            )  # Create the directory if it doesn't exist

            temp_avatar_path = str(temp_avatar_dir / f"avatar_{user.id}.png")

            avatar_data = await user.avatar.read()
            with open(temp_avatar_path, "wb") as temp_avatar:
                temp_avatar.write(avatar_data)

            # Use PIL to open the animated avatar and extract the first frame as an image
            animated_avatar = Image.open(temp_avatar_path)
            first_frame = animated_avatar.convert("RGBA").copy()

            # Save the first frame as a static image (PNG)
            first_frame_path = temp_avatar_dir / f"avatar_{user.id}.png"
            first_frame.save(first_frame_path)
            # Now, use the saved animated avatar with text for generating the animation
            reanimator_command = [
                f"{data_manager.bundled_data_path(self)}/reanimator",
                "--zip",
                zip_template,
                "--in",
                str(first_frame_path),  # Use the animated avatar with text
                "--gif",
                str(gif_output),  # Convert the Path to a string
            ]
        else:
            # For static avatars, use the original avatar data
            avatar_format = "png"
            user_id = str(user.id)
            temp_avatar_dir = data_manager.cog_data_path(self) / "avatars"
            temp_avatar_path = str(temp_avatar_dir / f"avatar_{user.id}.png")
            avatar_data = await user.avatar.read()
            with open(temp_avatar_path, "wb") as temp_avatar:
                temp_avatar.write(avatar_data)

        if "heart-locket.zip" in zip_template:
            reanimator_command = [
                f"{data_manager.bundled_data_path(self)}/reanimator",
                "--zip",
                zip_template,
                "--in",
                temp_avatar_path,
                temp_text_path,  # Include the text image path
                "--gif",
                str(gif_output),  # Convert the Path to a string
            ]
        elif "nesting-doll.zip" in zip_template:
            reanimator_command = [
                f"{data_manager.bundled_data_path(self)}/reanimator",
                "--zip",
                zip_template,
                "--in",
                temp_avatar_path,
                temp_avatar_path,
                temp_avatar_path,
                "--gif",
                str(gif_output),  # Convert the Path to a string
            ]
        else:
            reanimator_command = [
                f"{data_manager.bundled_data_path(self)}/reanimator",
                "--zip",
                zip_template,
                "--in",
                temp_avatar_path,
                "--gif",
                str(gif_output),  # Convert the Path to a string
            ]

        try:
            subprocess.run(
                reanimator_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            error_message = (
                e.stderr.decode("utf-8") if e.stderr is not None else "Unknown error"
            )
            await ctx.send(f"Error: {error_message}")
            return None

        return gif_output

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def heart(self, ctx, member: FuzzyMember = commands.Author):
        """Make a heartlocket, my beloved"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'heart-locket.zip'}"
            )
            gif_output = (
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )
            await self.process_command(ctx, zip_template, member, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def flag2(self, ctx, member: FuzzyMember = commands.Author):
        """Flagify (Older version)"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'flag.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def bears(self, ctx, member: FuzzyMember = commands.Author):
        """Flying bear"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'flying-bear.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def fcookie(self, ctx, member: FuzzyMember = commands.Author):
        """Fortune Cookify"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'fortune-cookie.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def ndoll(self, ctx, member: FuzzyMember = commands.Author):
        """Nesting Dolls"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'nesting-doll.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def rubix(self, ctx, member: FuzzyMember = commands.Author):
        """Rubix Cube someone!"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'rubix.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def toaster(self, ctx, member: FuzzyMember = commands.Author):
        """Toastifier!"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'toaster.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def valentine(self, ctx, member: FuzzyMember = commands.Author):
        """Valentine Wishes"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'valentine.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def tattoo(self, ctx, member: FuzzyMember = commands.Author):
        """Tattoo someone!"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'back-tattoo.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def book(self, ctx, member: FuzzyMember = commands.Author):
        """Bookify!"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'book.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def circuit(self, ctx, member: FuzzyMember = commands.Author):
        """Put someone in a circuit board"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'circuitboard.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def circuit2(self, ctx, member: FuzzyMember = commands.Author):
        """Put someone in a circuit board (Older version)"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'circuit-board.zip'}"
            )

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def flag(self, ctx, member: FuzzyMember = commands.Author):
        """Flagarize yourself!"""
        async with ctx.typing():
            zip_template = f"{bundled_data_path(self) / 'templates' / 'flag2.zip'}"

            gif_output = str(
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )

            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    @commands.command()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def billboard(self, ctx, member: FuzzyMember = commands.Author):
        """Billboard yourself~"""
        async with ctx.typing():
            zip_template = (
                f"{bundled_data_path(self) / 'templates' / 'billboard-cityscape.zip'}"
            )

            gif_output = (
                cog_data_path(self) / "animations" / f"animation_{member.id}.gif"
            )
            user = member or ctx.author
            await self.process_command(ctx, zip_template, user, gif_output)

    async def process_command(self, ctx, zip_template, user, gif_output):
        async with self.lock:
            async with ctx.typing():
                generated_image = await self.generate_image(
                    ctx, zip_template, user, gif_output
                )
                if generated_image:
                    await ctx.send(file=discord.File(generated_image))

    async def get_avatar(self, user: discord.User):
        if user.avatar.is_animated():
            # Get the first frame of the animated avatar as a static avatar
            static_avatar = await user.avatar.read()
            return static_avatar
        else:
            # If the avatar is not animated, just get the avatar as-is
            avatar_data = await user.avatar.read()
            return avatar_data

    def create_text_image(self, text, font_size=40):
        image = Image.new("RGB", (300, 300), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", font_size)
        text_x = 10
        text_y = 100
        text_color = (0, 0, 0)
        draw.text((text_x, text_y), text, fill=text_color, font=font)
        return image

    def cleanup_cog_data(self):
        # Use the cog's class name as the directory name
        cog_name = self.__class__.__name__
        # Create the cog data path by concatenating the cog's name as a string
        data_path = data_manager.cog_data_path(self, cog_name)

        avatars_path = data_path / "avatars"
        animations_path = data_path / "animations"
        text_images_path = data_path / "text_images"
        avatars_path.mkdir(parents=True, exist_ok=True)
        animations_path.mkdir(parents=True, exist_ok=True)
        text_images_path.mkdir(parents=True, exist_ok=True)

        for file in avatars_path.iterdir():
            if file.is_file():
                file.unlink()

        for file in text_images_path.iterdir():
            if file.is_file():
                file.unlink()

        for file in animations_path.iterdir():
            if file.is_file():
                file.unlink()

    def cog_unload(self):
        # Clean up when the cog is unloaded (reloaded)
        self.cleanup_cog_data()

    def cog_load(self):
        # Clean up when the cog is loaded initially
        self.cleanup_cog_data()
        # Check and grant execute permissions to the reanimator script
        reanimator_path = data_manager.bundled_data_path(self) / "reanimator"
        self.check_and_grant_permissions(reanimator_path)

    def check_and_grant_permissions(self, reanimator_path):
        if not os.access(reanimator_path, os.X_OK):
            # If the script doesn't have execute permissions, add them
            os.chmod(
                reanimator_path, 0o755
            )  # Add execute permissions (rwx for owner, rx for group and others)
