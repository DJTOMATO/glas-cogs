import discord
from redbot.core import commands, app_commands, Config
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import asyncio
import functools
import re
from .functions_js import (
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
        self.font_path = f"{bundled_data_path(self)}/fonts/sazanami-gothic.ttf"

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
        text: str,
        left: Optional[str],
        center: Optional[str],
        right: Optional[str],
        bg: Optional[str],
        meta: Optional[str],
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

        parameters = {
            "text": text,
            "left": left,
            "center": center,
            "right": right,
            "meta": meta,
            "bg": bg,
        }

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
