import discord
from redbot.core import commands, Config
import re

class NoArgs(commands.Cog):
    """
    This cog will remove useless cdn expiration args from any url in whitelisted channels.
    Useful for meme channels and others
    Made with GPT, so use at your own risk lol
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild_settings = {"whitelisted_channels": []}
        self.config.register_guild(**default_guild_settings)

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if not isinstance(message.channel, discord.TextChannel):
            return

        if message.author.bot:
            return

        urls = re.findall(r'(https?://\S+)', message.content)
        for url in urls:
            if ".webm" in url:
                try:
                    clean_url = url.split(".webm")[0] + ".webm"

                    channel = self.bot.get_channel(message.channel.id)
                    if await self.is_channel_whitelisted(channel):
                        original_author = message.author.mention
                        await channel.send(f"{original_author} posted a webm file. Here's the cleaned webm file without extra arguments:\n{clean_url}")
                        await message.delete()
                except Exception as e:
                    await channel.send(f"Failed to repost the attachment: {e}")

    @commands.group()

    async def nwhitelist(self, ctx):
        """Manage whitelisted channels for webm reposting."""
        pass

    @nwhitelist.command(name="add")
    async def whitelist_add(self, ctx, channel: discord.TextChannel):
        """Add a channel to the whitelist."""
        async with self.config.guild(ctx.guild).whitelisted_channels() as whitelisted_channels:
            if channel.id not in whitelisted_channels:
                whitelisted_channels.append(channel.id)
                await ctx.send(f"{channel.mention} has been added to the whitelist.")
            else:
                await ctx.send(f"{channel.mention} is already in the whitelist.")

    @nwhitelist.command(name="remove")
    async def whitelist_remove(self, ctx, channel: discord.TextChannel):
        """Remove a channel from the whitelist."""
        async with self.config.guild(ctx.guild).whitelisted_channels() as whitelisted_channels:
            if channel.id in whitelisted_channels:
                whitelisted_channels.remove(channel.id)
                await ctx.send(f"{channel.mention} has been removed from the whitelist.")
            else:
                await ctx.send(f"{channel.mention} is not in the whitelist.")

    @nwhitelist.command(name="show")
    async def whitelist_show(self, ctx):
        """Show the current whitelist."""
        whitelisted_channels = await self.config.guild(ctx.guild).whitelisted_channels()
        if whitelisted_channels:
            channel_mentions = [self.bot.get_channel(channel_id).mention for channel_id in whitelisted_channels]
            await ctx.send(f"The current whitelisted channels are: {' '.join(channel_mentions)}")
        else:
            await ctx.send("There are no whitelisted channels.")

    async def is_channel_whitelisted(self, channel):
        whitelisted_channels = await self.config.guild(channel.guild).whitelisted_channels()
        return channel.id in whitelisted_channels

def setup(bot):
    bot.add_cog(NoArgs(bot))