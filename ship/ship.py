import discord
import random
from datetime import datetime
from redbot.core import commands
from redbot.core.i18n import get_locale
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import functools
from random import choice
from redbot.core.data_manager import bundled_data_path
from os import listdir

relationships = {
    "No.....simplemente no.": 0,
    "Pero... la compatibilidad entre ustedes es nula.": 5,
    "Me opongo completamente a esta relación. :x": 10,
    "Esto simplemente nunca funcionará.": 15,
    "Creo que hay mejores duos para ustedes.": 20,
    "Pienso que les irá mejor con alguien más.": 25,
    "Sería mejor que salieran con alguien más. n.n": 30,
    "No pasarán más allá de simples citas.": 35,
    "¿Realmente son feliz así?": 40,
    "¡Buena pareja! Los apoyo.": 45,
    "Parece que se gustan mucho n.n": 50,
    "Hace una pareja super duper linda.": 55,
    "Nunca se engañen. Esto es muy bello.": 60,
    "No pude haberle hecho ship a una mejor pareja que esta.": 65,
    "De verdad me alegra que se hayan encontrado.": 70,
    "Les hago ship para siempre. :3": 75,
    "Definitivamente la pareja más linda.": 80,
    "Son una pareja hecha en el cielo.": 85,
    "Esta es la verdadera belleza.": 90,
}

relationships_en = {
    "No.....Just no.": 0,
    "But... the compatibility between you two is null.": 5,
    "I completely oppose this relationship. :x": 10,
    "This simply will never work.": 15,
    "I think there are better duos for you.": 20,
    "I think you'll be better off with someone else.": 25,
    "It would be better if you went out with someone else. n.n": 30,
    "You won't go beyond simple dates.": 35,
    "Are you really happy like this?": 40,
    "Good couple! I support you.": 45,
    "It seems like you really like each other n.n": 50,
    "You make a super duper cute couple.": 55,
    "Never deceive yourselves. This is very beautiful.": 60,
    "I couldn't have shipped a better couple than this one.": 65,
    "I'm really glad you found each other.": 70,
    "I ship you forever. :3": 75,
    "Definitely the cutest couple.": 80,
    "You are a couple made in heaven.": 85,
    "This is true beauty.": 90,
}


class Ship(commands.Cog):
    @commands.command(aliases=["love"], cooldown_after_parsing=True)
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        """Calculate the percentage of love compatibility between two people.."""
        async with ctx.typing():

            locale = get_locale()
            name1 = self.sanitize_name(user1.display_name)
            name2 = self.sanitize_name(user2.display_name)
            if name1 == name2:
                if locale == "es-ES":
                    await ctx.send("No puedes shipearte dos veces al mismo usuario")
                else:
                    await ctx.send("You cannot calculate someone twice!")
                return
            ship_name = await self.ship_name(name1, name2)
            rate = await self.calculate_rate(name1, name2)
            message = await self.get_message(rate, locale)

            avatar1 = await self.get_avatar(user1)
            avatar2 = await self.get_avatar(user2)

            image = self.generate_image(ctx, avatar1, avatar2, rate)

            embed = discord.Embed(
                description=f"** {message} **",
                color=discord.Colour.from_rgb(255, 105, 180),
            )

            embed.set_image(url="attachment://ship.png")

            if locale == "es-ES":
                message = f"❤️ | El nombre del ship es {ship_name} <:lamor:933194494172622908>\n❤️ | La compatibilidad es {rate}%"
            else:
                message = f"❤️ | The ship name is {ship_name} <:lamor:933194494172622908>\n❤️ | The compatibility rate is {rate}%"

            await ctx.send(message)
            await ctx.send(file=image, embed=embed)

    async def calculate_rate(self, name1, name2):
        sorted_names = sorted((name1, name2))
        seed = hash((sorted_names[1], sorted_names[0])) % 100
        return seed

    async def ship_name(self, name1, name2):
        ship_name = name1[:3] + name2[-3:]
        return ship_name

    async def get_message(self, rate, locale):
        if locale == "es-ES":
            closest_rate = min(relationships.values(), key=lambda x: abs(x - rate))
            closest_message = [
                key for key, value in relationships.items() if value == closest_rate
            ][0]
            return closest_message
        else:
            closest_rate = min(relationships_en.values(), key=lambda x: abs(x - rate))
            closest_message = [
                key for key, value in relationships_en.items() if value == closest_rate
            ][0]
            return closest_message

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
        draw = ImageDraw.Draw(image)
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
