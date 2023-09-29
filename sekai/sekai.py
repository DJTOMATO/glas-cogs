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
    {
        "label": "Airi Momoi",
        "description": "愛莉 桃井",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157096390825103481/ari-01.png",
        "color": "FF0000",
    },
    {
        "label": "Akito Shinonome",
        "description": "彰人 東雲",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157099741524533248/akito-01.png",
        "color": "3e5981",
    },
    {
        "label": "An Shiraishi",
        "description": "杏 白石",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157100811780890674/an-01.png",
        "color": "67AED4",
    },
    {
        "label": "Emu Otori",
        "description": "えむ 鳳",
        "image_path": "https://cdn.discordapp.com/attachments/1157096154664796311/1157096231986790450/emu-01.png",
        "color": "ffc0cb",
    },
    {
        "label": "Ena Shinonome",
        "description": "絵名 東雲",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157102189051904110/ena-01.png",
        "color": "3a8d8d",
    },
    {
        "label": "Haruka Kiritani",
        "description": "桐谷 遥",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157102606427095140/haruka-01.png",
        "color": "00b0ea",
    },
    {
        "label": "Honami Mochizuki",
        "description": "望月 穂波",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157107898355294258/honami-01.png",
        "color": "00b0ea",
    },
    {
        "label": "Ichika Hoshino",
        "description": "星乃 一歌 ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103081713053706/ichika-01.png",
        "color": "004680",
    },
    {
        "label": "KAITO",
        "description": "KAITO",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103416468840448/kaito-01.png",
        "color": "91bfcc",
    },
    {
        "label": "Kanade Yoisaki",
        "description": "宵崎 奏",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157108391118917652/kanade-01.png",
        "color": "FF0000",
    },
    {
        "label": "Kohane Azusawa",
        "description": "小豆沢 こはね",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103672564662283/kohane-01.png",
        "color": "FF0000",
    },
    {
        "label": "Len Kagamine",
        "description": "鏡音 レン",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157105765732077660/len-01.png",
        "color": "FF0000",
    },
    {
        "label": "Luka Megurine",
        "description": "巡音 ルカ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157105978056134666/luka-01.png",
        "color": "FF0000",
    },
    {
        "label": "Mafuyu Asahina",
        "description": "朝比奈 まふゆ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103672564662283/kohane-01.png",
        "color": "FF0000",
    },
    {
        "label": "MEIKO",
        "description": "MEIKO",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157108737945903164/meiko-01.png",
        "color": "86cecb",
    },
    {
        "label": "Miku Hatsune",
        "description": "ミク 初音",
        "image_path": "https://cdn.discordapp.com/attachments/1157096154664796311/1157096311871508561/miku-01.png",
        "color": "86cecb",
    },
    {
        "label": "Minori Hanasato",
        "description": "花里 みのり",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109076564647956/minori-01.png",
        "color": "FF0000",
    },
    {
        "label": "Mizuki Akiyama",
        "description": "暁山 瑞希",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109287898853448/mizuki-01.png",
        "color": "FF0000",
    },
    {
        "label": "Nene Kusanagi",
        "description": "草薙 寧々",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109308237025341/nene-01.png",
        "color": "FF0000",
    },
    {
        "label": "Rin Kagamine",
        "description": "鏡音 リン",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110305038549132/rin-01.png",
        "color": "FF0000",
    },
    {
        "label": "Rui Kamishiro",
        "description": "神代 類 ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110362391445597/rui-01.png",
        "color": "FF0000",
    },
    {
        "label": "Saki Tenma",
        "description": "天馬 咲希",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110525382107187/saki-01.png",
        "color": "FF0000",
    },
    {
        "label": "Shiho Hinomori",
        "description": "日野森 志歩",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110605132603402/shiho-01.png",
        "color": "FF0000",
    },
    {
        "label": "Shizuku Hinomori",
        "description": "日野森 雫",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110664360366090/shizuku-01.png",
        "color": "FF0000",
    },
    {
        "label": "Toya Aoyagi",
        "description": "青柳 冬弥",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110742999375912/touya-01.png",
        "color": "FF0000",
    },
    {
        "label": "Tsukasa Tenma",
        "description": "天馬 司",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110757406802020/tsukasa-01.png",
        "color": "FF0000",
    },
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
            self.embed.title = selected_character["label"]
            self.embed.description = selected_character["description"]

            color = selected_character["color"]
            self.embed.color = discord.Color(int(color, 16))
            self.embed.set_image(url=f"{selected_character['image_path']}")
            self.embed.set_footer(
                icon_url="https://bae.lena.moe/l9q3mnnat3i3.gif",
                text="Originally made by Ayaka! Try it with !sekai",
            )
            await interaction.response.edit_message(embed=self.embed, view=self.view)
            await self.message.edit(embed=self.embed, view=self.view)
        except Exception as e:
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
        self.message = await ctx.send(embed=self.embed, view=view)

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
