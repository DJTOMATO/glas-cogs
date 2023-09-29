import asyncio

import functools
from io import BytesIO
from typing import Literal
import textwrap
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class Youwouldnt(commands.Cog):
    """
    Youwouldnt
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=82345678897346,
            force_registration=True,
        )
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        return

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def youwo(self, ctx, *, text: commands.clean_content(fix_channel_mentions=True)):
        """You wouln't steal a meme..."""

        async with ctx.typing():
            task = functools.partial(self.gen_wouldnt, ctx, text)
            image = await self.generate_image(ctx, task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    async def generate_image(self, ctx: commands.Context, task: functools.partial):
        task = self.bot.loop.run_in_executor(None, task)
        try:
            image = await asyncio.wait_for(task, timeout=60)
        except asyncio.TimeoutError:
            return "An error occurred while generating this image. Try again later."
        else:
            return image

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.ANTIALIAS)
        return image

    def gen_wouldnt(self, ctx, text):
        # base canvas
        im = Image.new("RGBA", (818, 574), None)
        image = Image.open(f"{bundled_data_path(self)}/you/you.png", mode="r").convert("RGBA")
        im.paste(image, (0, 0), image)

        font = ImageFont.truetype(f"{bundled_data_path(self)}/xband-ro.ttf", 130)
        canvas = ImageDraw.Draw(im)

        margin = 40
        offset = 60

        for line in textwrap.wrap(text, width=13):
            canvas.text(
                (margin + 30, offset + 50),
                line,
                font=font,
                spacing=500,
                fill="#FFFFFF",
                align="center",
                stroke_width=1,
                stroke_fill=(169, 169, 169),
            )
            offset += font.getsize(line)[1]

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "woulnt.png")
        fp.close()
        return _file
