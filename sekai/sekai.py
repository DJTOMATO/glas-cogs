from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from redbot.core.dev_commands import async_compile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import asyncio
import discord
import random
import functools
import textwrap
import regex as re
import typing
from typing import Optional


class Sekai(commands.Cog):
    """
    Creates Sekai Sticker
    """

    # Thanks MAX <3
    def __init__(self, bot: Red) -> None:
        self.bot = bot

    __version__ = "1.0.0"

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=["wonderhoy"], cooldown_after_parsing=True)
    # Thanks Kowlin! <3 & AAA3A
    # async def ygo(self, ctx: commands.Context, member: discord.Member, *, skill_text: Optional[str]):
    async def sekai(
        self,
        ctx: commands.Context,
        character: typing.Optional[commands.Range[str, 1, 8]] = 0,
        chara_face: typing.Optional[commands.Range[int, 1, 20]] = 0,
        text: typing.Optional[commands.Range[str, 1, 500]] = 0,
        textx: typing.Optional[commands.Range[str, 1, 300]] = 0,
        texty: typing.Optional[commands.Range[str, 1, 300]] = 0,
        fontsize: typing.Optional[commands.Range[int, 1, 80]] = 0,
        spacesize: typing.Optional[commands.Range[int, 1, 10]] = 0,
        rotate: typing.Optional[commands.Range[int, 1, 360]] = 0,
    ):
        """Make a Sekai sticker"""
        """Only emu available for now."""
        """Cog in development, so bear me the bugs"""
        """Example: ``!sekai emu 13 "Wonderhoy!" 25 50 30``"""
        #await ctx.send(
        #    f"Debug: character: {character}, chara_face: {chara_face}, text: {text}, textx: {textx}, texty: {texty}, fontsize: {fontsize}"
        #)
        async with ctx.typing():
            task = functools.partial(
                self.gen_card,
                ctx,
                character,
                chara_face,
                text,
                textx,
                texty,
                fontsize,
                spacesize,
                rotate,
            )
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
            return "An error occurred while generating this sticker. Try again later."
        else:
            return image

    async def sanitize_string(self, input_string):
        sanitized_string = re.sub(r"[^a-zA-Záéíóú\s]+", "", input_string)
        return sanitized_string

    async def draw_text_90_into(text: str, into, at):
        # Measure the text area
        font = ImageFont.truetype(r"C:\Windows\Fonts\Arial.ttf", 16)
        wi, hi = font.getsize(text)

        # Copy the relevant area from the source image
        img = into.crop((at[0], at[1], at[0] + hi, at[1] + wi))

        # Rotate it backwards
        img = img.rotate(270, expand=1)

        # Print into the rotated area
        d = ImageDraw.Draw(img)
        d.text((0, 0), text, font=font, fill=(0, 0, 0))

        # Rotate it forward again
        img = img.rotate(90, expand=1)

        # Insert it back into the source image
        # Note that we don't need a mask
        into.paste(img, at)

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    # Thanks Phen!
    def gen_card(
        self, ctx, character, chara_face, text, textx, texty, fontsize, spacesize, rotate
    ):
        # base canvas
        if chara_face < 10:
            chara_face = "0" + str(chara_face)
        sticker_base = Image.open(
            f"{bundled_data_path(self)}/{character}/{character}_{chara_face}.png", mode="r"
        ).convert("RGBA")
        widthh, height = sticker_base.size
        im = Image.new("RGBA", (widthh, height), None)
        # Emu only for now
        character = "emu"

        if character == "emu":
            characolor = "#FF66BB"
        im.paste(sticker_base, (0, 0), sticker_base)
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(f"{bundled_data_path(self)}/ahoy.ttf", fontsize)

        lines = textwrap.wrap(text, width=widthh)
        draw.multiline_text(
            (int(textx), int(texty)),
            "\n".join(lines),
            font=font,
            fill=f"{characolor}",
            stroke_width=5,
            stroke_fill="#FFF",
        )

        sticker_base.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "card.png")
        fp.close()
        return _file
