from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.data_manager import bundled_data_path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import asyncio
import discord
import random
import functools
import textwrap
from .functions import *
from .functions import FuzzyMember
import regex as re
from typing import Optional


class YgoCard(commands.Cog):
    """
    Creates YGO Card
    """

    # Thanks MAX <3
    def __init__(self, bot: Red) -> None:
        self.bot = bot

    __version__ = "1.0.0"

    @commands.bot_has_permissions(attach_files=True)
    # @commands.cooldown(1, 10, commands.BucketType.user) Until cog is totally working
    @commands.command(aliases=["ygocard"], cooldown_after_parsing=True)
    # Thanks Kowlin! <3
    async def cardme(self, ctx, member: discord.Member, skill_text: Optional[str]) -> str:
        """Make a ygocard..."""
        if not member:
            member = ctx.author
        # Thanks Kowlin! <3
        if skill_text is not None:
            pass
        else:
            skill_text = "You didn't set a card description! Silly~"
        if len(skill_text) > 193:
            raise ValueError("Error: Skill Text cannot be longer than 193 characters")
        if len(skill_text) < 3:
            skill_text = "You didn't set a card description! Silly~"
        aa = str(member.nick)

        card_name = await self.sanitize_string(aa)
        a = str(member.top_role)
        highest_role_name = await self.sanitize_string(a)
        b = str(ctx.guild.name)
        server_name = await self.sanitize_string(b)
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(
                self.gen_card, ctx, avatar, highest_role_name, skill_text, card_name, server_name
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
            return "An error occurred while generating this image. Try again later."
        else:
            return image

    async def sanitize_string(self, input_string):
        sanitized_string = re.sub(r"[^a-zA-Z\s]", "", input_string)
        return sanitized_string

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

    # Thanks Phen!
    def gen_card(self, ctx, member_avatar, top_role, skill, card_name, server_name):
        member_avatar = self.bytes_to_image(member_avatar, 325)
        # base canvas
        im = Image.new("RGBA", (420, 610), None)
        border_list = [
            "DarkSynchro.png",
            "Effect.png",
            "Fusion.png",
            "Normal.png",
            "Ritual.png",
            "Skill.png",
            "Spell.png",
            "Synchro.png",
            "Token.png",
            "Trap.png",
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
        # adding stars
        while stars > count:
            im.paste(star_img, (43 + pos, 73), star_img)
            pos = pos + 29
            count = count + 1
        # adding random atk and def
        # Theres no need to write atk/def if the card is not a monster
        nonmonstercards = ["Skill.png", "Spell.png", "Trap.png"]
        draw = ImageDraw.Draw(im)
        if border not in nonmonstercards:
            font = ImageFont.truetype(
                f"{bundled_data_path(self)}/fonts/CrimsonText-Regular.ttf", 18
            )
            atk = random.randint(1, 8) * 1000
            deff = str(random.randint(1, 8) * 1000)

            draw.text((265, 551), f"{atk}", font=font, fill="#000")
            draw.text((350, 551), f"{deff}", font=font, fill="#000")

        # draw card skill
        skillfont = ImageFont.truetype(f"{bundled_data_path(self)}/fonts/Amiri-Regular.ttf", 16)
        # Previous method, might work worse than current one
        # draw.text((345, 551), f"[{skill}]", font=skillfont, fill="#000", align = "right")
        lines = textwrap.wrap(skill, width=50)
        draw.multiline_text((35, 475), "\n".join(lines), font=skillfont, fill="#000", spacing=0)

        # draw user higest role (type)
        rolefont = ImageFont.truetype(f"{bundled_data_path(self)}/fonts/SpectralSC-Bold.ttf", 18)
        draw.text((35, 454), f"[{top_role}]", font=rolefont, fill="#000")

        # draw card(username)
        namefont = ImageFont.truetype(
            f"{bundled_data_path(self)}/fonts/Matrix-Regular-Small-Caps.otf", 32
        )
        draw.text((32, 34), f"{card_name}", font=namefont, fill="#000")

        # draw serial(servername)
        serverfont = ImageFont.truetype(f"{bundled_data_path(self)}/fonts/Matrix-Book.ttf", 14)
        draw.text(
            (26, 583), f"Card made at: {server_name}", font=serverfont, fill="#000", align="left"
        )
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
