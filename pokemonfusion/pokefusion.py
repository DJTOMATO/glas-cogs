import discord
from datetime import datetime
from redbot.core import commands
from redbot.core.bot import Red
from .functions import *

# Thanks Flame
from .functions import names, ids


# Thanks MAX <3
async def __init__(self, red: Red):
    self.bot = red
    datacheck()


class PokeFusion(commands.Cog):
    """
    Fuse Gen1 Pkmns in a terrible fashion
    """

    @commands.command()
    async def pokefuse(self, ctx, name1, name2):
        """Searches for pokemons.."""
        await datacheck()
        # checks if pokemon exists in the database
        veri = await VerifyName(names, name1)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name1} does not exist, Please type it again. Check Pkmn1"
            )
        else:
            id1 = 666
            # Initial check
            print(f"The ID of the Pokemon {name1} is {id1}")
        try:
            # We Assign the ID based on Name
            id1 = await GetID(names, name1)
        except ValueError:
            raise ValueError("Error: Failed to retrieve the ID for the pokemon {name}")
            # return f"Error: Failed to retrieve the ID for the pokemon {name}"
        else:
            print(f"After checking, The ID of the Pokemon {name1} is {id1}")

            # Assuming name and ID were OK, we go on
            # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
            name3 = "PLACEHOLDER UNTIL I FIND A WAY"  # Pending, create method to fuse names
            print(f"id1 = {id1}")
            id2 = 2
            # print(f"id2 = {id2}")
            try:
                url3 = f"https://images.alexonsager.net/pokemon/fused/{id1}/{id1}.{id2}.png"
            except ValueError as e:
                return await ctx.send(f"Error creating the URL: {e}")

            em = discord.Embed(description=f"{name1} + {name2} = {name3}")
            em.title = "Pokemon Fusion"
            em.color = discord.Color(8599000)
            em.timestamp = datetime.now()
            em.set_image(url=url3)
            await ctx.send(embed=em)
