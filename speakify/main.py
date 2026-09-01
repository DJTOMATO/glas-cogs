import asyncio
import io
import logging
import math
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from PIL import Image
from redbot.core import commands
from redbot.core.bot import Red

log = logging.getLogger("red.speakify")

QUALITY_PRESETS = {
    "low": {"size": 64, "frames": 50, "delay": 6},
    "mid": {"size": 128, "frames": 100, "delay": 5},
    "high": {"size": 256, "frames": 150, "delay": 4},
}


class Speakify(commands.Cog):
    """Transform avatars and image attachments into a Speakify animated GIF."""

    __author__ = "Glas"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        super().__init__()
        self.bot: Red = bot

    def format_help_for_context(self, ctx: commands.Context):
        helpcmd = super().format_help_for_context(ctx)
        txt = f"Version: {self.__version__}\nAuthor: {self.__author__}"
        return f"{helpcmd}\n\n{txt}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int):
        return

    async def red_get_data_for_user(self, *, requester: str, user_id: int):
        return

    async def cog_load(self) -> None:
        asyncio.create_task(self.initialize())

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()

    @commands.hybrid_command(aliases=["cuayo"])
    @commands.max_concurrency(1, commands.BucketType.default)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def speakify(
        self,
        ctx: commands.Context,
        target: Optional[discord.User] = None,
        quality: str = "mid",
    ):
        """Create a Speakify GIF from a user avatar or image attachment."""
        quality = quality.lower()
        if quality not in QUALITY_PRESETS:
            return await ctx.send("Quality must be one of: low, mid, high.")

        attachment = self._find_attachment(ctx)
        source_name = None
        if attachment is not None:
            source_bytes = await self._download_attachment(attachment)
            source_name = Path(attachment.filename or "attachment").stem
        else:
            if target is None:
                target = ctx.author
            source_bytes = await self._download_avatar(target)
            source_name = f"{target.name}_avatar"

        if source_bytes is None:
            return await ctx.send(
                "Could not download an image. Attach a valid image or mention a user."
            )

        async with ctx.typing():
            try:
                gif_bytes = await self.bot.loop.run_in_executor(
                    None, self._build_gif, source_bytes, quality
                )
            except Exception:
                log.exception("Speakify generation failed.")
                return await ctx.send(
                    "Something went wrong while creating the Speakify GIF. Try again later."
                )

        filename = f"{source_name}_speakify.gif"
        await ctx.send(file=discord.File(io.BytesIO(gif_bytes), filename=filename))

    def _find_attachment(self, ctx: commands.Context) -> Optional[discord.Attachment]:
        message = ctx.message
        for attachment in message.attachments:
            if self._is_image_attachment(attachment):
                return attachment

        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            for attachment in getattr(ref, "attachments", []):
                if self._is_image_attachment(attachment):
                    return attachment

        return None

    def _is_image_attachment(self, attachment: discord.Attachment) -> bool:
        if attachment.content_type:
            return attachment.content_type.startswith("image")
        return attachment.filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
        )

    async def _download_attachment(self, attachment: discord.Attachment) -> Optional[bytes]:
        if attachment.size and attachment.size > 8_000_000:
            return None
        try:
            return await attachment.read()
        except Exception:
            return None

    async def _download_avatar(self, user: discord.User) -> Optional[bytes]:
        avatar = getattr(user, "display_avatar", None) or getattr(user, "avatar", None)
        if avatar is None:
            return None
        if hasattr(avatar, "replace"):
            url = str(avatar.replace(format="png", size=512).url)
        else:
            url = str(avatar.url)
        return await self._download_url(url)

    async def _download_url(self, url: str) -> Optional[bytes]:
        session = getattr(self.bot, "session", None)
        if session is None and hasattr(self.bot, "http"):
            session = getattr(self.bot.http, "session", None)

        if session is None:
            async with aiohttp.ClientSession() as session:
                return await self._fetch_bytes(session, url)
        return await self._fetch_bytes(session, url)

    async def _fetch_bytes(self, session: aiohttp.ClientSession, url: str) -> Optional[bytes]:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                return await response.read()
        except Exception:
            return None

    def _build_gif(self, source_bytes: bytes, quality_key: str) -> bytes:
        source = Image.open(io.BytesIO(source_bytes)).convert("RGB")
        target = Image.open(self._asset_path()).convert("RGB")
        preset = QUALITY_PRESETS[quality_key]
        size = preset["size"]
        frames_count = preset["frames"]
        delay = preset["delay"]

        source_img = self._prepare_image(source, size)
        target_img = self._prepare_image(target, size)
        assignments = self._match_pixels(source_img, target_img)
        source_pixels = list(source_img.getdata())
        width, height = source_img.size

        frames = []
        for frame_idx in range(frames_count):
            t = frame_idx / (frames_count - 1) if frames_count > 1 else 1.0
            t = self._ease(t)
            frame_bytes = self._interpolated_frame(source_pixels, assignments, width, t)
            frames.append(Image.frombytes("RGB", (width, height), bytes(frame_bytes)))

        output = io.BytesIO()
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=delay * 10,
            loop=0,
            disposal=2,
        )
        return output.getvalue()

    def _asset_path(self) -> Path:
        return Path(__file__).parent / "speakify.png"

    def _prepare_image(self, img: Image.Image, size: int) -> Image.Image:
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        cropped = img.crop((left, top, left + min_dim, top + min_dim))
        return cropped.resize((size, size), Image.LANCZOS)

    def _match_pixels(self, source: Image.Image, target: Image.Image) -> list[int]:
        source_pixels = list(source.getdata())
        target_pixels = list(target.getdata())
        width = source.width

        src_sorted = sorted(
            range(len(source_pixels)),
            key=lambda index: self._pixel_sort_key(source_pixels[index], index, width),
        )
        tgt_sorted = sorted(
            range(len(target_pixels)),
            key=lambda index: self._pixel_sort_key(target_pixels[index], index, width),
        )

        assignments = [0] * len(source_pixels)
        for target_index, source_index in enumerate(src_sorted):
            assignments[tgt_sorted[target_index]] = source_index
        return assignments

    def _pixel_sort_key(self, pixel: tuple[int, int, int], index: int, width: int):
        r, g, b = pixel
        lum = r + g + b
        return (lum, r, g, b, index // width, index % width)

    def _ease(self, t: float) -> float:
        if t < 0.5:
            return 4.0 * t * t * t
        return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0

    def _interpolated_frame(
        self,
        source_pixels: list[tuple[int, int, int]],
        assignments: list[int],
        width: int,
        t: float,
    ) -> bytearray:
        size = width * width
        acc_r = [0.0] * size
        acc_g = [0.0] * size
        acc_b = [0.0] * size
        acc_w = [0.0] * size

        for target_index, source_index in enumerate(assignments):
            sx = source_index % width
            sy = source_index // width
            tx = target_index % width
            ty = target_index // width
            fx = sx * (1.0 - t) + tx * t
            fy = sy * (1.0 - t) + ty * t
            r, g, b = source_pixels[source_index]
            x0 = int(math.floor(fx))
            y0 = int(math.floor(fy))
            dx = fx - x0
            dy = fy - y0

            for oy in (0, 1):
                for ox in (0, 1):
                    weight = (1.0 - dx if ox == 0 else dx) * (1.0 - dy if oy == 0 else dy)
                    nx = x0 + ox
                    ny = y0 + oy
                    if 0 <= nx < width and 0 <= ny < width:
                        index = ny * width + nx
                        acc_r[index] += r * weight
                        acc_g[index] += g * weight
                        acc_b[index] += b * weight
                        acc_w[index] += weight

        frame = bytearray(size * 3)
        for pixel_index in range(size):
            w = acc_w[pixel_index]
            if w > 0:
                frame[3 * pixel_index] = int(round(acc_r[pixel_index] / w))
                frame[3 * pixel_index + 1] = int(round(acc_g[pixel_index] / w))
                frame[3 * pixel_index + 2] = int(round(acc_b[pixel_index] / w))
            else:
                frame[3 * pixel_index : 3 * pixel_index + 3] = b"\x00\x00\x00"
        return frame
