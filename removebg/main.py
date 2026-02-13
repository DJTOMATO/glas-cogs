import asyncio
import logging
import os
import platform
from io import BytesIO
from typing import Optional

import discord
from discord import app_commands
from redbot.core import Config, commands
from redbot.core.bot import Red

log = logging.getLogger("glas.rembg")

FULL_MODELS = [
    "u2net",
    "u2netp",
    "u2net_human_seg",
    "u2net_cloth_seg",
    "silueta",
    "isnet-general-use",
    "isnet-anime",
    "sam",
    "birefnet-general",
    "birefnet-general-lite",
    "birefnet-portrait",
    "birefnet-dis",
    "birefnet-hrsod",
    "birefnet-cod",
    "birefnet-massive",
    "bria-rmbg",
]

PI_SAFE_MODELS = [
    "u2net",
    "u2netp",
    "u2net_human_seg",
    "u2net_cloth_seg",
    "silueta",
    "isnet-general-use",
    "isnet-anime",
]

IS_ARM = platform.machine().lower() in ("armv7l", "aarch64")
AVAILABLE_MODELS = PI_SAFE_MODELS if IS_ARM else FULL_MODELS


class BgRemover(commands.Cog):
    __author__ = "Glas"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config = Config.get_conf(self, 117, force_registration=True)
        self._semaphore = asyncio.Semaphore(1)
        self._sessions = {}
        os.environ["NUMBA_NUM_THREADS"] = "1"
        os.environ["NUMBA_THREADING_LAYER"] = "workqueue"

    def format_help_for_context(self, ctx: commands.Context):
        helpcmd = super().format_help_for_context(ctx)
        models = ", ".join(AVAILABLE_MODELS)
        return f"{helpcmd}\n\nAvailable models:\n{models}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int):
        return

    async def red_get_data_for_user(self, *, requester: str, user_id: int):
        return

    def _get_session(self, model: str):
        from rembg import new_session

        if model not in self._sessions:
            self._sessions[model] = new_session(model)
        return self._sessions[model]

    def _process(self, image_bytes: bytes, model: str) -> BytesIO:
        from rembg import remove
        from PIL import Image

        session = self._get_session(model)
        image = Image.open(BytesIO(image_bytes)).convert("RGBA")

        if max(image.size) > 1024:
            image.thumbnail((1024, 1024))

        output = remove(image, session=session, alpha_matting=False)

        buffer = BytesIO()
        output.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    async def _run(self, send_func, image_bytes: bytes, model: str, typing_ctx=None):
        if self._semaphore.locked():
            return await send_func("⏳ Another image is currently processing.")

        async with self._semaphore:
            if typing_ctx:
                async with typing_ctx.typing():
                    await self._execute(send_func, image_bytes, model)
            else:
                await self._execute(send_func, image_bytes, model)

    async def _execute(self, send_func, image_bytes: bytes, model: str):
        loop = asyncio.get_running_loop()
        try:
            buffer = await asyncio.wait_for(
                loop.run_in_executor(None, self._process, image_bytes, model),
                timeout=60,
            )
        except asyncio.TimeoutError:
            return await send_func("⏱ Processing timed out.")
        except Exception:
            log.exception("rembg failed")
            return await send_func("❌ Background removal failed.")

        await send_func(file=discord.File(buffer, filename="no_bg.png"))

    @commands.command(name="bgremove", aliases=["nobg", "nobackground"])
    async def bgremove(
        self,
        ctx: commands.Context,
        model: Optional[str] = "u2netp",
        user: Optional[discord.Member] = None,
        url: Optional[str] = None,
    ):
        model = model or "u2netp"

        if model not in AVAILABLE_MODELS:
            return await ctx.send("❌ Invalid or unsupported model on this system.")

        image_bytes = None

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.size > 8 * 1024 * 1024:
                return await ctx.send("❌ File too large (max 8MB).")
            image_bytes = await attachment.read()

        elif user:
            avatar = user.display_avatar.replace(format="png", size=1024)
            image_bytes = await avatar.read()

        elif url:
            try:
                async with self.bot.session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Failed to fetch image.")
                    image_bytes = await resp.read()
            except Exception:
                return await ctx.send("❌ Invalid image URL.")

        else:
            return await ctx.send("❌ Provide attachment, user, or URL.")

        await self._run(ctx.send, image_bytes, model, typing_ctx=ctx)

    @app_commands.command(
        name="bgremove", description="Remove background from an image"
    )
    @app_commands.describe(
        attachment="Image attachment",
        user="User avatar",
        url="Direct image URL",
        model="Model to use",
    )
    @app_commands.choices(
        model=[app_commands.Choice(name=m, value=m) for m in AVAILABLE_MODELS]
    )
    async def bgremove_slash(
        self,
        interaction: discord.Interaction,
        attachment: Optional[discord.Attachment] = None,
        user: Optional[discord.Member] = None,
        url: Optional[str] = None,
        model: app_commands.Choice[str] = None,
    ):
        await interaction.response.defer()

        selected_model = model.value if model else "u2netp"

        if selected_model not in AVAILABLE_MODELS:
            return await interaction.followup.send(
                "❌ Unsupported model on this system."
            )

        image_bytes = None

        if attachment:
            if attachment.size > 8 * 1024 * 1024:
                return await interaction.followup.send("❌ File too large (max 8MB).")
            image_bytes = await attachment.read()

        elif user:
            avatar = user.display_avatar.replace(format="png", size=1024)
            image_bytes = await avatar.read()

        elif url:
            try:
                async with self.bot.session.get(url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(
                            "❌ Failed to fetch image."
                        )
                    image_bytes = await resp.read()
            except Exception:
                return await interaction.followup.send("❌ Invalid image URL.")

        else:
            return await interaction.followup.send(
                "❌ Provide attachment, user, or URL."
            )

        await self._run(interaction.followup.send, image_bytes, selected_model)
