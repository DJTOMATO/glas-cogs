import discord
from discord.ext import tasks
from redbot.core import Config, commands
import os
import shutil
import time
import asyncio
import aiomysql
import logging
from .functions import ListenerFunctions
import pymysql.err


class Artemis(commands.Cog):
    """Artemis Image Poster Service"""

    DEFAULT_DB_CONFIG = {
        "host": "",
        "user": "",
        "port": 0,
        "password": "",
        "db": "",
    }
    DEFAULT_FOLDERS = {
        "watch_folder": "",
        "old_images_folder": "",
    }

    def __init__(self, bot):
        self.bot = bot
        self.linked_users = []  # A list to store (discord_id, user, access_code) tuples
        self.log = logging.getLogger("glas.glas-cogs.artemis")
        self.config = Config.get_conf(self, identifier="Artemis")
        self.config.register_global(linked_users=[])
        self.config.register_global(channel_id=None)
        self.config.register_global(watch_folder=self.DEFAULT_FOLDERS["watch_folder"])
        self.config.register_global(
            old_images_folder=self.DEFAULT_FOLDERS["old_images_folder"]
        )
        self.config.register_global(db_config=self.DEFAULT_DB_CONFIG)
        self.watch_folder = self.config.watch_folder
        self.old_images_folder = self.config.old_images_folder

        self.posted_images = set()
        self.last_post_time = 0
        self.rate_limit = 120
        self.image_post_task.start()
        self.listener_functions = ListenerFunctions(
            self.config, self.linked_users
        )  # Pass linked_users to ListenerFunctions

    async def initialize(self):
        linked_users_data = await self.config.linked_users()
        self.linked_users = linked_users_data or []

        db_config_data = await self.config.db_config.all()
        self.db_config = db_config_data or self.DEFAULT_DB_CONFIG.copy()

        watch_folder_data = await self.config.watch_folder()
        self.watch_folder = watch_folder_data or self.DEFAULT_FOLDERS["watch_folder"]

        old_images_folder_data = await self.config.old_images_folder()
        self.old_images_folder = (
            old_images_folder_data or self.DEFAULT_FOLDERS["old_images_folder"]
        )

        channel_id = await self.config.channel_id()
        self.channel_id = channel_id

        self.log.warning(f"Loaded set_channel: {self.channel_id}")
        self.log.warning(f"Loaded linked users: {self.linked_users}")
        self.log.warning(f"Loaded db_config: {self.db_config}")
        self.log.warning(f"Loaded watch_folder: {self.watch_folder}")
        self.log.warning(f"Loaded old_images_folder: {self.old_images_folder}")

        if not self.image_post_task.is_running():
            self.image_post_task.start()

    @commands.command()
    async def link(self, ctx, access_code: str):
        """Connects your AIME with Discord ID"""
        discord_id = ctx.author.id

        try:
            user = await self.listener_functions.get_user_from_access_code(
                self.db_config, access_code
            )
        except pymysql.err.OperationalError as e:
            # Handle the specific error for MySQL connection issues
            await ctx.send(f"Error connecting to the database: {e}")
            return
        except Exception as e:
            # Handle other exceptions if needed
            await ctx.send(f"An error occurred: {e}")
            return

        if user is not None:
            linked_users = await self.config.linked_users()
            linked_users.append((discord_id, user, access_code))
            await self.config.linked_users.set(linked_users)  # Save the updated list
            await ctx.message.delete()  # Delete the user's message

            # Extract the last 4 digits of the access_code
            last_4_digits = access_code[-4:]

            # Send a message displaying only the last 4 digits of the access_code
            await ctx.send(
                f"You are now linked as user {user} with access code ending in {last_4_digits}"
            )
        else:
            await ctx.send("Invalid access code. Please check and try again.")

    @tasks.loop(seconds=30)
    async def image_post_task(self, ctx):
        print("Checking for images...")
        channel_id = await self.config.channel_id()
        if channel_id is None:
            return

        current_time = time.time()

        self.linked_users_data = await self.config.linked_users()

        for filename in os.listdir(self.watch_folder):
            if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
                self.file_path = os.path.join(self.watch_folder, filename)
                if (
                    filename not in self.posted_images
                    and current_time - self.last_post_time >= self.rate_limit
                ):
                    channel_id = await self.config.channel_id()
                    await self.listener_functions.process_image(
                        self, ctx, channel_id, filename
                    )
                    self.last_post_time = current_time
                    self.posted_images.add(filename)

    @image_post_task.before_loop
    async def before_image_post_task(self):
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.mod()
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """[Mod] Set's Channel for Artemis Image Posting"""
        await self.config.channel_id.set(channel.id)
        await ctx.send(f"Image channel set to {channel.mention}")

    @commands.mod()
    @commands.command()
    async def check_linked_users(self, ctx):
        """[Mod] Check the contents of linked_users"""
        linked_users = await self.config.linked_users()
        if not linked_users:
            await ctx.send("No users are currently linked.")
        else:
            user_info = "\n".join(
                f"Discord ID: {discord_id}, User: {user}, Access Code: {access_code}"
                for discord_id, user, access_code in linked_users
            )
            await ctx.send(f"Linked Users:\n{user_info}")

    @commands.command()
    @commands.is_owner()  # You can restrict this command to the owner if needed
    async def delete_linked_users(self, ctx):
        """[Mod] Delete the contents of linked_users"""
        await self.config.linked_users.set([])  # Clear and save an empty list
        await ctx.send("Linked users have been deleted.")

    @commands.command()
    @commands.is_owner()  # Only allow the bot owner to set the database config
    async def set_db_config(self, ctx, host, user, port, password, db):
        """Set the database configuration."""

        db_config = {
            "host": host,
            "user": user,
            "port": int(port),
            "password": password,
            "db": db,
        }
        await self.config.db_config.set(db_config)
        await ctx.send(self.db_config)
        await ctx.send("Database configuration set successfully.")

    @commands.command()
    @commands.is_owner()  # Only allow the bot owner to clear the database config
    async def clear_db_config(self, ctx):
        """Clear the database configuration."""
        self.db_config = self.DEFAULT_DB_CONFIG.copy()
        await ctx.send("Database configuration cleared successfully.")

    @commands.command()
    @commands.is_owner()  # Only allow the bot owner to set the folders
    async def set_folders(self, ctx, watch_folder=None, old_images_folder=None):
        """Set the watch and old images folders."""
        await self.config.watch_folder.set(watch_folder)
        await self.config.old_images_folder.set(old_images_folder)
        await ctx.send("Folders set successfully.")

    @commands.command()
    @commands.is_owner()  # Only allow the bot owner to reset the folders to default
    async def reset_folders(self, ctx):
        """Reset the folders to default values."""
        self.watch_folder = self.DEFAULT_FOLDERS["watch_folder"]
        self.old_images_folder = self.DEFAULT_FOLDERS["old_images_folder"]

        await ctx.send("Folders reset to default values.")

    @commands.is_owner()
    @commands.command()
    async def get_config(self, ctx):
        """Get current configuration values via DM."""
        user = ctx.author

        # Load the current configuration values
        watch_folder = await self.config.watch_folder()
        old_images_folder = await self.config.old_images_folder()
        linked_users = await self.config.linked_users()
        db_config = await self.config.db_config()
        post_channel = await self.config.channel_id()
        # Prepare the message with the current configuration values
        message = (
            "Current Configuration:\n"
            f"Watch Folder: {watch_folder}\n"
            f"Post Channel: {post_channel}\n"
            f"Linked Users: {linked_users}\n"
            f"Database Config: {db_config}\n"
            f"Old Images Folder: {old_images_folder}"
        )

        try:
            # Send the message via DM
            await user.send(message)
            await ctx.send("Check your DMs for the current configuration.")
        except Exception as e:
            await ctx.send(f"Error sending DM: {e}")

    @commands.command()
    @commands.mod()
    async def force(self, ctx):
        """[Debug] Post new images if any"""
        channel_id = await self.config.channel_id()
        if channel_id is None:
            await ctx.send(
                "Please set the image channel first using the set_channel command."
            )
        else:
            await ctx.send("Forcing image check...")
            await self.image_post_task(self)

    async def cog_unload(self):
        # Stop the task when the cog is reloaded or unloaded
        if self.image_post_task.is_running():
            self.image_post_task.cancel()

    @commands.command()
    async def mai(self, ctx):
        await self.listener_functions.maii(ctx)

    @commands.command()
    async def diva(self, ctx):
        await self.listener_functions.divaa(ctx)

    async def ong(self, ctx):
        await self.listener_functions.ongg(ctx)

    @commands.command()
    async def chuni(self, ctx):
        await self.listener_functions.chunii(ctx)
