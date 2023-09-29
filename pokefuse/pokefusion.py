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
        # Check Poke 1
        veri = await VerifyName(names, name1)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name1} does not exist, Please type it again. \nRemember! Only Gen 1 Pokemons are available"
            )
        else:
            id1 = 666
            # Initial check, WILL Get replaced anyways
        try:
            # We Assign the ID based on Name
            id1 = await GetID(names, name1)
        except ValueError:
            raise ValueError("Error: Failed to retrieve the ID for the pokemon {name}")

        else:
            # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
            # END Check Poke 1

            # Check Poke 2
            veri = await VerifyName(names, name2)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name2} does not exist, Please type it again. \nRemember! Only Gen 1 Pokemons are available"
            )
        else:
            id2 = 666
        try:
            # We Assign the ID based on Name
            id2 = await GetID(names, name2)
        except ValueError:
            raise ValueError("Error: Failed to retrieve the ID for the pokemon {name2}")

        else:
            # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
            # END Check Poke 2

            mixed = await mix_names(name1, name2)
            name3 = f"{mixed}"

            try:
                url3 = f"https://images.alexonsager.net/pokemon/fused/{id2}/{id2}.{id1}.png"
            except ValueError as e:
                return await ctx.send(f"Error creating the URL: {e}")

            em = discord.Embed(description=f"{name1.title()} + {name2.title()} = {name3.title()}")
            em.title = "GEN 1 - Pokemon Fusion"
            em.color = discord.Color(8599000)
            # em.footer = "Try it with !pokefuse <Pkmn1> <pkmn2>"
            em.timestamp = datetime.now()
            em.set_image(url=url3)
            await ctx.send(embed=em)
