import discord
import random
from datetime import datetime
from redbot.core import commands, Config
import asyncio
from .functions import get_steam_app_list, get_app_id, get_game_prices
import logging
class SteamCog(commands.Cog):

  def __init__(self, bot):
    self.bot = bot
    self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
    self.log = logging.getLogger("glas.glas-cogs.steamer")
    
  @commands.command()
  async def searchgame(self, ctx, game_name: str):
      """Search for a game."""
      """Don't have a Steam API key? [Get it here](https://steamcommunity.com/dev/apikey)"""
      steamapi = await self.bot.get_shared_api_tokens("steam")
      if steamapi.get("api_key") is None:
          return await ctx.send("The Steam API key has not been set.")

    # Check if the user has entered a game name and API key
      if game_name and steamapi:
          # Call the function to get the list of apps
          app_list = await get_steam_app_list(steamapi)
          #self.log.warning(f"app_list: {app_list}")
          # Call the function to get appid, providing the app_list as an argument
          appid = get_app_id(game_name, app_list)

          # Check if appid is found
          if appid:
              # List of regions
              regions = ['TR', 'DE', 'US', 'UK', 'RU', 'UA', 'AR', 'CL','PE']

              # Call the function to get prices for each region
              prices_info = await get_game_prices(ctx, appid, regions)
              print(prices_info)
              # Display prices information
              for info in prices_info:
                
                await ctx.send(f'[View in Steam Store](https://store.steampowered.com/app/{appid})')

          else:
              await ctx.send("Game not found.")


   

