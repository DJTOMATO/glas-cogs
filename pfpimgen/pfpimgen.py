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
import random
import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageSequence
import numpy as np
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import pagify

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

from .converters import FuzzyMember


class PfpImgen(commands.Cog):
    """
    Make images from avatars!
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

    async def send_with_retries(self, ctx, content=None, file=None, retries=3, delay=2):
        for attempt in range(retries):
            try:
                if file:
                    await ctx.send(file=file)
                else:
                    await ctx.send(content)
                return  # If successful, exit the function
            except discord.errors.DiscordServerError as e:
                if attempt < retries - 1:
                    await asyncio.sleep(delay)  # Wait before retrying
                    delay *= 2  # Exponential backoff
                else:
                    await ctx.send(
                        f"Failed to send message after {retries} attempts. Error: {e}"
                    )

    async def cog_unload(self):
        await self.session.close()

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        return

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["catgirl"], cooldown_after_parsing=True)
    async def ineko(self, ctx, *, member: FuzzyMember = None):
        """Make a neko avatar..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_neko, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["ameto"], cooldown_after_parsing=True)
    async def dj(self, ctx, *, member: FuzzyMember = None):
        """Make a DJ..."""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ameto, ctx, avatar, username)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["discord"], cooldown_after_parsing=True)
    async def cloudflare(self, ctx, *, member: FuzzyMember = None):
        """Cloudflare someone!..."""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_discord, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["youu"], cooldown_after_parsing=True)
    async def you(self, ctx, *, member: FuzzyMember = None):
        """Make a you avatar..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_you, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["mrbest"], cooldown_after_parsing=True)
    async def fraud(self, ctx, *, member: FuzzyMember = None):
        """He's a fraud..."""
        if member:
            async with ctx.typing():
                # t = ctx.author
                # avatar = await self.get_avatar(t)
                # target = await self.get_avatar(member)
                user = ctx.author
                target = member

                member_avatar = await self.get_avatar(ctx.author)
                target_avatar = await self.get_avatar(target)

                member_name = user.name
                target_name = target.name

                task = functools.partial(
                    self.gen_fraud,
                    ctx,
                    member_avatar,
                    member_name,
                    target_avatar,
                    target_name,
                )
                image = await self.generate_image(task)
            if isinstance(image, str):
                await ctx.send(image)
            else:
                await ctx.send(file=image)
        else:
            await ctx.send("You must target someone!")

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["fumopicture"], cooldown_after_parsing=True)
    async def fumopic(self, ctx, *, member: FuzzyMember = None):
        """Remilia caughts you in 4K..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_fumopic, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["gos"], cooldown_after_parsing=True)
    async def gosling(self, ctx, *, member: FuzzyMember = None):
        """Totally not gosling at all..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_gosling, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["selfie"], cooldown_after_parsing=True)
    async def marisa(self, ctx, *, member: FuzzyMember = None):
        """Selfie with Marisa..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_marisa, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["youcould"], cooldown_after_parsing=True)
    async def religion(self, ctx, *, member: FuzzyMember = None):
        """We could make a religion out off this!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_religion, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["nepnep"], cooldown_after_parsing=True)
    async def nep(self, ctx, *, member: FuzzyMember = None):
        """Rom & Ram spooked at you..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_nep, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["playbetter"], cooldown_after_parsing=True)
    async def better(self, ctx, *, member: FuzzyMember = None):
        """Play better games..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_better, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["liar"], cooldown_after_parsing=True)
    async def lies(self, ctx, *, member: FuzzyMember = None):
        """Don't believe his lies..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_lies, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["lookat"], cooldown_after_parsing=True)
    async def ahri(self, ctx, *, member: FuzzyMember = None):
        """Look at this shit..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ahri, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["otsucringe"], cooldown_after_parsing=True)
    async def pippa(self, ctx, *, member: FuzzyMember = None):
        """Pippa stares at you..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_pippa, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["sapeado"], cooldown_after_parsing=True)
    async def cage(self, ctx, *, member: FuzzyMember = None):
        """to the cage..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_jail, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await self.send_with_retries(ctx, content=image)
        else:
            await self.send_with_retries(ctx, file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["inapic"], cooldown_after_parsing=True)
    async def ina(self, ctx, *, member: FuzzyMember = None):
        """Ina is totally disgusted at you..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ina, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["nofunallowed"], cooldown_after_parsing=True)
    async def nofun(self, ctx, *, member: FuzzyMember = None):
        """No fun allowed!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_nofun, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["emiko"], cooldown_after_parsing=True)
    async def elite(self, ctx, *, member: FuzzyMember = None):
        """Elite Miko!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_elite, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def conference(self, ctx, *, member: FuzzyMember = None):
        """Well well, what do you have to say?..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ogey, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def doctor(self, ctx, *, member: FuzzyMember = None):
        """The Doctor is IN..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_doctor, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def bonk(self, ctx, *, member: FuzzyMember = None):
        """Bonk! Go to horny jail."""

        async with ctx.typing():
            bonker = False
            if member:
                bonker = ctx.author
            else:
                member = ctx.author
            victim_avatar = await self.get_avatar(member)
            if bonker:
                bonker_avatar = await self.get_avatar(bonker)
                task = functools.partial(
                    self.gen_bonk, ctx, victim_avatar, bonker_avatar
                )
            else:
                task = functools.partial(self.gen_bonk, ctx, victim_avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def simp(self, ctx, *, member: FuzzyMember = None):
        """You are now a simp."""
        if not member:
            member = ctx.author
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_simp, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def banner(self, ctx, *, member: FuzzyMember = None):
        """To war we go!"""
        if not member:
            member = ctx.author
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_banner, ctx, avatar, member.color)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def nickel(
        self,
        ctx,
        member: Optional[FuzzyMember] = None,
        *,
        text: commands.clean_content(fix_channel_mentions=True),
    ):
        """If I had a nickel for everytime someone ran this command..

        I'd probably have a lot."""
        text = " ".join(text.split())
        if not member:
            member = ctx.author
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_nickel, ctx, avatar, text[:29])
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def stoptalking(
        self,
        ctx,
        member: Optional[FuzzyMember] = None,
        *,
        text: commands.clean_content(fix_channel_mentions=True),
    ):
        """Tell someone to stop blabbering away"""
        text = " ".join(text.split())
        if not member:
            member = ctx.author
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_stop, ctx, avatar, text)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def horny(self, ctx, *, member: FuzzyMember = None):
        """Assign someone a horny license."""
        member = member or ctx.author
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_horny, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def shutup(
        self,
        ctx,
        member: Optional[FuzzyMember] = None,
        *,
        text: commands.clean_content(fix_channel_mentions=True),
    ):
        """Will you shutup, man"""
        text = " ".join(text.split())
        if not member:
            biden = None
            member = ctx.author
        else:
            biden = ctx.author
        async with ctx.typing():
            trump = await self.get_avatar(member)
            if biden:
                biden = await self.get_avatar(biden)
            task = functools.partial(
                self.gen_shut, ctx, trump, text, biden_avatar=biden
            )
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def ahoy(self, ctx, *, member: FuzzyMember = None):
        """You and Marine <3..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ahoy, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def waku(self, ctx, *, member: FuzzyMember = None):
        """Certified WakuWaku moment..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_waku, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def idiot(self, ctx, *, member: FuzzyMember = None):
        """You're a fucking idiot..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_idiot, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def sanic(self, ctx, *, member: FuzzyMember = None):
        """Sonic Celebrates..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_sanic, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def thrilled(self, ctx, *, member: FuzzyMember = None):
        """Thrilled..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_thrilled, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def kowone(self, ctx, *, member: FuzzyMember = None):
        """Korone......"""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_kowone, ctx, avatar, username)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def funado(self, ctx, *, member: FuzzyMember = None):
        """Estoy funado..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_funado, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def dreams(self, ctx, *, member: FuzzyMember = None):
        """Has soñado..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_dream, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def marihat(self, ctx, *, member: FuzzyMember = None):
        """Marisa Hat..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_marihat, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def thisnow(self, ctx, *, member: FuzzyMember = None):
        """We can end this now..."""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_naruto, ctx, avatar, username)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def didyou(self, ctx, *, member: FuzzyMember = None):
        """Did you know..."""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_didyou, ctx, avatar, username)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def itis(self, ctx, *, member: FuzzyMember = None):
        """You are running out..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_itis, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def slur(self, ctx, *, member: FuzzyMember = None):
        """TIME TO GO CALL SOMEONE A SLUR ON DISCORD!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_slur, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def thejar(self, ctx, *, member: FuzzyMember = None):
        """To the jar!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_jar, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def ipunch(self, ctx, *, member: FuzzyMember = None):
        """Punch somebody!..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_punch, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def mhr(self, ctx, *, member: FuzzyMember = None):
        """My honest reaction..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_mhr, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def denwa(self, ctx, *, member: FuzzyMember = None):
        """Point at..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_point, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def rika(self, ctx, *, member: FuzzyMember = None):
        """Point at..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_rika, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def ireally(self, ctx, *, member: FuzzyMember = None):
        """I really shouln't..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ireally, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def amigo(self, ctx, *, member: FuzzyMember = None):
        """Amigo at..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_amigo, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def secreto(self, ctx, *, member: FuzzyMember = None):
        """El Secreto de la creatividad"""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_creatividad, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def thisuser(self, ctx, *, member: FuzzyMember = None):
        """This user makes me happy"""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_happy, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def competition(self, ctx, *, member: FuzzyMember = None):
        """When you're at a competition"""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_compet, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def sus(self, ctx, *, member: FuzzyMember = None):
        """You're among us..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_sus, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def sugoi(self, ctx, *, member: FuzzyMember = None):
        """You become serval..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_sugoi, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def jack(self, ctx, *, member: FuzzyMember = None):
        """Jack Sparrow's tresaure..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_jack, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def ash(self, ctx, *, member: FuzzyMember = None):
        """You become ash..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_ash, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def pretend(self, ctx, *, member: FuzzyMember = None):
        """You become Essex..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_pretend, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def evidence(self, ctx, *, member: FuzzyMember = None):
        """Here's the photographic evidence..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_evidence, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def taiko(self, ctx, *, member: FuzzyMember = None):
        """Taiko..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_taiko, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def bill(self, ctx, *, member: FuzzyMember = None):
        """You become a billboard..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_bill, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def clowno(self, ctx, *, member: FuzzyMember = None):
        """You become a clown..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_clownoffice, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def bau(self, ctx, *, member: FuzzyMember = None):
        """You become a bau bau..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_bau, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def mygf(self, ctx, *, member: FuzzyMember = None):
        """My girlfriend..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_mygf, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def huaso(self, ctx, *, member: FuzzyMember = None):
        """Tikitikiti..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_chupalla, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(cooldown_after_parsing=True)
    async def honestly(self, ctx, *, member: FuzzyMember = None):
        """Quite incredible..."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_honestly, ctx, avatar)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["olreliable"], cooldown_after_parsing=True)
    async def reliable(self, ctx, *, member: FuzzyMember = None):
        """Call the ol' reliable..."""
        if not member:
            member = ctx.author
        username = member.display_name
        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_reliable, ctx, avatar, username)
            image = await self.generate_image(task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    # @commands.bot_has_permissions(attach_files=True)
    # @commands.cooldown(1, 10, commands.BucketType.user)
    # @commands.command(cooldown_after_parsing=True)
    # async def petpet(self, ctx: commands.Context, member: FuzzyMember = None):
    #     """petpet someone"""
    #     member = member or ctx.author
    #     async with ctx.typing():
    #         params = {"avatar": member.display_avatar.replace(format="png").url}
    #         url = "https://api.popcat.xyz/pet"
    #         async with self.session.get(url, params=params) as resp:
    #             if resp.status != 200:
    #                 return await ctx.send(
    #                     "An error occurred while generating this image. Try again later."
    #                 )
    #             image = await resp.read()
    #         fp = BytesIO(image)
    #         fp.seek(0)
    #         file = discord.File(fp, "petpet.gif")
    #         fp.close()
    #     await ctx.send(file=file)

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

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.LANCZOS)
        return image

    def gen_neko(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 156)
        # base canvas
        im = Image.new("RGBA", (500, 750), None)
        # neko = Image.open(f"{bundled_data_path(self)}/neko/neko.png", mode="r").convert("RGBA")
        nekomask = Image.open(
            f"{bundled_data_path(self)}/neko/nekomask.png", mode="r"
        ).convert("RGBA")
        # im.paste(neko, (0, 0), neko)

        # pasting the pfp
        im.paste(member_avatar, (149, 122), member_avatar)
        im.paste(nekomask, (0, 0), nekomask)
        nekomask.close()
        member_avatar.close()
        # uppy test
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "neko.png")
        fp.close()
        return _file

    def gen_nofun(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 155)

        # base canvas
        im = Image.new("RGBA", (512, 512), None)

        # neko = Image.open(f"{bundled_data_path(self)}/nofun/nofun.png", mode="r").convert("RGBA")
        nofunmask = Image.open(
            f"{bundled_data_path(self)}/nofun/nofunmask.png", mode="r"
        ).convert("RGBA")
        # im.paste(neko, (0, 0), neko)
        #        im = Image.FLIP_LEFT_RIGHT()
        # pasting the pfp
        im.paste(member_avatar, (140, 8), member_avatar)
        im.paste(nofunmask, (0, 0), nofunmask)
        nofunmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "nofun.png")
        fp.close()
        return _file

    def gen_ogey(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 228)
        # base canvas
        im = Image.new("RGBA", (960, 540), None)
        # ogey = Image.open(f"{bundled_data_path(self)}/ogey/ogey.png", mode="r").convert("RGBA")
        ogeymask = Image.open(
            f"{bundled_data_path(self)}/ogey/ogeymask.png", mode="r"
        ).convert("RGBA")
        # im.paste(ogey, (0, 0), ogey)

        # pasting the pfp
        im.paste(member_avatar, (585, 119), member_avatar)
        im.paste(ogeymask, (0, 0), ogeymask)
        ogeymask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ogey.png")
        fp.close()
        return _file

    def gen_elite(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 180)
        # base canvas
        im = Image.new("RGBA", (799, 555), None)
        # ogey = Image.open(f"{bundled_data_path(self)}/ogey/ogey.png", mode="r").convert("RGBA")
        elitemask = Image.open(
            f"{bundled_data_path(self)}/elitemath/elite_mask.png", mode="r"
        ).convert("RGBA")
        eliteeyes = Image.open(
            f"{bundled_data_path(self)}/elitemath/elite_eyes.png", mode="r"
        ).convert("RGBA")
        # im.paste(ogey, (0, 0), ogey)

        # pasting the pfp
        im.paste(elitemask, (0, 0), elitemask)
        im.paste(member_avatar, (570, 320), member_avatar)

        # im.paste(eliteeyes, (592, 405), eliteeyes)

        eliteeyes.close()
        elitemask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "elitemiko.png")
        fp.close()
        return _file

    def gen_doctor(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 160)
        # base canvas
        im = Image.new("RGBA", (612, 612), None)
        # doctor = Image.open(f"{bundled_data_path(self)}/doctor/doctor.png", mode="r").convert("RGBA")
        doctormask = Image.open(
            f"{bundled_data_path(self)}/doctor/doctormask.png", mode="r"
        ).convert("RGBA")
        # im.paste(doctor, (0, 0), ogey)

        # pasting the pfp
        im.paste(member_avatar, (110, 150), member_avatar)
        im.paste(doctormask, (0, 0), doctormask)
        doctormask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "doctor.png")
        fp.close()
        return _file

    def gen_bonk(self, ctx, victim_avatar, bonker_avatar=None):
        # base canvas
        im = Image.open(
            f"{bundled_data_path(self)}/bonk/bonkbase.png", mode="r"
        ).convert("RGBA")

        # pasting the victim
        victim_avatar = self.bytes_to_image(victim_avatar, 256)
        victim_avatar = victim_avatar.rotate(angle=10, resample=Image.BILINEAR)
        im.paste(victim_avatar, (650, 225), victim_avatar)
        victim_avatar.close()

        # pasting the bonker
        if bonker_avatar:
            bonker_avatar = self.bytes_to_image(bonker_avatar, 223)
            im.paste(bonker_avatar, (206, 69), bonker_avatar)
            bonker_avatar.close()

        # pasting the bat
        bonkbat = Image.open(
            f"{bundled_data_path(self)}/bonk/bonkbat.png", mode="r"
        ).convert("RGBA")
        im.paste(bonkbat, (452, 132), bonkbat)
        bonkbat.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "bonk.png")
        fp.close()
        return _file

    def gen_simp(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 136)
        # base canvas
        im = Image.new("RGBA", (500, 319), None)
        card = Image.open(f"{bundled_data_path(self)}/simp/simp.png", mode="r").convert(
            "RGBA"
        )

        # pasting the pfp
        member_avatar = member_avatar.rotate(
            angle=3, resample=Image.BILINEAR, expand=True
        )
        im.paste(member_avatar, (73, 105))
        member_avatar.close()

        # pasting the card
        im.paste(card, (0, 0), card)
        card.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "simp.png")
        fp.close()
        return _file

    def gen_banner(self, ctx, member_avatar, color: discord.Color):
        im = Image.new("RGBA", (489, 481), color.to_rgb())
        comic = Image.open(
            f"{bundled_data_path(self)}/banner/banner.png", mode="r"
        ).convert("RGBA")
        member_avatar = self.bytes_to_image(member_avatar, 200)

        # 2nd slide
        av = member_avatar.rotate(angle=7, resample=Image.BILINEAR, expand=True)
        av = av.resize((90, 90), Image.LANCZOS)
        im.paste(av, (448, 38), av)

        # 3rd slide
        av2 = member_avatar.rotate(angle=7, resample=Image.BILINEAR, expand=True)
        av2 = av2.resize((122, 124), Image.LANCZOS)
        im.paste(av2, (47, 271), av2)

        # 4th slide
        av3 = member_avatar.rotate(angle=26, resample=Image.BILINEAR, expand=True)
        av3 = av3.resize((147, 148), Image.LANCZOS)
        im.paste(av2, (345, 233), av2)

        av.close()
        av2.close()
        av3.close()
        member_avatar.close()

        # cover = Image.open(f"{bundled_data_path(self)}/banner/bannercover.png", mode="r").convert("RGBA")
        # im.paste(cover, (240, 159), cover)
        im.paste(comic, (0, 0), comic)

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "banner.png")
        fp.close()
        return _file

    def gen_nickel(self, ctx, member_avatar, text: str):
        member_avatar = self.bytes_to_image(member_avatar, 182)
        # base canvas
        im = Image.open(
            f"{bundled_data_path(self)}/nickel/nickel.png", mode="r"
        ).convert("RGBA")

        # avatars
        im.paste(member_avatar, (69, 70), member_avatar)
        im.paste(member_avatar, (69, 407), member_avatar)
        im.paste(member_avatar, (104, 758), member_avatar)
        member_avatar.close()

        # text
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", 30)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(text, font, stroke_width=2)
        canvas.text(
            ((im.width - text_width) / 2, 285),
            text,
            font=font,
            fill=(206, 194, 114),
            align="center",
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "nickel.png")
        fp.close()
        return _file

    def circle_avatar(self, avatar):
        mask = Image.new("L", avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    def gen_stop(self, ctx, member_avatar, text: str):
        member_avatar = self.bytes_to_image(member_avatar, 140)
        # base canvas
        im = Image.open(f"{bundled_data_path(self)}/stop/stop.png", mode="r").convert(
            "RGBA"
        )

        # avatars
        circle_main = self.circle_avatar(member_avatar).rotate(
            angle=57, resample=Image.BILINEAR, expand=True
        )
        im.paste(circle_main, (84, 207), circle_main)
        im.paste(circle_main, (42, 864), circle_main)
        member_avatar.close()
        circle_main.close()

        # text
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", 25)
        canvas = ImageDraw.Draw(im)
        y = 70
        pages = list(pagify(text, [" "], page_length=30))[:4]
        for page in pages:
            text_width, text_height = canvas.textsize(page, font, stroke_width=2)
            x = ((im.width + 40) - text_width) / 2
            canvas.text(
                (x, y),
                page,
                font=font,
                fill=(255, 255, 255),
                align="center",
                spacing=2,
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )
            y += 25

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "horny.png")
        fp.close()
        return _file

    def gen_horny(self, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 85)
        # base canvas
        im = Image.new("RGBA", (360, 300), None)
        card = Image.open(
            f"{bundled_data_path(self)}/horny/horny.png", mode="r"
        ).convert("RGBA")

        # pasting the pfp
        member_avatar = member_avatar.rotate(
            angle=22, resample=Image.BILINEAR, expand=True
        )
        im.paste(member_avatar, (43, 117))
        member_avatar.close()

        # pasting the card
        im.paste(card, (0, 0), card)
        card.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "horny.png")
        fp.close()
        return _file

    def gen_shut(self, ctx, member_avatar, text: str, *, biden_avatar=None):
        member_avatar = self.bytes_to_image(member_avatar, 135)
        # base canvas
        im = Image.open(
            f"{bundled_data_path(self)}/shutup/shutup.png", mode="r"
        ).convert("RGBA")

        # avatars
        im.paste(member_avatar, (49, 2), member_avatar)
        member_avatar.close()
        if biden_avatar:
            biden_avatar = self.bytes_to_image(biden_avatar, 178)
            im.paste(biden_avatar, (372, 0), biden_avatar)

        # text
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", 20)
        canvas = ImageDraw.Draw(im)
        pages = list(pagify(text, [" "], page_length=40))[:2]
        y = 250 - (len(pages) * 25)
        for page in pages:
            text_width, text_height = canvas.textsize(page, font, stroke_width=2)
            x = ((im.width - 300) - text_width) / 2
            canvas.text(
                (x, y),
                page,
                font=font,
                fill=(255, 255, 255),
                align="center",
                spacing=2,
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )
            y += 25

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "shutup.png")
        fp.close()
        return _file

    def gen_ahoy(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 150)
        im = Image.new("RGBA", (640, 527), None)
        ahoymask = Image.open(
            f"{bundled_data_path(self)}/ahoy/ahoymask.png", mode="r"
        ).convert("RGBA")
        member_avatar = member_avatar.rotate(41, Image.NEAREST, expand=1)
        im.paste(member_avatar, (280, 310), member_avatar)
        im.paste(ahoymask, (0, 0), ahoymask)
        ahoymask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ahoy.png")
        fp.close()
        return _file

    def gen_waku(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        im = Image.new("RGBA", (720, 675), None)

        wakumask = Image.open(
            f"{bundled_data_path(self)}/waku/waku_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (100, 90), member_avatar)
        im.paste(wakumask, (0, 0), wakumask)
        wakumask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "waku.png")
        fp.close()
        return _file

    def gen_idiot(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 300)
        im = Image.new("RGBA", (600, 416), None)

        idiotmask = Image.open(
            f"{bundled_data_path(self)}/idiot/idiot_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (150, 40), member_avatar)
        im.paste(idiotmask, (0, 0), idiotmask)
        idiotmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "idiot.png")
        fp.close()
        return _file

    # Your function definition
    def gen_honestly(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 400)
        member_avatar = member_avatar.resize((200, 800))
        im = Image.new("RGBA", (645, 341), None)
        im2 = Image.new("RGBA", (645, 341), None)

        step1 = Image.open(
            f"{bundled_data_path(self)}/honesty/frame_0.png", mode="r"
        ).convert("RGBA")

        step2 = Image.open(
            f"{bundled_data_path(self)}/honesty/frame_1.png", mode="r"
        ).convert("RGBA")

        im.paste(step1, (0, 0), step1)
        im.paste(member_avatar, (450, -300), member_avatar)

        im2.paste(step1, (0, 0), step1)
        im2.paste(member_avatar, (450, -300), member_avatar)
        im2.paste(step2, (0, 0), step2)

        # Create a list of frames
        frames = [im, im2]

        # Create a BytesIO object to hold the GIF
        gif_data = BytesIO()

        # Create a GIF from the frames
        frames[0].save(
            gif_data,
            save_all=True,
            append_images=frames[1:],
            format="GIF",
            duration=50,  # Adjust the duration (in milliseconds) as needed
            loop=0,  # Set loop to 0 for an infinite loop
        )

        gif_data.seek(0)

        _file = discord.File(gif_data, "honesty.gif")

        return _file

    def gen_you(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 130)

        im = Image.new("RGBA", (717, 642), None)

        youmask = Image.open(
            f"{bundled_data_path(self)}/you/you_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (280, 140), member_avatar)
        im.paste(youmask, (0, 0), youmask)
        youmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "you.png")
        fp.close()
        return _file

    def gen_fumopic(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 260)

        im = Image.new("RGBA", (451, 600), None)

        fumopicmask = Image.open(
            f"{bundled_data_path(self)}/fumopic/fumopic_mask.png", mode="r"
        ).convert("RGBA")

        member_avatar = member_avatar.rotate(315, Image.NEAREST, expand=1)
        im.paste(member_avatar, (120, 200), member_avatar)
        im.paste(fumopicmask, (0, 0), fumopicmask)
        fumopicmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "fumopic.png")
        fp.close()
        return _file

    def gen_ina(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 270)

        im = Image.new("RGBA", (600, 338), None)

        inamask = Image.open(
            f"{bundled_data_path(self)}/ina/ina_mask.png", mode="r"
        ).convert("RGBA")

        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(member_avatar, (105, 75), member_avatar)
        im.paste(inamask, (0, 0), inamask)
        inamask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "inapic.png")
        fp.close()
        return _file

    def gen_gosling(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 250)
        # base canvas
        im = Image.new("RGBA", (512, 512), None)

        gosmask = Image.open(
            f"{bundled_data_path(self)}/gosling/gosling_mask.png", mode="r"
        ).convert("RGBA")

        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(member_avatar, (50, 0), member_avatar)
        im.paste(gosmask, (0, 0), gosmask)
        gosmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "gosling.png")
        fp.close()
        return _file

    def gen_marisa(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 577)

        im = Image.new("RGBA", (433, 577), None)

        marisamask = Image.open(
            f"{bundled_data_path(self)}/marisa/marisa_mask.png", mode="r"
        ).convert("RGBA")

        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(marisamask, (0, 0), marisamask)
        marisamask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "marisa.png")
        fp.close()
        return _file

    def gen_thrilled(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 155)

        im = Image.new("RGBA", (863, 509), None)

        handmask = Image.open(
            f"{bundled_data_path(self)}/hand/hand_mask.png", mode="r"
        ).convert("RGBA")

        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(handmask, (0, 0), handmask)
        im.paste(member_avatar, (184, 95), member_avatar)

        handmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "thrilled.png")
        fp.close()
        return _file

    def gen_religion(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 520)

        im = Image.new("RGBA", (520, 612), None)

        religionmask = Image.open(
            f"{bundled_data_path(self)}/religion/religion_mask.png", mode="r"
        ).convert("RGBA")

        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(religionmask, (0, 0), religionmask)
        religionmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "religion.png")
        fp.close()
        return _file

    def gen_nep(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 768)
        # base canvas
        im = Image.new("RGBA", (768, 563), None)

        nepmask = Image.open(
            f"{bundled_data_path(self)}/nep/nep_mask.png", mode="r"
        ).convert("RGBA")
        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.paste(member_avatar, (0, -20), member_avatar)
        im.paste(nepmask, (0, 0), nepmask)
        nepmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "nep.png")
        fp.close()
        return _file

    def gen_lies(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 435)

        member_avatar = member_avatar.rotate(46, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (701, 461), None)
        liesmask = Image.open(
            f"{bundled_data_path(self)}/lies/lies_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (-83, -250), member_avatar)
        im.paste(liesmask, (0, 0), liesmask)
        liesmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "lies.png")
        fp.close()
        return _file

    def gen_ahri(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 250)

        member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        im = Image.new("RGBA", (554, 650), None)
        liesmask = Image.open(
            f"{bundled_data_path(self)}/ahri/ahri_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (295, 110), member_avatar)
        im.paste(liesmask, (0, 0), liesmask)
        liesmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ahri.png")
        fp.close()
        return _file

    def gen_pippa(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 120)
        im = Image.new("RGBA", (940, 339), None)
        pippamask = Image.open(
            f"{bundled_data_path(self)}/pippa/pippa_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (327, 130), member_avatar)
        im.paste(pippamask, (0, 0), pippamask)
        pippamask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "pippa.png")
        fp.close()
        return _file

    def gen_jail(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 120)

        im = Image.new("RGBA", (800, 640), None)
        jailmask = Image.open(
            f"{bundled_data_path(self)}/jail/jail_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (330, 230), member_avatar)
        im.paste(jailmask, (0, 0), jailmask)
        jailmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "jail.png")
        fp.close()
        return _file

    def gen_sanic(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 190)

        im = Image.new("RGBA", (494, 557), None)
        sanicmask = Image.open(
            f"{bundled_data_path(self)}/sanic/sanic_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (50, 100), member_avatar)
        im.paste(sanicmask, (0, 0), sanicmask)
        sanicmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "sanic.png")
        fp.close()
        return _file

    def gen_funado(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 450)

        im = Image.new("RGBA", (960, 958), None)
        funamask = Image.open(
            f"{bundled_data_path(self)}/funado/funado.jpg", mode="r"
        ).convert("RGBA")

        im.paste(funamask, (0, 0), funamask)
        im.paste(member_avatar, (220, 30), member_avatar)

        funamask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "funado.png")
        fp.close()
        return _file

    def gen_dream(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 750)

        im = Image.new("RGBA", (913, 960), None)
        dreammask = Image.open(
            f"{bundled_data_path(self)}/dream/dream_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (60, 110), member_avatar)
        im.paste(dreammask, (0, 0), dreammask)
        dreammask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "dream.png")
        fp.close()
        return _file

    def gen_marihat(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 262)

        im = Image.new("RGBA", (262, 262), None)
        marimask = Image.open(
            f"{bundled_data_path(self)}/marihat/mari_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(marimask, (0, 0), marimask)
        marimask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "dream.png")
        fp.close()
        return _file

    def gen_naruto(self, ctx, member_avatar, username):
        member_avatar = self.bytes_to_image(member_avatar, 500)

        # base canvas
        im = Image.new("RGBA", (720, 720), None)
        narumask = Image.open(
            f"{bundled_data_path(self)}/naruto/naru_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(narumask, (0, 0), narumask)
        narumask.close()
        member_avatar.close()
        text = username
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", 30)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(text, font, stroke_width=1)
        canvas.text(
            (250, 530),
            text,
            font=font,
            fill=(0, 0, 0),
            align="left",
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )

        fp = BytesIO()
        im.save(fp, "PNG")
        # test
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "naruto.png")
        fp.close()
        return _file

    def gen_itis(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (600, 600), None)
        itismask = Image.open(
            f"{bundled_data_path(self)}/itis/itis_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(itismask, (0, 0), itismask)
        itismask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "itis.png")
        fp.close()
        return _file

    def gen_slur(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (600, 600), None)
        slurmask = Image.open(
            f"{bundled_data_path(self)}/slur/slur_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(slurmask, (0, 0), slurmask)
        slurmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "slur.png")
        fp.close()
        return _file

    def gen_jar(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (600, 600), None)
        jarmask = Image.open(
            f"{bundled_data_path(self)}/jar/jar_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(jarmask, (0, 0), jarmask)
        jarmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "jar.png")
        fp.close()
        return _file

    def gen_punch(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (600, 600), None)
        punchmask = Image.open(
            f"{bundled_data_path(self)}/punch/punch_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(punchmask, (0, 0), punchmask)
        punchmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "punch.png")
        fp.close()
        return _file

    def gen_mhr(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 650)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (602, 602), None)
        mhrmask = Image.open(
            f"{bundled_data_path(self)}/mhr/mhr_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 80), member_avatar)
        im.paste(mhrmask, (0, 0), mhrmask)
        mhrmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "mhr.png")
        fp.close()
        return _file

    def gen_rika(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 150)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (640, 640), None)
        mhrmask = Image.open(
            f"{bundled_data_path(self)}/rika/rika_mask.png", mode="r"
        ).convert("RGBA")

        member_avatar.rotate(
            75, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )
        im.rotate(
            120, resample=0, expand=0, center=None, translate=None, fillcolor=None
        )

        im.paste(member_avatar, (160, 380), member_avatar)
        im.paste(mhrmask, (0, 0), mhrmask)
        mhrmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "nipa.png")
        fp.close()
        return _file

    def gen_point(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 316)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (613, 316), None)
        pointmask = Image.open(
            f"{bundled_data_path(self)}/point/point_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(pointmask, (0, 0), pointmask)
        pointmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "point.png")
        fp.close()
        return _file

    def gen_ireally(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 555)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (555, 553), None)
        ireally = Image.open(
            f"{bundled_data_path(self)}/ireally/ireally.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(ireally, (0, 0), ireally)
        ireally.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ireally.png")
        fp.close()
        return _file

    def gen_amigo(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 256)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (256, 256), None)
        amigomask = Image.open(
            f"{bundled_data_path(self)}/amigo/amigo_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(amigomask, (0, 0), amigomask)
        amigomask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "amigo.png")
        fp.close()
        return _file

    def gen_creatividad(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 350)

        # Create a circular mask
        mask = Image.new("L", member_avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, member_avatar.size[0], member_avatar.size[1]), fill=255)

        # Apply the circular mask to the avatar
        member_avatar.putalpha(mask)

        im = Image.new("RGBA", (458, 612), None)
        creatividad = Image.open(
            f"{bundled_data_path(self)}/creatividad/creatividad.png", mode="r"
        ).convert("RGBA")
        muy = Image.open(
            f"{bundled_data_path(self)}/creatividad/muy.png", mode="r"
        ).convert("RGBA")
        im.paste(creatividad, (0, 0), creatividad)
        im.paste(member_avatar, (50, 100), member_avatar)
        im.paste(muy, (0, 0), muy)
        creatividad.close()
        member_avatar.close()
        muy.close()
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "creatividad.png")
        fp.close()
        return _file

    def gen_happy(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 400)

        # Create a circular mask
        mask = Image.new("L", member_avatar.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, member_avatar.size[0], member_avatar.size[1]), fill=255)

        # Apply the circular mask to the avatar
        member_avatar.putalpha(mask)

        im = Image.new("RGBA", (640, 640), None)
        x = random.randint(1, 3)
        muy = Image.open(f"{bundled_data_path(self)}/happy/{x}.png", mode="r").convert(
            "RGBA"
        )

        im.paste(member_avatar, (10, 140), member_avatar)
        im.paste(muy, (0, 0), muy)
        member_avatar.close()
        muy.close()
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "happy.png")
        fp.close()
        return _file

    def gen_fraud(self, ctx, member_avatar, member_name, target_avatar, target_name):
        abc = member_avatar
        dff = target_avatar
        target_avatar2 = self.bytes_to_image(dff, 55)
        member_avatar = self.bytes_to_image(abc, 110)

        target_avatar = self.bytes_to_image(target_avatar, 520)
        fraud = Image.open(
            f"{bundled_data_path(self)}/fraud/fraud_template.png", mode="r"
        ).convert("RGBA")
        im = Image.new("RGBA", (1024, 693), None)
        im.paste(target_avatar, (308, 10), target_avatar)
        im.paste(member_avatar, (20, 590), member_avatar)
        im.paste(target_avatar2, (110, 385), target_avatar2)
        im.paste(fraud, (0, 0), fraud)

        # Target
        font = ImageFont.truetype(f"{bundled_data_path(self)}/RobotoRegular.ttf", 41)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(target_name, font, stroke_width=2)
        canvas.text(
            (393, 590),
            target_name,
            font=font,
            fill=(0, 0, 0),
            align="center",
            stroke_width=0,
            stroke_fill=(0, 0, 0),
        )
        # Channel name
        font = ImageFont.truetype(f"{bundled_data_path(self)}/RobotoRegular.ttf", 35)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(member_name, font, stroke_width=2)
        canvas.text(
            (152, 643),
            member_name,
            font=font,
            fill=(87, 87, 87),
            align="center",
            stroke_width=0,
            stroke_fill=(0, 0, 0),
        )

        fraud.close()
        target_avatar.close()
        target_avatar2.close()
        member_avatar.close()
        # Left side text
        font = ImageFont.truetype(f"{bundled_data_path(self)}/Roboto-Black.ttf", 20)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(target_name, font, stroke_width=0.5)
        text_width = int(text_width)
        text_height = int(text_height)
        text_img = Image.new("RGBA", (text_width, text_height), (255, 255, 255, 0))
        text_canvas = ImageDraw.Draw(text_img)
        text_canvas.text(
            (0, 0),
            target_name,
            font=font,
            fill=(0, 0, 0),
            align="left",
            stroke_width=0,
            stroke_fill=(0, 0, 0),
        )
        rotated_text_img = text_img.rotate(5, resample=Image.BICUBIC, expand=1)
        im.paste(rotated_text_img, (2, 328), rotated_text_img)
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "fraud.png")
        fp.close()
        return _file

    def gen_didyou(self, ctx, member_avatar, username):
        member_avatar = self.bytes_to_image(member_avatar, 500)

        # base canvas
        im = Image.new("RGBA", (1000, 750), None)
        gen_didyou = Image.open(
            f"{bundled_data_path(self)}/didyou/didyou.png", mode="r"
        ).convert("RGBA")

        im.paste(gen_didyou, (0, 0), gen_didyou)
        gen_didyou.close()
        member_avatar.close()
        text = ctx.guild.name
        font = ImageFont.truetype(f"{bundled_data_path(self)}/arial.ttf", 30)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(text, font, stroke_width=1)
        canvas.text(
            (670, 712),
            text,
            font=font,
            fill=(0, 0, 0),
            align="left",
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )

        fp = BytesIO()
        im.save(fp, "PNG")
        # test
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "didyou.png")
        fp.close()
        return _file

    def gen_sus(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 350)

        im = Image.new("RGBA", (589, 758), None)
        im.paste(member_avatar, (225, 40), member_avatar)
        body = Image.open(
            f"{bundled_data_path(self)}/sus/sus_mask.png", mode="r"
        ).convert("RGBA")
        faceplate = Image.open(
            f"{bundled_data_path(self)}/sus/sus_mask_2.png", mode="r"
        ).convert("RGBA")
        mask = (
            Image.open(f"{bundled_data_path(self)}/sus/sus_mask_6.png")
            .convert("L")
            .resize(body.size)
        )
        im2 = Image.composite(im, faceplate, mask)
        im.paste(im2)
        im.paste(body, (0, 0), body)
        im.paste(faceplate, (0, 0), faceplate)

        body.close()
        faceplate.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "sus.png")
        fp.close()
        return _file

    def gen_sugoi(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 500)

        im = Image.new("RGBA", (500, 500), None)
        im.paste(member_avatar, (0, 0), member_avatar)
        head = Image.open(
            f"{bundled_data_path(self)}/serval/head.png", mode="r"
        ).convert("RGBA")
        ribbon = Image.open(
            f"{bundled_data_path(self)}/serval/ribbon.png", mode="r"
        ).convert("RGBA")

        im.paste(head, (0, 0), head)
        im.paste(ribbon, (0, 0), ribbon)
        head.close()
        ribbon.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "sugoi.png")
        fp.close()
        return _file

    def gen_ash(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 500)

        im = Image.new("RGBA", (500, 500), None)
        im.paste(member_avatar, (0, 0), member_avatar)
        head = Image.open(f"{bundled_data_path(self)}/ash/ash.png", mode="r").convert(
            "RGBA"
        )
        im.paste(head, (50, 30), head)
        head.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ash.png")
        fp.close()
        return _file

    def gen_jack(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 300)

        im = Image.new("RGBA", (337, 746), None)
        im.paste(member_avatar, (30, 258), member_avatar)
        head = Image.open(f"{bundled_data_path(self)}/jack/jack.png", mode="r").convert(
            "RGBA"
        )
        im.paste(head, (0, 0), head)
        head.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "jack.png")
        fp.close()
        return _file

    def gen_bill(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 200)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (625, 352), None)
        billmask = Image.open(
            f"{bundled_data_path(self)}/bill/bill.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (277, 0), member_avatar)
        im.paste(billmask, (0, 0), billmask)
        billmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "bill.png")
        fp.close()
        return _file

    def gen_clownoffice(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 225)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (661, 645), None)
        clownmask = Image.open(
            f"{bundled_data_path(self)}/clown/clown_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (18, 190), member_avatar)
        im.paste(clownmask, (0, 0), clownmask)
        clownmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "mhr.png")
        fp.close()
        return _file

    def gen_bau(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 155)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (840, 554), None)
        bawmask = Image.open(
            f"{bundled_data_path(self)}/bau/bau_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (350, 210), member_avatar)
        im.paste(bawmask, (0, 0), bawmask)
        bawmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "bau.png")
        fp.close()
        return _file

    def gen_better(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 340)

        member_avatar = member_avatar.rotate(15, Image.NEAREST, expand=1)

        im = Image.new("RGBA", (465, 500), None)
        better_mask = Image.open(
            f"{bundled_data_path(self)}/better/better_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (30, 40), member_avatar)
        im.paste(better_mask, (0, 0), better_mask)

        better_mask.close()
        member_avatar.close()
        # make im transparent by making white areas transparent
        im = im.convert("RGBA")
        data = im.getdata()

        new_data = []
        for item in data:
            if item[:3] == (255, 255, 255):
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        im.putdata(new_data)

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "playbettergames.png")
        fp.close()
        return _file

    def gen_mygf(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 306)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (672, 568), None)
        mygfmask = Image.open(
            f"{bundled_data_path(self)}/mygf/mygf_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (39, 30), member_avatar)
        im.paste(mygfmask, (0, 0), mygfmask)
        mygfmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "mygf.png")
        fp.close()
        return _file

    def gen_compet(self, ctx, member_avatar):
        member_avatar1 = self.bytes_to_image(member_avatar, 60)
        member_avatar2 = self.bytes_to_image(member_avatar, 60)
        member_avatar3 = self.bytes_to_image(member_avatar, 580)

        im = Image.new("RGBA", (575, 722), None)
        mycompmask = Image.open(
            f"{bundled_data_path(self)}/competition/competition_mask.png", mode="r"
        ).convert("RGBA")

        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        im.paste(mycompmask, (0, 0), mycompmask)
        mycompmask.close()

        im.paste(member_avatar1, (342, 38), member_avatar1)
        member_avatar.close()

        im.paste(member_avatar2, (480, 84), member_avatar2)
        member_avatar2.close()

        im.paste(member_avatar3, (0, 160), member_avatar3)
        member_avatar3.close()
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "whenyoure.png")
        fp.close()
        return _file

    def gen_chupalla(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 501)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (501, 501), None)
        chupallamask = Image.open(
            f"{bundled_data_path(self)}/chupalla/chupalla_mask.png", mode="r"
        ).convert("RGBA")
        banderamask = Image.open(
            f"{bundled_data_path(self)}/chupalla/fondo_mask.png", mode="r"
        ).convert("RGBA")
        wine = Image.open(
            f"{bundled_data_path(self)}/chupalla/wine.png", mode="r"
        ).convert("RGBA")
        empanada = Image.open(
            f"{bundled_data_path(self)}/chupalla/empanada.png", mode="r"
        ).convert("RGBA")
        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(chupallamask, (100, 25), chupallamask)
        im.paste(banderamask, (130, 400), banderamask)
        im.paste(wine, (0, 250), wine)
        im.paste(empanada, (300, 250), empanada)
        empanada.close()
        chupallamask.close()
        banderamask.close()
        wine.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "chupalla.png")
        fp.close()
        return _file

    def gen_ameto(self, ctx, member_avatar, username):
        member_avatar = self.bytes_to_image(member_avatar, 600)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (915, 907), None)
        ametomask = Image.open(
            f"{bundled_data_path(self)}/ameto/ameto_mask.png", mode="r"
        ).convert("RGBA")
        im.paste(member_avatar, (150, 0), member_avatar)
        im.paste(ametomask, (0, 0), ametomask)
        ametomask.close()
        member_avatar.close()
        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        text = username
        font = ImageFont.truetype(
            f"{bundled_data_path(self)}/Magistral-Cond-W08-Bold.ttf", 60
        )
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(text, font, stroke_width=1)
        canvas.text(
            (330, 653),
            text,
            font=font,
            fill=(255, 255, 255),
            align="left",
            stroke_width=3,
            stroke_fill=(255, 29, 80),
        )

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ameto.png")
        fp.close()
        return _file

    def gen_reliable(self, ctx, member_avatar, username):
        member_avatar = self.bytes_to_image(member_avatar, 50)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (384, 578), None)
        reliablemask = Image.open(
            f"{bundled_data_path(self)}/reliable/reliable_mask.png", mode="r"
        ).convert("RGBA")
        # member_avatar.rotate(-25, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        im.paste(reliablemask, (0, 0), reliablemask)
        im.paste(member_avatar, (180, 395), member_avatar)
        reliablemask.close()
        member_avatar.close()
        # member_avatar.rotate(90, resample=0, expand=0, center=None, translate=None, fillcolor=None)
        # im.rotate(120, resample=0, expand=0, center=None, translate=None, fillcolor=None)

        # TEST START
        # Load font
        font_path = f"{bundled_data_path(self)}/krab.ttf"
        font_size = 50
        font = ImageFont.truetype(font_path, font_size)

        # Create a new image for the rotated text
        text_width, text_height = font.getsize(username)
        rotated_text_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(rotated_text_img)
        username = username[:6] if len(username) > 6 else username
        # Draw the text on the rotated text image
        draw.text(
            (0, 0), username, font=font, fill=(0, 0, 0), align="left", stroke_width=0
        )

        # Rotate the text image by 20 degrees
        rotated_text_img = rotated_text_img.rotate(-24, expand=True)

        # Paste the rotated text onto the original image
        im.paste(rotated_text_img, (105, 415), rotated_text_img)

        # TEST END
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "ameto.png")
        fp.close()
        return _file

    def gen_discord(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 453)

        im = Image.new("RGBA", (1548, 1040), None)
        discordmask = Image.open(
            f"{bundled_data_path(self)}/discord/discord_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(discordmask, (0, 0), discordmask)
        im.paste(member_avatar, (523, 235), member_avatar)
        discordmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "discord.png")
        fp.close()
        return _file

    def gen_kowone(self, ctx, member_avatar, username):
        member_avatar = self.bytes_to_image(member_avatar, 260)

        im = Image.new("RGBA", (244, 260), None)
        kowonemask = Image.open(
            f"{bundled_data_path(self)}/kowone/korone_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (0, 0), member_avatar)
        im.paste(kowonemask, (0, 0), kowonemask)
        kowonemask.close()
        member_avatar.close()
        # text
        text = username
        text = text.lower()
        font = ImageFont.truetype(f"{bundled_data_path(self)}/Calibri.ttf", 25)
        canvas = ImageDraw.Draw(im)
        text_width, text_height = canvas.textsize(text, font, stroke_width=1)
        canvas.text(
            ((im.width - text_width) / 2, 223),
            text,
            font=font,
            fill=(0, 0, 0),
            align="center",
            stroke_width=0,
            stroke_fill=(0, 0, 0),
        )
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "discord.png")
        fp.close()
        return _file

    def gen_taiko(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 480)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (960, 540), None)
        r = random.randint(1, 3)
        taiko_mask = Image.open(
            f"{bundled_data_path(self)}/taiko/taiko_mask_{r}.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (240, 90), member_avatar)
        im.paste(taiko_mask, (0, 0), taiko_mask)
        taiko_mask.close()
        member_avatar.close()
        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "taiko.png")
        fp.close()
        return _file

    def gen_pretend(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 350)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (744, 609), None)
        pretendmask = Image.open(
            f"{bundled_data_path(self)}/pretend/pretend_mask.png", mode="r"
        ).convert("RGBA")
        blushmask = Image.open(
            f"{bundled_data_path(self)}/pretend/blush_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (90, 80), member_avatar)

        im.paste(blushmask, (126, 228), blushmask)
        im.paste(pretendmask, (0, 0), pretendmask)

        pretendmask.close()
        blushmask.close()
        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "pretend.png")
        fp.close()
        return _file

    def gen_evidence(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 724)

        # member_avatar = member_avatar.rotate(330, Image.NEAREST, expand=1)
        # base canvas
        im = Image.new("RGBA", (1436, 808), None)
        evi_mask = Image.open(
            f"{bundled_data_path(self)}/evidence/evidence_mask.png", mode="r"
        ).convert("RGBA")

        im.paste(member_avatar, (350, 60), member_avatar)

        im.paste(evi_mask, (0, 0), evi_mask)

        evi_mask.close()

        member_avatar.close()

        fp = BytesIO()
        im.save(fp, "PNG")
        fp.seek(0)
        im.close()
        _file = discord.File(fp, "pretend.png")
        fp.close()
        return _file
