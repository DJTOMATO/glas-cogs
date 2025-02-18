import discord
import random
from redbot.core import commands
import functools
import asyncio
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from redbot.core.data_manager import bundled_data_path
import aiohttp


class QuoterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=["epicquote"], cooldown_after_parsing=True)
    async def quoter(self, ctx: commands.Context):
        if ctx.message.reference:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            avatar = await self.get_avatar(replied_message.author)
            message_content = self.remove_emojis(replied_message.content)
            nickname = replied_message.author.display_name
            username = replied_message.author.name
            emoji = self.extract_first_emoji(replied_message.content)
        else:
            await ctx.send("Please use this command as a reply to a message.")
            return

        async with ctx.typing():
            task = functools.partial(self.gen_pic, avatar, message_content, nickname, username, emoji)
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
            return "An error occurred while generating this image. Try again later."
        else:
            return image

    async def get_avatar(self, member: discord.abc.User):
        avatar = BytesIO()
        display_avatar: discord.Asset = member.display_avatar.replace(size=512, static_format="png")
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    async def get_avatar_from_url(self, url: str):
        avatar = BytesIO()
        async with self.session.get(url) as response:
            if response.status != 200:
                raise commands.BadArgument("Invalid image URL.")
            avatar_bytes = await response.read()
            avatar.write(avatar_bytes)
            avatar.seek(0)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def gen_pic(self, avatar, message_content, nickname, username, emoji):
        if len(message_content) > 230:
            message_content = message_content[:230] + "..."

        img = Image.new("RGBA", (1200, 600), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)

        with Image.open(avatar) as avatar_img:
            avatar_img = avatar_img.convert("L").convert("RGBA")
            avatar_img = avatar_img.resize((600, 600), Image.LANCZOS)
            img.paste(avatar_img, (0, 0))

        pillar_width = 68
        for x in range(600 - pillar_width // 2, 600 + pillar_width // 2):
            for y in range(600):
                if random.random() < (1 - abs(x - 600) / (pillar_width // 2)):
                    img.putpixel((x, y), (0, 0, 0, 0))

        font_path_message = f"{bundled_data_path(self)}/ariali.ttf"
        font_path_nickname = f"{bundled_data_path(self)}/ARIALBI.TTF"
        emoji_font_path = f"{bundled_data_path(self)}/NotoEmoji-VariableFont_wght.ttf"
        try:
            font_message_cursive = ImageFont.truetype(font_path_message, 40, layout_engine=ImageFont.Layout.RAQM)
            font_nickname_bold = ImageFont.truetype(font_path_nickname, 30, layout_engine=ImageFont.Layout.RAQM)
            font_emoji = ImageFont.truetype(emoji_font_path, 30, layout_engine=ImageFont.Layout.RAQM)
        except OSError:
            font_message_cursive = ImageFont.load_default()
            font_nickname_bold = ImageFont.load_default()
            font_emoji = ImageFont.load_default()

        max_width = 570
        message_lines, message_line_height = self.wrap_text(draw, message_content, font_message_cursive, max_width, respect_newlines=True)
        nickname_lines, nickname_line_height = self.wrap_text(draw, f"- {nickname}", font_nickname_bold, max_width)

        line_spacing = 10
        total_text_height = (len(message_lines) * (message_line_height + line_spacing) +
                             len(nickname_lines) * (nickname_line_height + line_spacing) -
                             line_spacing)
        start_y = (600 - total_text_height) // 2

        y = start_y
        for line in message_lines:
            line_width, line_height = self.get_text_dimensions(line, font_message_cursive)
            x = 905 - line_width // 2
            draw.text((x, y), line, font=font_message_cursive, fill=(255, 255, 255))
            y += message_line_height + line_spacing

        for line in nickname_lines:
            line_width, line_height = self.get_text_dimensions(line, font_nickname_bold)
            x = 905 - line_width // 2
            draw.text((x, y), line, font=font_nickname_bold, fill=(255, 255, 255))
            y += nickname_line_height + line_spacing

        if emoji:
            emoji_width, emoji_height = self.get_text_dimensions(emoji, font_emoji)
            draw.text((x + line_width + 10, y - line_height), emoji, font=font_emoji, fill=(255, 255, 255))

        with BytesIO() as fp:
            img.save(fp, "PNG")
            fp.seek(0)
            _file = discord.File(fp, "quote.png")

        return _file

    def wrap_text(self, draw, text, font, max_width, respect_newlines=False):
        lines = []
        line_height = self.get_text_dimensions('A', font)[1]
        if respect_newlines:
            paragraphs = text.split('\n')
        else:
            paragraphs = [text]

        for paragraph in paragraphs:
            words = paragraph.split()
            while words:
                line = ''
                while words and self.get_text_dimensions(line + words[0], font)[0] <= max_width:
                    line += (words.pop(0) + ' ')
                lines.append(line.strip())
            if respect_newlines:
                lines.append('')

        return lines, line_height

    @staticmethod
    def get_text_dimensions(text, font):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    @staticmethod
    def remove_emojis(text):
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r'', text).replace('\n', '\n')

    @staticmethod
    def extract_first_emoji(text):
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )
        match = emoji_pattern.search(text)
        return match.group(0) if match else None
