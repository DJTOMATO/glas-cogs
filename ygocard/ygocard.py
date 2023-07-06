import asyncio
from email.mime import image
from typing import Literal, Optional
import aiohttp
import discord
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .functions import *
from .functions import FuzzyMember
import random
import functools
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify


# Thanks MAX <3
async def __init__(self, red: Red):
    self.bot = red


class YgoCard(commands.Cog):
    """
    Creates YGO Card
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    async def cog_unload(self):
        await self.session.close()

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["ygocard"], cooldown_after_parsing=True)
    async def cardme(self, ctx: commands.Context, member: discord.Member = commands.Author):
        """Make a ygocard..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            # get role of user whoever's target or not
            user = await ctx.guild.get_member(member)
            top_role = user.top_role.name
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_card, ctx, avatar, top_role)
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
        display_avatar: discord.Asset = member.display_avatar.replace(
            size=512, static_format="png"
        )
        await display_avatar.save(avatar, seek_begin=True)
        return avatar

    # async def get_role(self, ctx, member: discord.abc.User):
    #     member = ctx.guild.get_member(client.user.id)
    #     top_role = member.top_role
    #     return top_role

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def gen_card(self, ctx, member_avatar, top_role):
        member_avatar = self.bytes_to_image(member_avatar, 315)
        # base canvas
        im = Image.new("RGBA", (420, 610), None)
        border_list = [
            "DarkSynchro.png",
            "Effect.png",
            "Fusion.png",
            "Link.png",
            "Normal.png",
            "Ritual.png",
            "Skill.png",
            "Spell.png",
            "Synchro.png",
            "Token.png",
            "Trap.png",
            "Xyz.png",
        ]
        border = random.choice(border_list)
        cardmask = Image.open(f"{bundled_data_path(self)}/border/{border}", mode="r").convert(
            "RGBA"
        )
        # pasting the pfp
        im.paste(member_avatar, (51, 110), member_avatar)
        im.paste(cardmask, (0, 0), cardmask)
        # choosing a random attribute
        attribute_list = [
            "Dark.png",
            "Divine.png",
            "Earth.png",
            "Fire.png",
            "Light.png",
            "Spell.png",
            "Trap.png",
            "Water.png",
            "Wind.png",
        ]
        # random item from list

        attribute = random.choice(attribute_list)
        attribute_i = Image.open(
            f"{bundled_data_path(self)}/attribute/{attribute}", mode="r"
        ).convert("RGBA")
        # pasting the attribute
        im.paste(attribute_i, (350, 28), attribute_i)
        # choosing stars
        stars = random.randint(1, 12)
        star_img = Image.open(f"{bundled_data_path(self)}/star/Normal.png", mode="r").convert(
            "RGBA"
        )
        count = 0
        pos = 0
        while stars > count:
            im.paste(star_img, (43 + pos, 73), star_img)
            pos = pos + 29
            count = count + 1
        # adding random atk and def
        # use a truetype font
        try:
            font = ImageFont.truetype(
                f"{bundled_data_path(self)}/fonts/CrimsonText-Regular.ttf", 18
            )

        except ValueError:
            raise ValueError("Error: Algo pasó con {ValueError}")

        atk = random.randint(1, 8) * 1000
        deff = str(random.randint(1, 8) * 1000)
        draw = ImageDraw.Draw(im)
        draw.text((265, 551), f"{atk}", font=font, fill="#000")
        draw.text((350, 551), f"{deff}", font=font, fill="#000")
        # draw user higest role (type)

        rolefont = ImageFont.truetype(f"{bundled_data_path(self)}/fonts/SpectralSC-Bold.ttf", 18)

        draw.text((35, 458), f"[{top_role}]", font=rolefont, fill="#000")
        # im = im._image
        # ending
        cardmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "card.png")
        fp.close()
        return _file


# class YgoCard(commands.Cog):
#     """
#     Creates YGO Card
#     """

#     @commands.command()
#     async def ygo(
#         self,
#         ctx,
#         foil,
#         cardtype,
#         name,
#         level,
#         attribute,
#         setid,
#         creaturetype,
#         desc,
#         atk,
#         defe,
#         pwd,
#         creator,
#         sticker,
#     ):
#         """Searches for pokemons.."""
#         await datacheck(foil, cardtype, name, level,attribute,        setid,
#         creaturetype,
#         desc,
#         atk,
#         defe,
#         pwd,
#         creator,
#         sticker,)
#         # Check Poke 1
#         veri = await VerifyName(names, name1)
#         if veri == False:
#             return await ctx.send(f"The pokemon {name1} does not exist, Please type it again.")
#         else:
#             id1 = 666
#             # Initial check, WILL Get replaced anyways
#         try:
#             # We Assign the ID based on Name
#             id1 = await GetID(names, name1)
#         except ValueError:
#             raise ValueError("Error: Failed to retrieve the ID for the pokemon {name}")
#             em = discord.Embed(description=f"{name1.title()} + {name2.title()} = {name3.title()}")
#             em.title = "Here is your card"
#             em.color = discord.Color(8599000)
#             em.timestamp = datetime.now()
#             em.set_image(url=url3)
#             await ctx.send(embed=em)
