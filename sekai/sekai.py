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
        "color": "FB8AAC",
        "emoji": "airi:1093346507907932292",
    },
    {
        "label": "Akito Shinonome",
        "description": "彰人 東雲",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157099741524533248/akito-01.png",
        "color": "FF7722",
        "emoji": "akito:1093613770594594936",
    },
    {
        "label": "An Shiraishi",
        "description": "杏 白石",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157100811780890674/an-01.png",
        "color": "00BADC",
        "emoji": "an:1093614957905588224",
    },
    {
        "label": "Emu Otori",
        "description": "えむ 鳳",
        "image_path": "https://cdn.discordapp.com/attachments/1157096154664796311/1157096231986790450/emu-01.png",
        "color": "FF66BB",
        "emoji": "emu:1094261561155133480",
    },
    {
        "label": "Ena Shinonome",
        "description": "絵名 東雲",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157102189051904110/ena-01.png",
        "color": "B18F6C",
        "emoji": "ena:1094261743330541729",
    },
    {
        "label": "Haruka Kiritani",
        "description": "桐谷 遥",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157102606427095140/haruka-01.png",
        "color": "6495F0",
        "emoji": "haruka:1094261899115376712",
    },
    {
        "label": "Honami Mochizuki",
        "description": "望月 穂波",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157107898355294258/honami-01.png",
        "color": "F86666",
        "emoji": "honami:1094262044632563813",
    },
    {
        "label": "Ichika Hoshino",
        "description": "星乃 一歌 ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103081713053706/ichika-01.png",
        "color": "33AAEE",
        "emoji": "ichika:1094262202418089994",
    },
    {
        "label": "KAITO",
        "description": "KAITO",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103416468840448/kaito-01.png",
        "color": "3366CC",
        "emoji": "kaito:1094262392122245140",
    },
    {
        "label": "Kanade Yoisaki",
        "description": "宵崎 奏",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157108391118917652/kanade-01.png",
        "color": "BB6688",
        "emoji": "kanade:1094262562914316408",
    },
    {
        "label": "Kohane Azusawa",
        "description": "小豆沢 こはね",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157103672564662283/kohane-01.png",
        "color": "FF6699",
        "emoji": "kohane:1094262705885556736",
    },
    {
        "label": "Len Kagamine",
        "description": "鏡音 レン",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157105765732077660/len-01.png",
        "color": "D3BD00",
        "emoji": "len:1094262824701792266",
    },
    {
        "label": "Luka Megurine",
        "description": "巡音 ルカ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157105978056134666/luka-01.png",
        "color": "F88CA7",
        "emoji": "luka:1094262966876123248",
    },
    {
        "label": "Mafuyu Asahina",
        "description": "朝比奈 まふゆ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157132941827244132/mafuyu-01.png",
        "color": "7171AF",
        "emoji": "mafuyu:1094263132328841246",
    },
    {
        "label": "MEIKO",
        "description": "MEIKO",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157108737945903164/meiko-01.png",
        "color": "E4485F",
        "emoji": "meiko:1094263290395381800",
    },
    {
        "label": "Miku Hatsune",
        "description": "ミク 初音",
        "image_path": "https://cdn.discordapp.com/attachments/1157096154664796311/1157096311871508561/miku-01.png",
        "color": "33CCBB",
        "emoji": "miku:1094263461011263519",
    },
    {
        "label": "Minori Hanasato",
        "description": "花里 みのり",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109076564647956/minori-01.png",
        "color": "F39E7D",
        "emoji": "minori:1094263627277664356",
    },
    {
        "label": "Mizuki Akiyama",
        "description": "暁山 瑞希",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109287898853448/mizuki-01.png",
        "color": "CA8DB6",
        "emoji": "mizuki:1094263876650016858",
    },
    {
        "label": "Nene Kusanagi",
        "description": "草薙 寧々",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157109308237025341/nene-01.png",
        "color": "19CD94",
        "emoji": "nene:1094264060582830191",
    },
    {
        "label": "Rin Kagamine",
        "description": "鏡音 リン",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110305038549132/rin-01.png",
        "color": "E8A505",
        "emoji": "rin:1094264676822564934",
    },
    {
        "label": "Rui Kamishiro",
        "description": "神代 類 ",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110362391445597/rui-01.png",
        "color": "BB88EE",
        "emoji": "rui:1094264833563705436",
    },
    {
        "label": "Saki Tenma",
        "description": "天馬 咲希",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110525382107187/saki-01.png",
        "color": "F5B303",
        "emoji": "saki:1094264979781328919",
    },
    {
        "label": "Shiho Hinomori",
        "description": "日野森 志歩",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110605132603402/shiho-01.png",
        "color": "A0C10B",
        "emoji": "shiho:1094265147868069949",
    },
    {
        "label": "Shizuku Hinomori",
        "description": "日野森 雫",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110664360366090/shizuku-01.png",
        "color": "5CD0B9",
        "emoji": "shizuku:1094265295985713183",
    },
    {
        "label": "Tsukasa Tenma",
        "description": "天馬 司",
        "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110757406802020/tsukasa-01.png",
        "color": "F09A04",
        "emoji": "tsukasa:1094265608398442596",
    },
    # 26 is too much sry Toya, nobody gonna miss u
    # {
    #    "label": "Toya Aoyagi",
    #    "description": "青柳 冬弥",
    #    "image_path": "https://cdn.discordapp.com/attachments/861428239012069416/1157110742999375912/touya-01.png",
    #    "color": "FF0000",
    # },
]


