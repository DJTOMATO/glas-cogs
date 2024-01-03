import discord
from redbot.core import commands, app_commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import asyncio
import functools
import regex as re
from .functions_js import (
    COLOR_CHOICES,
    CHARACTER_CHOICES,
    CHOICES,
    CHOICE_DESC,
    generate,
    convert_to_discord_file,
)
import logging
import traceback

from typing import Optional, Union, Tuple, Coroutine, Any


class Umineko(commands.Cog):
    """Umineko Screenshot Generator"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__version__ = "1.0.0"
        self.message = None
        self.embed = discord.Embed(title="Umineko", description="a.")
        self.color = None
        self.log = logging.getLogger("glas.glas-cogs.umineko")

    # async def generate_image(self, task: commands.Context):
    #     task = self.bot.loop.run_in_executor(None, task)
    #     try:
    #         image = await asyncio.wait_for(task, timeout=60)
    #     except asyncio.TimeoutError:
    #         return "An error occurred while generating this sticker. Try again later."
    #     else:
    #         return image

    @app_commands.command(name="umi", description="Umineko Background Generator")
    @app_commands.describe(**CHOICE_DESC)
    @app_commands.choices(
        **CHOICES,
    )
    async def umi_command(
        self,
        ctx: commands.Context,
        text1: str,
        text2: Optional[str],
        left: Optional[str],
        center: Optional[str],
        right: Optional[str],
        metaleft: Optional[str],
        metacenter: Optional[str],
        metaright: Optional[str],
        color1: Optional[str],
        color2: Optional[str],
        bg: Optional[str],
    ):
        """Make a Umineko Screenshot!"""
        if left and left not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for left", ephemeral=True
            )
        if center and center not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for center", ephemeral=True
            )
        if center and center not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for center", ephemeral=True
            )
        if metaleft and metaleft not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for metaleft", ephemeral=True
            )
        if metacenter and metacenter not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for metacenter", ephemeral=True
            )
        if metaright and metaright not in CHARACTER_CHOICES:
            return await ctx.send(
                f"You chose an invalid character for metaright", ephemeral=True
            )
        parameters = {
            "text1": text1,
            "text2": text2,
            "left": left,
            "center": center,
            "right": right,
            "metaleft": metaleft,
            "metacenter": metacenter,
            "metaright": metaright,
            "color1": color1,
            "color2": color2,
            "bg": bg,
        }

        DEFAULT_CHARACTER_FOLDER = "beatrice"
        characters = {
            "left": left,
            "center": center,
            "right": right,
            "metaleft": metaleft,
            "metacenter": metacenter,
            "metaright": metaright,
        }
        character_folders = {}
        for key, value in characters.items():
            if value in CHARACTER_CHOICES:
                character_folders[key] = CHARACTER_CHOICES[value]
            elif not value:
                character_folders[key] = DEFAULT_CHARACTER_FOLDER
            else:
                return await ctx.send(
                    f"You chose an invalid character for {key}", ephemeral=True
                )
        try:
            image = await self.generate_image(ctx, **parameters)
            if isinstance(image, discord.File):
                await ctx.response.send_message(file=image)
            else:
                await ctx.response.send_message(image)
        except Exception as e:
            # Log the full traceback
            self.log.error("An error occurred:")
            self.log.error(
                "".join(traceback.format_exception(type(e), e, e.__traceback__))
            )

            # Handle the exception, e.g., inform the user
            await ctx.response.send_message(
                f"An error occurred: {str(e)}", ephemeral=True
            )

    @umi_command.autocomplete("left")
    @umi_command.autocomplete("center")
    @umi_command.autocomplete("right")
    @umi_command.autocomplete("metaleft")
    @umi_command.autocomplete("metaright")
    @umi_command.autocomplete("metacenter")
    async def character_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        if not current:
            results = CHARACTER_CHOICES.keys()
        else:
            results = [
                ch
                for ch in CHARACTER_CHOICES.keys()
                if ch.lower().startswith(current.lower())
            ]
            results += [
                ch
                for ch in CHARACTER_CHOICES.keys()
                if current.lower() in ch[1:].lower()
            ]

        return [app_commands.Choice(name=ch, value=ch) for ch in results][:25]

    async def generate_image(self, ctx, **parameters):
        """Generate Umineko Screenshot and return the image."""
        # Core logic for Umineko screenshot generation using kwargs and ctx

        # Replace the following line with your actual image generation logic
        image_data = await generate(self, ctx, **parameters)

        # For simplicity, assume there's a method to convert image_data to a Discord File
        image_file = convert_to_discord_file(image_data)

        return image_file
