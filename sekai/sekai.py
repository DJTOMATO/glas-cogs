from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import asyncio
import discord
import functools
import textwrap
import regex as re
import typing
from typing import Optional
from discord.ui import Select, View
from discord import SelectOption

# Character list, will get updated
characters = [
    {"label": "Emu Otori", "description": "えむ 鳳", "image_path": "emu-01.png", "color": "ffc0cb"},
    {
        "label": "Miku Hatsune",
        "description": "ミク 初音",
        "image_path": "miku-01.png",
        "color": "86cecb",
    },
    {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
    # Placeholders
    # {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
    # {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
    # {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
    # {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
    # {"label": "Airi Momoi", "description": "愛莉 桃井", "image_path": "ari-01.png", "color": "FF0000"},
]


# Dropdown Selector
class CharacterDropdown(discord.ui.Select):
    def __init__(self, characters, embed, message):
        select_options = [
            discord.SelectOption(label=character["label"], value=character["label"])
            for character in characters
        ]
        super().__init__(placeholder="Select your Character...", options=select_options)
        self.characters = characters
        self.embed = embed
        self.message = message

    async def callback(self, interaction: discord.Interaction):
        try:
            # Obtains Character
            selected_character_value = interaction.data["values"][0]
            selected_character = next(
                (
                    character
                    for character in self.characters
                    if character["label"] == selected_character_value
                ),
                None,
            )
            if selected_character is None:
                return
            # Grabs image for character
            selected_character_image = discord.File(
                f"{bundled_data_path(self)}/{selected_character['image_path']}"
            )
            # Embed updates
            self.embed.title = selected_character["label"]
            self.embed.description = selected_character["description"]
            # Color Choser
            color = selected_character["color"]
            # Color
            self.embed.color = discord.Color(int(color, 16))
            self.embed.set_image(url=f"attachment://{selected_character['image_path']}")

            # self.embed.set_image(selected_character_image) <= An error occurred: Embed.set_image() takes 1 positional argument but 2 were given

            # Interaction Update?
            await interaction.response.edit_message(embed=self.embed, view=self.view)
            # Edit message?
            await self.message.edit(embed=self.embed, view=self.view)
            # Replies as new message after dropdown is chosen??
            # await interaction.followup.send(file=selected_character_image, embed=self.embed)
        except Exception as e:
            # Error report on the initial view/embed
            self.embed.description = f"An error occurred: {e}"
            await interaction.response.edit_message(embed=self.embed, view=self.view)
        except discord.errors.InteractionResponded:
            pass


# The view
class CharacterView(discord.ui.View):
    def __init__(self, characters, embed, message):
        super().__init__()
        self.add_item(CharacterDropdown(characters, embed, message))


# The commands
class Sekai(commands.Cog):
    """Creates Sekai Sticker"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__version__ = "1.0.0"
        self.message = None
        self.embed = discord.Embed(
            title="Sekai Stickers!", description="Select a character to view available stickers."
        )

    # Show all available characters
    @commands.hybrid_command()
    async def characters(self, ctx):
        view = CharacterView(characters, self.embed, self.message)
        if self.message is None:
            self.message = await ctx.send(embed=self.embed, view=view)
        else:
            await self.message.edit(embed=self.embed, view=self.view)

    # Create sticker command
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.hybrid_command()
    async def sekai(
        self,
        ctx: commands.Context,
        character: typing.Optional[commands.Range[str, 1, 8]] = 0,
        chara_face: typing.Optional[commands.Range[int, 1, 20]] = 0,
        text: typing.Optional[commands.Range[str, 1, 500]] = 0,
        textx: typing.Optional[commands.Range[str, 1, 300]] = 0,
        texty: typing.Optional[commands.Range[str, 1, 300]] = 0,
        fontsize: typing.Optional[commands.Range[int, 1, 80]] = 0,
    ):
        """Make a Sekai sticker
        Only emu available for now.
        Cog in development, so bear me the bugs
        Example: ``!sekai emu 13 "Wonderhoy!" 25 50 30``"""
        await ctx.send(
            f"Debug: character: {character}, chara_face: {chara_face}, text: {text}, textx: {textx}, texty: {texty}, fontsize: {fontsize}"
        )
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
    def gen_card(self, ctx, character, chara_face, text, textx, texty, fontsize):
        # Error preventer
        arr = ["Emu", "Miku", "emu", "Miku"]
        if character not in arr:
            character = "emu"
        if chara_face == 0:
            chara_face = 1
        if character == 0:
            character = "emu"
        if text == 0:
            text = "You forgot a text!"
        if textx == 0:
            textx = 50
        if texty == 0:
            texty = 40
        if fontsize == 0:
            fontsize = 20

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
        _file = discord.File(fp, "Sticker.png")
        fp.close()
        return _file