# Dropdown Selector
class CharacterDropdown(discord.ui.Select):
    def __init__(self, characters, embed, message):
        select_options = [
            discord.SelectOption(
                label=character["label"],
                value=character["label"],
                description=character["description"],
                emoji=character["emoji"],  # Thanks Melon! <3
            )
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
                text=f"Originally made by Ayaka! Try it with [p]sekai",
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
    """Creates Sekai Sticker
    WONDERHOY"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__version__ = "1.0.0"
        self.message = None
        self.embed = discord.Embed(
            title="Sekai Stickers!", description="Select a character to view available stickers."
        )
        self.color = None

    # Show all available characters
    @commands.hybrid_command()
    async def characters(self, ctx):
        """Show available characters!"""
        view = CharacterView(characters, self.embed, self.message)
        self.message = await ctx.send(embed=self.embed, view=view)

    # Create sticker command
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.hybrid_command()
    async def sekai(
        self,
        ctx: commands.Context,
        character: commands.Range[str, 1, 8] = None,
        chara_face: commands.Range[int, 1, 20] = None,
        text: typing.Optional[str] = None,
        textx: typing.Optional[commands.Range[str, 1, 300]] = 0,
        texty: typing.Optional[commands.Range[str, 1, 300]] = 0,
        fontsize: typing.Optional[commands.Range[int, 1, 80]] = 0,
    ):
        """Make a Sekai sticker!
        View all characters with `[p]characters`.
        Simple Example: ``[p]sekai emu 13 "Wonderhoy!"``
        Ext Example: ``[p]sekai emu 13 "Wonderhoy!" 25 50 30``
        """
        if (
            character == None
            and chara_face == None
            and text == 0
            and textx == 0
            and texty == 0
            and fontsize == 0
        ):
            # If no arguments are provided, send the command's help message
            await ctx.send_help(ctx.command)
        else:
            # await ctx.send(
            #    f"Debug: character: {character}, chara_face: {chara_face}, text: {text}, textx: {textx}, texty: {texty}, fontsize: {fontsize}"
            # )
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

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    # Thanks Phen!
    def gen_card(self, ctx, character, chara_face, text, textx, texty, fontsize):
        # Error preventer
        arr = [
            "ari",
            "akito",
            "an",
            "emu",
            "ena",
            "haruka",
            "honami",
            "ichika",
            "kaito",
            "kanade",
            "kohane",
            "len",
            "luka",
            "mafuyu",
            "meiko",
            "miku",
            "minori",
            "mizuki",
            "nene",
            "rin",
            "rui",
            "saki",
            "shiho",
            "shizuku",
            "tsukasa",
            "airi",
        ]
        try:
            if character.lower() not in [name for name in arr]:
                character = "emu"
        except AttributeError:
            return f"Youre missing the sticker contents!. \n Type ``{ctx.prefix}help sekai`` for details"
        if chara_face == 0:
            chara_face = 1
        if character == 0:
            character = "emu"
        if text == 0:
            text = "You forgot the text!"
        if textx == 0:
            textx = 25
        if texty == 0:
            texty = 45
        if fontsize == 0:
            fontsize = 30

        # base canvas
        if chara_face < 10:
            chara_face = "0" + str(chara_face)
        else:
            if chara_face > 19:
                chara_face = "01"

        # Odd case where some images don't exist. Don't ask me lol
        if chara_face == 10:
            chara_face = 8
            character = "emu"
            text = "There is no face 10! Silly"

        # Creation
        try:
            sticker_base = Image.open(
                f"{bundled_data_path(self)}/{character}/{character}_{chara_face}.png", mode="r"
            ).convert("RGBA")
        except FileNotFoundError:
            return f"The specified sticker file was not found. \nCheck the list with {ctx.prefix}characters"

        widthh, height = sticker_base.size
        im = Image.new("RGBA", (widthh, height), None)
        colors = [
            {"name": "ari", "color": "FB8AAC"},
            {"name": "airi", "color": "FB8AAC"},
            {"name": "akito", "color": "FF7722"},
            {"name": "an", "color": "00BADC"},
            {"name": "emu", "color": "FF66BB"},
            {"name": "ena", "color": "B18F6C"},
            {"name": "haruka", "color": "6495F0"},
            {"name": "honami", "color": "F86666"},
            {"name": "ichika", "color": "33AAEE"},
            {"name": "kaito", "color": "3366CC"},
            {"name": "kanade", "color": "BB6688"},
            {"name": "kohane", "color": "FF6699"},
            {"name": "len", "color": "D3BD00"},
            {"name": "luka", "color": "F88CA7"},
            {"name": "mafuyu", "color": "7171AF"},
            {"name": "meiko", "color": "E4485F"},
            {"name": "miku", "color": "33CCBB"},
            {"name": "minori", "color": "F39E7D"},
            {"name": "mizuki", "color": "CA8DB6"},
            {"name": "nene", "color": "19CD94"},
            {"name": "rin", "color": "E8A505"},
            {"name": "rui", "color": "BB88EE"},
            {"name": "saki", "color": "F5B303"},
            {"name": "shiho", "color": "A0C10B"},
            {"name": "shizuku", "color": "5CD0B9"},
            {"name": "tsukasa", "color": "F09A04"},
        ]
        # character = "emu"
        characolor = None

        for color in colors:
            if color["name"] == character:
                characolor = "#" + color["color"]

                break

        if characolor is None:
            characolor = "#FF66BB"
        im.paste(sticker_base, (0, 0), sticker_base)
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype(f"{bundled_data_path(self)}/ahoy.ttf", fontsize)

        # Calculate the maximum number of characters per line
        try:
            max_chars_per_line = int((widthh - int(textx)) / fontsize) + 5
        except ValueError:
            return f'There was an error generating the sticker. \nDid you add "quotes" to the message?'

        # Wrap the text using textwrap module
        wrapped_text = textwrap.wrap(text, width=max_chars_per_line)
        line_spacing = 5  # Adjust the line spacing as needed

        # Calculate the total height required for the text
        total_text_height = 0
        for line in wrapped_text:
            text_width, text_height = draw.textsize(line, font=font)
            total_text_height += text_height + line_spacing

        # Calculate the new image height
        new_height = max(height, total_text_height + int(texty) + 3)

        # Resize the image if necessary
        if new_height > height:
            im = im.resize((widthh, new_height), resample=Image.LANCZOS)
            height = new_height

        text_y = int(texty)
        for line in wrapped_text:
            text_width, text_height = draw.textsize(line, font=font)
            draw.text(
                (int(textx), text_y),
                line,
                font=font,
                fill=characolor,
                stroke_width=5,
                stroke_fill="#FFF",
            )
            text_y += text_height + line_spacing

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "Sticker.png")
        fp.close()
        return _file
