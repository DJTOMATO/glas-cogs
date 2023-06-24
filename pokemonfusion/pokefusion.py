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
        print(names)
        print(ids)
        veri = await VerifyName(names, name1)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name1} does not exist, Please type it again. Check Pkmn1"
            )
        else:
            try:  # obtain id of such pokemon
                print(id1)
                id1 = await GetID(ids, name1)
                print(id1)
            except:
                return await ctx.send(f"Something happened, Idk LMAO. Check Pkmn1")
            finally:
                # nothing
                # Assuming name and ID were OK, we go on
                # UNUSED url1 = f"https://images.alexonsager.net/pokemon/{id1}"

                # checks if pokemon exists in the database
                id1 = 1
                id2 = 2
                veri2 = await VerifyName(names, name2)
                if veri2 == False:
                    return await ctx.send(
                        f"The pokemon {name2} does not exist, Please type it again. Check Pkmn2"
                    )
                else:
                    try:  # obtain id of such pokemon
                        print(id2)
                        id2 = await GetID(ids, name2)
                        print(id2)
                    except:
                        return await ctx.send(f"Something happened, Idk LMAO. Check Pkmn2")
                    else:
                        # Assuming name and ID were OK, we go on
                        # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
                        name3 = "PLACEHOLDER UNTIL I FIND A WAY"  # Pending, create method to fuse names
                        print(f"id1 = {id1}")
                        print(f"id2 = {id2}")
                        try:
                            url3 = f"https://images.alexonsager.net/pokemon/fused/{id1}/{id1}.{id2}.png"
                        except ValueError:
                            return await ctx.send(f"Error Creating the URL: {ValueError}")
                        em = discord.Embed(description=f"{name1} + {name2} = {name3}")
                        em.title = "Pokemon Fusion"
                        em.color = discord.Color(8599000)
                        em.timestamp = datetime.now()
                        em.set_image(url=url3)
                        await ctx.send(embed=em)
