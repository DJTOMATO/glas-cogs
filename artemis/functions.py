import os
import shutil
import time
import discord
import aiomysql


class ListenerFunctions:
    def __init__(self, config, linked_users):
        self.config = config
        self.linked_users = linked_users  
        self.posted_images = set()


    async def get_user_from_access_code(self, db_config, access_code):
        connection = await aiomysql.connect(**db_config)
        async with connection.cursor() as cursor:
            query = "SELECT user FROM aime_card WHERE access_code = %s;"
            await cursor.execute(query, (access_code,))
            result = await cursor.fetchone()

        if result:
            return result[0]

    async def process_image(bot, channel_id, watch_folder, linked_users, last_post_time, rate_limit, filename):
        channel = bot.get_channel(channel_id)
        if not channel:
            return

        current_time = time.time()

        parts = filename.split("_")
        if len(parts) < 1:
            return

        user_id_str = parts[0]
        user_id = int(user_id_str)

        user_mention = None

        for discord_id, user, access_code in linked_users:
            if user == user_id:
                user_mention = f"<@{discord_id}>"
                break

        if user_mention is None:
            await channel.send(f"User ID: {user_id_str} is unlinked! Link it with `!link access_code/aime.txt`")
        else:
            await channel.send(f"Score by {user_mention}:")

        file_path = os.path.join(watch_folder, filename)
        with open(file_path, 'rb') as image_file:
            _file = discord.File(image_file, filename=filename)

        await channel.send(file=_file)

        old_images_folder = '/mnt/hdd/data/artemis/oldimages/'
        new_path = os.path.join(old_images_folder, filename)

        try:
            shutil.move(file_path, new_path)
        except Exception as e:
            await channel.send(f"Failed to move the image to oldimages folder: {e}")

    async def send_user_data_embed_ong(self, ctx, result, game_type):
        embed = discord.Embed(title=f"Lena Network - {game_type} Info", color=0x7289DA)

        # Modify the list of columns to match the ongeki_profile_data table structure
        columns = [
            'id', 'user', 'version', 'userName', 'level', 'reincarnationNum', 'exp', 'point',
            'totalPoint', 'playCount', 'jewelCount', 'totalJewelCount', 'medalCount', 'playerRating',
            'highestRating', 'battlePoint', 'nameplateId', 'trophyId', 'cardId', 'characterId',
            'characterVoiceNo', 'tabSetting', 'tabSortSetting', 'cardCategorySetting', 'cardSortSetting',
            'playedTutorialBit', 'firstTutorialCancelNum', 'sumTechHighScore', 'sumTechBasicHighScore',
            'sumTechAdvancedHighScore', 'sumTechExpertHighScore', 'sumTechMasterHighScore',
            'sumTechLunaticHighScore', 'sumBattleHighScore', 'sumBattleBasicHighScore',
            'sumBattleAdvancedHighScore', 'sumBattleExpertHighScore', 'sumBattleMasterHighScore',
            'sumBattleLunaticHighScore', 'eventWatchedDate', 'cmEventWatchedDate', 'firstGameId',
            'firstRomVersion', 'firstDataVersion', 'firstPlayDate', 'lastGameId', 'lastRomVersion',
            'lastDataVersion', 'compatibleCmVersion', 'lastPlayDate', 'lastPlaceId', 'lastPlaceName',
            'lastRegionId', 'lastRegionName', 'lastAllNetId', 'lastClientId', 'lastUsedDeckId',
            'lastPlayMusicLevel', 'banStatus', 'rivalScoreCategorySetting', 'overDamageBattlePoint',
            'bestBattlePoint', 'lastEmoneyBrand', 'lastEmoneyCredit', 'isDialogWatchedSuggestMemory'
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

    async def send_user_data_embed(self, ctx, result, game_type):
        embed = discord.Embed(title=f"Lena Network - {game_type} Info", color=0x7289DA)

        columns = [
            'id', 'user', 'version', 'exp', 'level', 'point',
            'frameId', 'trophyId', 'userName', 'playCount', 'lastGameId',
            'characterId', 'firstGameId', 'friendCount', 'nameplateId',
            'totalMapNum', 'lastPlayDate', 'playerRating',
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
            'id', 'user', 'version', 'userName', 'isNetMember', 'iconId', 'plateId',
            'titleId', 'partnerId', 'frameId', 'selectMapId', 'totalAwake', 'gradeRating',
            'musicRating', 'playerRating', 'highestRating', 'gradeRank', 'classRank',
            'courseRank', 'charaSlot', 'charaLockSlot', 'contentBit', 'playCount',
            'mapStock', 'eventWatchedDate', 'lastGameId', 'lastRomVersion', 'lastDataVersion',
            'lastLoginDate', 'lastPairLoginDate', 'lastPlayDate', 'lastTrialPlayDate',
            'lastPlayCredit', 'lastPlayMode', 'lastPlaceId', 'lastPlaceName',
            'lastAllNetId', 'lastRegionId', 'lastRegionName', 'lastClientId',
            'lastCountryCode', 'lastSelectEMoney', 'lastSelectTicket', 'lastSelectCourse',
            'lastCountCourse', 'firstGameId', 'firstRomVersion', 'firstDataVersion',
            'firstPlayDate', 'compatibleCmVersion', 'dailyBonusDate', 'dailyCourseBonusDate',
            'playVsCount', 'playSyncCount', 'winCount', 'helpCount', 'comboCount',
            'totalDeluxscore', 'totalBasicDeluxscore', 'totalAdvancedDeluxscore',
            'totalExpertDeluxscore', 'totalMasterDeluxscore', 'totalReMasterDeluxscore',
            'totalSync', 'totalBasicSync', 'totalAdvancedSync', 'totalExpertSync',
            'totalMasterSync', 'totalReMasterSync', 'totalAchievement',
            'totalBasicAchievement', 'totalAdvancedAchievement', 'totalExpertAchievement',
            'totalMasterAchievement', 'totalReMasterAchievement', 'playerOldRating',
            'playerNewRating', 'dateTime', 'banState',
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

    async def post_image(channel, file_path, filename, linked_users_data, posted_images, last_post_time):
        print("Posting image...")
        linked_users_data = await self.config.linked_users_data()

        if filename in self.posted_images:
            return

        parts = filename.split("_")
        if len(parts) < 1:
            return

        user_id_str = parts[0]
        user_id = int(user_id_str)

        user_mention = None

        if linked_users_data is None:
            print("linked_users_data is None")
            return

        for discord_id, user_id_num in linked_users_data.items():
            print(f"discord_id: {discord_id}, user_id_num: {user_id_num}")

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
