import discord
from discord.ext import tasks
import os
import shutil
from redbot.core import Config, commands
from discord.ext.commands import has_permissions
import time
import asyncio

class Listener(commands.Cog):
    """Artemis Image Poster Service"""
    def __init__(self, bot):
        self.bot = bot
        self.watch_folder = '/mnt/hdd/data/artemis/images/'
        self.config = Config.get_conf(self, identifier="Artemis")
        self.config.register_global(channel_id=None)
        self.config.register_user(linked_users_data={})
        self.linked_users = {}
        self.posted_images = set()
        self.last_post_time = 0
        self.rate_limit = 120  # Increased to 120 seconds (2 minutes) between posts

        # Load linked_users_data when the cog is loaded
        self.bot.loop.create_task(self.load_linked_users_data())

        # Schedule the image_check and process_images tasks


    def cog_unload(self):
        self.image_check.cancel()

    def load_linked_users_data(self):
        # Access the linked_users_data from the configuration
        self.linked_users = self.config.linked_users_data


    async def load_linked_users_data(self):
        # Access the linked_users_data from the configuration
        self.linked_users = self.config.linked_users_data

    async def load_linked_users_on_ready(self):
        # Load linked users when the bot is ready
        await self.bot.wait_until_red_ready()
        linked_users = self.linked_users
        if linked_users is None:
            linked_users = {}
        self.linked_users = linked_users

    async def cog_load(self):
        # Load linked users when the bot is ready
        asyncio.create_task(self.wait_for_bot_ready())


    async def wait_for_bot_ready(self):
        await self.bot.wait_until_red_ready()
        linked_users = self.linked_users
        if linked_users is None:
            linked_users = {}
        self.linked_users = linked_users

    @commands.Cog.listener()
    async def on_ready(self):
        # Start the tasks when the bot is ready
        if not self.image_check.is_running():
            self.image_check.start()

    @commands.command()
    @commands.mod()
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """[Mod] Set's Channel for Artemis Image Posting"""
        await self.config.channel_id.set(channel.id)
        await ctx.send(f"Image channel set to {channel.mention}")

    @commands.command()
    async def link(self, ctx, user_id: int):
        """Connects your AIME with Discord ID"""
        try:
            linked_users_data = await self.config.linked_users_data() #shouln't be load_linked_users_data?
            if linked_users_data is None:
                linked_users_data = {}  # Initialize as an empty dictionary

            # Check if the user is already linked
            if ctx.author.id in linked_users_data:
                await ctx.send(f"You are user {linked_users_data[ctx.author.id]} already, you cannot register again.")
            else:
                linked_users_data[ctx.author.id] = user_id
                await self.config.linked_users_data.set(linked_users_data)
            
                # Debugging: Print the updated linked users data
                #await ctx.send(f"Debug: Linked users data after linking: {linked_users_data}")

                await ctx.send(f"You are now linked as user {user_id}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command()
    async def my_data(self, ctx):
        """Returns Linked Data"""
        user_id = ctx.author.id

        # Get the linked users data
        linked_users_data = await self.config.linked_users_data()

        # Debugging: Print the linked_users_data
        print(f"Debug: Linked Users Data: {linked_users_data}")

        if str(user_id) in linked_users_data:
            linked_user_id = linked_users_data[str(user_id)]  # Retrieve the linked user ID as a string
            await ctx.send(f"You are linked to user ID: {linked_user_id}")
        else:
            await ctx.send("You are not linked to another user.")

    @commands.command()
    @commands.mod()
    async def force(self, ctx):
        """[Debug] Post new images if any"""
        channel_id = await self.config.channel_id()
        if channel_id is None:
            await ctx.send("Please set the image channel first using the set_channel command.")
        else:
            await ctx.send("Forcing image check...")
            await self.image_check()

    @tasks.loop(seconds=30)
    async def image_check(self):
        channel_id = await self.config.channel_id()
        if channel_id is None:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return

        current_time = time.time()

        for filename in os.listdir(self.watch_folder):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                file_path = os.path.join(self.watch_folder, filename)
                if filename not in self.posted_images and current_time - self.last_post_time >= self.rate_limit:
                    await self.post_image(channel, file_path, filename)
                    self.last_post_time = current_time
                    self.posted_images.add(filename)  # Add the filename to the set to avoid reposting

    async def post_image(self, channel, file_path, filename):
        linked_users_data = await self.config.linked_users_data()

        if filename in self.posted_images:
            return


        parts = filename.split("_")
        if len(parts) < 1:
            return

        user_id_str = parts[0]
        user_id = int(user_id_str)

        user_mention = None

        for discord_id, user_id_num in linked_users_data.items():
            if user_id_num == user_id:
                user_mention = f"<@{discord_id}>"
                break

        if user_mention is None:
            user_mention = f"Unlinked! Link it with ``!link {user_id_str}``"

        await channel.send(f"Score by {user_mention}:", allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

        with open(file_path, 'rb') as image_file:
            _file = discord.File(image_file, filename=filename)

        await channel.send(file=_file)

        # Move the posted image to the oldimages folder
        old_images_folder = '/mnt/hdd/data/artemis/oldimages/'
        new_path = os.path.join(old_images_folder, filename)

        try:
            shutil.move(file_path, new_path)
        except Exception as e:
            await channel.send(f"Failed to move the image to oldimages folder: {e}")




    @commands.command()
    @commands.mod()
    async def clean_linked_users(self, ctx):
        """[Mod] Clean Linked Users"""
        try:
            linked_users_data = await self.config.linked_users_data()
            
            if linked_users_data:
                linked_users_data.clear()  # Clear the linked users data
                
                # Save the updated configuration to remove all linked users
                await self.config.linked_users_data.set(linked_users_data)
                
                await ctx.send("All linked users have been removed from the database.")
            else:
                await ctx.send("No linked users found in the database.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")





    @commands.command()
    @commands.mod()
    async def clean_posted_images(self, ctx):
        """[Mod] Clean posted images"""
        self.posted_images.clear()
        await ctx.send("Cleaned the posted images set.")


