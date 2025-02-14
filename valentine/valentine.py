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
from redbot.core import Config


class Valentine(commands.Cog):
    def __init__(self):
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {"letters_received": {}}
        self.config.register_global(**default_global)

    @commands.command(aliases=["loveletter"], cooldown_after_parsing=True)
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def valentines(self, ctx, user2: discord.Member):
        """Send love letter to an user!.."""
        async with ctx.typing():
            user1 = ctx.author  
            locale = get_locale()
            name1 = self.sanitize_name(user1.display_name)
            name2 = self.sanitize_name(user2.display_name)
            if name1 == name2:
                if locale == "es-ES":
                    await ctx.send("No puedes enviarte una carta a ti mismo!")
                else:
                    await ctx.send("You cannot valentine yourself!")
                return

            avatar1 = await self.get_avatar(user1)
            #avatar2 = await self.get_avatar(user2)
            if locale == "es-ES":
                message = f"{name1} ha enviado una carta de San Valentín a {user2.mention}!"
            else:
                message = f"{user2.mention} has received a valentine card from {name1}!"

            # Update the count of letters received
            async with self.config.letters_received() as letters_received:
                if str(user2.id) not in letters_received:
                    letters_received[str(user2.id)] = 0
                letters_received[str(user2.id)] += 1
                received_count = letters_received[str(user2.id)]

            image = self.generate_image(ctx, avatar1, name1, name2)
            embed = discord.Embed(
                
                description=f"** {message} **",
                color=discord.Colour.from_rgb(255, 105, 180),
            )

            embed.set_image(url="attachment://valentine.png")
            embed.set_footer(text=f"{user2.display_name} has received {received_count} valentine letters.")

            await ctx.send(file=image, embed=embed)



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

    def generate_image(self, ctx, avatar1, name1, name2):
        image_path = choice(listdir(f"{bundled_data_path(self)}/images/"))
        template = Image.open(
            f"{bundled_data_path(self)}/images/{image_path}", mode="r"
        ).convert("RGBA")
        image = Image.new("RGBA", (720, 377), None)

        avatar1 = self.bytes_to_image(avatar1, 340)

        image.paste(im=avatar1, box=(360, 25))
        image.paste(im=template, box=(0, 0), mask=template)
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(
            f"{bundled_data_path(self)}/Lato-Bold.ttf", size=32, encoding="utf-8"
        )
        draw = ImageDraw.Draw(image)

        x1, y1 = 156, 285
        draw.text((x1-1, y1-1), name1, font=font, fill="black")
        draw.text((x1+1, y1-1), name1, font=font, fill="black")
        draw.text((x1-1, y1+1), name1, font=font, fill="black")
        draw.text((x1+1, y1+1), name1, font=font, fill="black")
        draw.text((x1, y1), name1, font=font, fill="white")

        x2, y2 = 103, 250
        draw.text((x2-1, y2-1), name2, font=font, fill="black")
        draw.text((x2+1, y2-1), name2, font=font, fill="black")
        draw.text((x2-1, y2+1), name2, font=font, fill="black")
        draw.text((x2+1, y2+1), name2, font=font, fill="black")
        draw.text((x2, y2), name2, font=font, fill="white")

        fp = BytesIO()
        image.save(fp, "PNG")
        fp.seek(0)
        image.close()
        _file = discord.File(fp, "valentine.png")
        fp.close()
        return _file
