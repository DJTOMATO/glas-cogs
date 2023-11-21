import os
import shutil
import time
import discord
import aiomysql
import pymysql.err
import logging
from redbot.core import Config, commands


class ListenerFunctions:
    def __init__(self, config, linked_users):
        self.config = config
        self.linked_users = linked_users
        self.posted_images = set()
        self.old_images_folder = self.config.old_images_folder
        self.channel_id = self.config.channel_id()
        self.log = logging.getLogger("glas.glas-cogs.artemis")

    async def get_user_from_access_code(self, db_config, access_code):
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            query = "SELECT user FROM aime_card WHERE access_code = %s;"
            await cursor.execute(query, (access_code,))
            result = await cursor.fetchone()

        if result:
            return result[0]

    async def send_user_data_embed_ong(self, ctx, result, game_type):
        embed = discord.Embed(title=f"Lena Network - {game_type} Info", color=0x7289DA)

        # Modify the list of columns to match the ongeki_profile_data table structure
        columns = [
            "id",
            "user",
            "version",
            "userName",
            "level",
            "reincarnationNum",
            "exp",
            "point",
            "totalPoint",
            "playCount",
            "jewelCount",
            "totalJewelCount",
            "medalCount",
            "playerRating",
            "highestRating",
            "battlePoint",
            "nameplateId",
            "trophyId",
            "cardId",
            "characterId",
            "characterVoiceNo",
            "tabSetting",
            "tabSortSetting",
            "cardCategorySetting",
            "cardSortSetting",
            "playedTutorialBit",
            "firstTutorialCancelNum",
            "sumTechHighScore",
            "sumTechBasicHighScore",
            "sumTechAdvancedHighScore",
            "sumTechExpertHighScore",
            "sumTechMasterHighScore",
            "sumTechLunaticHighScore",
            "sumBattleHighScore",
            "sumBattleBasicHighScore",
            "sumBattleAdvancedHighScore",
            "sumBattleExpertHighScore",
            "sumBattleMasterHighScore",
            "sumBattleLunaticHighScore",
            "eventWatchedDate",
            "cmEventWatchedDate",
            "firstGameId",
            "firstRomVersion",
            "firstDataVersion",
            "firstPlayDate",
            "lastGameId",
            "lastRomVersion",
            "lastDataVersion",
            "compatibleCmVersion",
            "lastPlayDate",
            "lastPlaceId",
            "lastPlaceName",
            "lastRegionId",
            "lastRegionName",
            "lastAllNetId",
            "lastClientId",
            "lastUsedDeckId",
            "lastPlayMusicLevel",
            "banStatus",
            "rivalScoreCategorySetting",
            "overDamageBattlePoint",
            "bestBattlePoint",
            "lastEmoneyBrand",
            "lastEmoneyCredit",
            "isDialogWatchedSuggestMemory",
        ]

        for i, column_name in enumerate(columns):
            column_value = result[i]
            embed.add_field(name=column_name, value=column_value, inline=True)

        user_id = None
        for _, user, _ in self.linked_users:
            if ctx.author.id == _:
                user_id = user
                break

        # Fetch the user's avatar and set it as a thumbnail in the embed
        user = ctx.author
        avatar_url = user.avatar.with_static_format("png")
        embed.set_thumbnail(url=avatar_url)
        await ctx.send(embed=embed)

    async def get_conn_config(self):
        # Retrieve database configuration
        return await self.config.db_config()

    async def send_user_data_embed(self, ctx, result, game_type):
        embed = discord.Embed(title=f"Lena Network - {game_type} Info", color=0x7289DA)

        columns = [
            "id",
            "user",
            "version",
            "exp",
            "level",
            "point",
            "frameId",
            "trophyId",
            "userName",
            "playCount",
            "lastGameId",
            "characterId",
            "firstGameId",
            "friendCount",
            "nameplateId",
            "totalMapNum",
            "lastPlayDate",
            "playerRating",
        ]
        for i, column_name in enumerate(columns):
            column_value = result[i]
            embed.add_field(name=column_name, value=column_value, inline=True)

        user_id = None
        for _, user, _ in self.linked_users:
            if ctx.author.id == _:
                user_id = user
                break

        # Fetch the user's avatar and set it as a thumbnail in the embed
        user = ctx.author
        avatar_url = user.avatar.with_static_format("png")
        embed.set_thumbnail(url=avatar_url)

        # Send the embed
        await ctx.send(embed=embed)

    async def send_user_data_embed_mai(self, ctx, result, game_type):
        # Create an embed to display the retrieved data
        embed = discord.Embed(title=f"Lena Network - {game_type} Info", color=0x7289DA)

        # Define the list of columns to match the mai2_profile_detail table structure
        columns = [
            "id",
            "user",
            "version",
            "userName",
            "isNetMember",
            "iconId",
            "plateId",
            "titleId",
            "partnerId",
            "frameId",
            "selectMapId",
            "totalAwake",
            "gradeRating",
            "musicRating",
            "playerRating",
            "highestRating",
            "gradeRank",
            "classRank",
            "courseRank",
            "charaSlot",
            "charaLockSlot",
            "contentBit",
            "playCount",
            "mapStock",
            "eventWatchedDate",
            "lastGameId",
            "lastRomVersion",
            "lastDataVersion",
            "lastLoginDate",
            "lastPairLoginDate",
            "lastPlayDate",
            "lastTrialPlayDate",
            "lastPlayCredit",
            "lastPlayMode",
            "lastPlaceId",
            "lastPlaceName",
            "lastAllNetId",
            "lastRegionId",
            "lastRegionName",
            "lastClientId",
            "lastCountryCode",
            "lastSelectEMoney",
            "lastSelectTicket",
            "lastSelectCourse",
            "lastCountCourse",
            "firstGameId",
            "firstRomVersion",
            "firstDataVersion",
            "firstPlayDate",
            "compatibleCmVersion",
            "dailyBonusDate",
            "dailyCourseBonusDate",
            "playVsCount",
            "playSyncCount",
            "winCount",
            "helpCount",
            "comboCount",
            "totalDeluxscore",
            "totalBasicDeluxscore",
            "totalAdvancedDeluxscore",
            "totalExpertDeluxscore",
            "totalMasterDeluxscore",
            "totalReMasterDeluxscore",
            "totalSync",
            "totalBasicSync",
            "totalAdvancedSync",
            "totalExpertSync",
            "totalMasterSync",
            "totalReMasterSync",
            "totalAchievement",
            "totalBasicAchievement",
            "totalAdvancedAchievement",
            "totalExpertAchievement",
            "totalMasterAchievement",
            "totalReMasterAchievement",
            "playerOldRating",
            "playerNewRating",
            "dateTime",
            "banState",
        ]

        # Add data to the embed
        for i, column_name in enumerate(columns):
            column_value = result[i]
            embed.add_field(name=column_name, value=column_value, inline=True)

        # Fetch the user's avatar and set it as a thumbnail in the embed
        user = ctx.author
        avatar_url = user.avatar.with_static_format("png")
        embed.set_thumbnail(url=avatar_url)

        # Send the embed
        await ctx.send(embed=embed)

    # A helper async function to get the linked user's ID based on their Discord ID
    async def linked_user_id(self, ctx):
        discord_id = ctx.author.id
        linked_users = await self.config.linked_users()
        for _, result_user_id, _ in linked_users:
            if ctx.author.id == _:
                return result_user_id
        return None

    async def link(self, discord_id, user_id, access_code, channel):
        try:
            user = await self.listener_functions.get_user_from_access_code(
                self.db_config, access_code
            )
        except pymysql.err.OperationalError as e:
            # Handle the specific error for MySQL connection issues
            await channel.send(f"Error connecting to the database: {e}")
            return
        except Exception as e:
            # Handle other exceptions if needed
            await channel.send(f"An error occurred: {e}")
            return

        if user is not None:
            linked_users = await self.config.linked_users()
            linked_users.append((discord_id, user, access_code))
            await self.config.linked_users.set(linked_users)  # Save the updated list

            # Extract the last 4 digits of the access_code
            last_4_digits = access_code[-4:]

            # Send a message displaying only the last 4 digits of the access_code
            await channel.send(
                f"You are now linked as user {user} with access code ending in {last_4_digits}"
            )
        else:
            await channel.send("Invalid access code. Please check and try again.")

    async def ongg(self, ctx):
        """Returns ONG Data for the linked user"""
        discord_id = ctx.author.id

        linked_users = await self.config.linked_users()

        for linked_discord_id, user_id, _ in linked_users:
            if linked_discord_id == discord_id:
                user_id = user_id
                break
        else:
            await ctx.send("You are not linked to another user.")
            return
        # Retrieve database configuration
        db_config = await self.get_conn_config()

        # Establish a database connection
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            query = f"SELECT * FROM ongeki_profile_data WHERE user = {user_id};"
            await cursor.execute(query)
            result = await cursor.fetchone()

        if result:
            await self.send_user_data_embed_ong(ctx, result, "ONG")

        else:
            await ctx.send("No data found for this user.")

    async def chunii(self, ctx):
        """Returns chuni Data for the linked user"""
        discord_id = ctx.author.id

        linked_users = await self.config.linked_users()

        for linked_discord_id, user_id, _ in linked_users:
            if linked_discord_id == discord_id:
                user_id = user_id
                break
        else:
            await ctx.send("You are not linked to another user.")
            return
        # Retrieve database configuration
        db_config = await self.get_conn_config()

        # Establish a database connection
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            query = f"SELECT * FROM chuni_profile_data WHERE user = {user_id};"
            await cursor.execute(query)
            result = await cursor.fetchone()

        if result:
            await self.send_user_data_embed(ctx, result, "Chunithm")

        else:
            await ctx.send("No data found for this user.")

    async def divaa(self, ctx):
        """Returns diva Data for the linked user"""
        discord_id = ctx.author.id

        linked_users = await self.config.linked_users()

        for linked_discord_id, user_id, _ in linked_users:
            if linked_discord_id == discord_id:
                user_id = user_id
                break
        else:
            await ctx.send("You are not linked to another user.")
            return

        # Retrieve database configuration
        db_config = await self.get_conn_config()

        # Establish a database connection
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            query = f"SELECT * FROM diva_profile WHERE user = {user_id};"
            await cursor.execute(query)
            result = await cursor.fetchone()

        if result:
            await self.send_user_data_embed(ctx, result, "Diva")
        else:
            await ctx.send("No data found for this user.")

    async def maii(self, ctx):
        """Returns mai Data for the linked user"""
        discord_id = ctx.author.id

        linked_users = await self.config.linked_users()
        user_id = None

        # Find the linked user for the current Discord user
        for linked_discord_id, result_user_id, _ in linked_users:
            if linked_discord_id == discord_id:
                user_id = result_user_id
                break

        # Check if a user_id was found
        if user_id is None:
            await ctx.send("You are not linked to another user.")
            return

        # Establish a database connection
        # Retrieve database configuration
        db_config = await self.get_conn_config()

        # Establish a database connection
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            # Create and execute the SQL query to fetch mai data
            query = f"SELECT * FROM mai2_profile_detail WHERE user = {user_id};"
            await cursor.execute(query)
            result = await cursor.fetchone()

        # Check if data was found
        if result:
            await self.send_user_data_embed_mai(ctx, result, "Mai")

        else:
            await ctx.send("No data found for this user.")
