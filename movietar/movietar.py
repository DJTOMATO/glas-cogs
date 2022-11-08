import discord
import random
from datetime import datetime
from redbot.core import commands
import moviepy
import moviepy.editor as mpe


class Movietar(commands.Cog):
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

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        return

    @commands.bot_has_permissions(attach_files=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=["movie"], cooldown_after_parsing=True)
    async def movietar(self, ctx, *, member: FuzzyMember = None):
        """Makes a video with your avatar.."""
        if not member:
            member = ctx.author

        async with ctx.typing():
            avatar = await self.get_avatar(member)
            task = functools.partial(self.gen_vid, ctx, avatar)
            image = await self.generate_image(ctx, task)
        if isinstance(image, str):
            await ctx.send(image)
        else:
            await ctx.send(file=image)

    async def get_avatar(self, member: discord.User):
        avatar = BytesIO()
        await member.avatar_url_as(static_format="png").save(avatar, seek_begin=True)
        return avatar

    @staticmethod
    def bytes_to_image(image: BytesIO, size: int):
        image = Image.open(image).convert("RGBA")
        image = image.resize((size, size), Image.ANTIALIAS)
        return image

    def gen_vid(self, ctx, member_avatar):
        member_avatar = self.bytes_to_image(member_avatar, 156)

        clip = VideoFileClip("clip.mp4")
        masked_clip = clip.fx(mpe.vfx.mask_color, color=[0, 1, 0], s=3)
        final_clip = mpe.CompositeVideoClip([some_background, masked_clip]).set_duration(
            clip.duration
        )
        final_clip.write_videofile("test.mp4")

        video = mp.VideoFileClip("test.mp4")
        image = avatar

        final = mp.CompositeVideoClip([image, video.set_position("center")])
        # final.write_videofile("final.mp4")

        return final
