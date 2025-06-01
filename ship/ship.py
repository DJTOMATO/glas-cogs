import discord
from redbot.core import commands
from redbot.core.i18n import Translator
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from random import choice
from redbot.core.data_manager import bundled_data_path
from os import listdir
import logging

_ = Translator("Ship", __file__)


RATE_MESSAGES_MAP = {
    0: "No.....Just no.",
    5: "But... the compatibility between you two is null.",
    10: "I completely oppose this relationship. :x",
    15: "This simply will never work.",
    20: "I think there are better duos for you.",
    25: "I think you'll be better off with someone else.",
    30: "It would be better if you went out with someone else. n.n",
    35: "You won't go beyond simple dates.",
    40: "Are you really happy like this?",
    45: "Good couple! I support you.",
    50: "It seems like you really like each other n.n",
    55: "You make a super duper cute couple.",
    60: "Never deceive yourselves. This is very beautiful.",
    65: "I couldn't have shipped a better couple than this one.",
    70: "I'm really glad you found each other.",
    75: "I ship you forever. :3",
    80: "Definitely the cutest couple.",
    85: "You are a couple made in heaven.",
    90: "This is true beauty.",
    100: "This is a miracle",
}


class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    log = logging.getLogger("red.valentine.ship")

    @commands.command(aliases=["love"], cooldown_after_parsing=True)
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """Calculate the percentage of love compatibility between two people.

        Example usage: `[p]ship @user1 @user2`
        This command generates a ship name and a compatibility rate based on the names of the users.
        """
        async with ctx.typing():
            name1 = self.sanitize_name(user1.display_name)
            name2 = self.sanitize_name(user2.display_name)
            if name1 == name2:
                await ctx.send(_("You cannot ship a user with themselves!"))
                return

            ship_name = await self.ship_name(name1, name2)
            rate = await self.calculate_rate(name1, name2)

            if ship_name == "Helnks":
                rate = 1000

            message_for_embed = await self.get_message(rate)

            avatar1 = await self.get_avatar(user1)
            avatar2 = await self.get_avatar(user2)

            image = self.generate_image(ctx, avatar1, avatar2, rate)

            embed = discord.Embed(
                description=f"** {message_for_embed} **",
                color=discord.Colour.from_rgb(255, 105, 180),
            )
            embed.set_image(url="attachment://ship.png")

            final_message_text = _(
                "❤️ | The ship name is {ship_name} ❤️ | The compatibility rate is {rate}%"
            ).format(ship_name=ship_name, rate=rate)
            await ctx.send(final_message_text)
            await ctx.send(file=image, embed=embed)

    async def calculate_rate(self, name1, name2):
        sorted_names = sorted((name1, name2))

        special_pairs = {
            frozenset({"Senko", "Glas"}),
            frozenset({"Lena", "Glas"}),
            frozenset({"Helaaisha", "Rutenks"}),
            frozenset({"AAA3A", "Code Master"}),
            frozenset({"AAA3A", "CodeMaster"}),
        }

        current_pair = frozenset({name1, name2})
        if current_pair in special_pairs:
            return 100

        return hash((sorted_names[1], sorted_names[0])) % 100

    async def ship_name(self, name1, name2):
        ship_name = name1[:3] + name2[-3:]
        return ship_name

    async def get_message(self, rate: int):
        """Gets the appropriate translated message string based on the compatibility rate."""
        if not RATE_MESSAGES_MAP:

            return _("ship_error_no_messages")
        actual_rate_for_message_lookup = rate

        if rate > 100:
            if 100 in RATE_MESSAGES_MAP:
                actual_rate_for_message_lookup = 100

        closest_numeric_key = min(
            RATE_MESSAGES_MAP.keys(),
            key=lambda k: abs(k - actual_rate_for_message_lookup),
        )

        message_translation_key = RATE_MESSAGES_MAP[closest_numeric_key]
        translator_func = _
        return translator_func(message_translation_key)

    async def get_avatar(self, member: discord.abc.User):
        avatar = BytesIO()
        display_avatar: discord.Asset = member.display_avatar.replace(
            size=512, static_format="png"
        )
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def sanitize_name(self, input_string):
        sanitized_string = re.sub(r"[^a-zA-Záéíóú\s]+", "", input_string)
        return sanitized_string

    def generate_image(self, ctx, avatar1, avatar2, rate):
        image_path = choice(listdir(f"{bundled_data_path(self)}/images/"))
        template = Image.open(
            f"{bundled_data_path(self)}/images/{image_path}", mode="r"
        ).convert("RGBA")
        image = Image.new("RGBA", (610, 200), None)

        avatar1 = self.bytes_to_image(avatar1, 200)
        avatar2 = self.bytes_to_image(avatar2, 200)
        image.paste(im=avatar1, box=(25, 19))
        image.paste(im=avatar2, box=(380, 19))
        image.paste(im=template, box=(0, 0), mask=template)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            f"{bundled_data_path(self)}/Lato-Bold.ttf", size=32, encoding="utf-8"
        )
        # draw = ImageDraw.Draw(image) # This was a duplicate
        bbox = draw.textbbox((0, 0), str(rate) + "%", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(
            (305 - text_width // 2, 90 - text_height // 2),
            str(rate) + "%",
            fill=(255, 255, 255),
            font=font,
            align="center",
        )
        fp = BytesIO()
        image.save(fp, "PNG")
        fp.seek(0)
        image.close()
        _file = discord.File(fp, "ship.png")
        fp.close()
        return _file
