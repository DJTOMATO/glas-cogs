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
        # Check Poke 1
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
            # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
        # END Check Poke 1

        # Check Poke 2
        veri = await VerifyName(names, name2)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name2} does not exist, Please type it again. Check Pkmn2"
            )
        else:
            id2 = 666
            # Initial check
            print(f"The ID of the Pokemon {name2} is {id2}")
        try:
            # We Assign the ID based on Name
            id2 = await GetID(names, name2)
        except ValueError:
            raise ValueError("Error: Failed to retrieve the ID for the pokemon {name2}")
            # return f"Error: Failed to retrieve the ID for the pokemon {name}"
        else:
            print(f"After checking, The ID of the Pokemon {name2} is {id2}")
            # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
            # END Check Poke 2

            mixed = await mix_names(name1, name2)
            name3 = f"{mixed}"  # Pending, create method to fuse names

            try:
                url3 = f"https://images.alexonsager.net/pokemon/fused/{id2}/{id2}.{id1}.png"
            except ValueError as e:
                return await ctx.send(f"Error creating the URL: {e}")

            em = discord.Embed(description=f"{name1} + {name2} = {name3}")
            em.title = "Pokemon Fusion"
            em.color = discord.Color(8599000)
            em.footer = "Try it with !pokefuse <Pkmn1> <pkmn2>"
            em.set_image(url=url3)
            await ctx.send(embed=em)
