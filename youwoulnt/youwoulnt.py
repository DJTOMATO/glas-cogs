"""
MIT License

Copyright (c) 2020-present phenom4n4n

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
from email.mime import image
import functools
from io import BytesIO
from typing import Literal, Optional
import textwrap
import aiohttp
import discord
import urllib
from PIL import Image, ImageDraw, ImageFont
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

from .converters import FuzzyMember


class Youwoulnt(commands.Cog):
    """
   You wouln't
    """

    __version__ = "1.1.1"

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
    
    def parse_text(self, text):
        return urllib.parse.quote(text)  
      
    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def youwo(self, ctx, *, text: commands.clean_content(fix_channel_mentions=True)):
        """You wouln't steal a meme..."""
        text = self.parse_text(text)
        async with ctx.typing():
            task = functools.partial(self.gen_woulnt, ctx, text)
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


    def gen_woulnt(self, ctx, text):
        
        # base canvas
        im = Image.new("RGBA", (818, 574), None)
        image = Image.open(f"{bundled_data_path(self)}/you/you.png", mode="r").convert(
            "RGBA"
        )
        im.paste(image, (0, 0), image)
        texto = self.parse_text(text)
        font = ImageFont.truetype(f"{bundled_data_path(self)}/xband-ro.ttf", 70)
        canvas = ImageDraw.Draw(im)
        
        margin = offset = 50
        for line in textwrap.wrap(texto, width=40):
            canvas.text((margin, offset), line, font=font, fill="#FFFFFF", align="center", stroke_width=1, stroke_fill=(169,169,169))
            offset += font.getsize(line)[1]       

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "woulnt.png")
        fp.close()
        return _file

