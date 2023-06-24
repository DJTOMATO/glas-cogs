import discord
from datetime import datetime
from redbot.core import commands
from redbot.core.bot import Red
from .functions import *

# Thanks Flame
from .functions import names, ids


# Thanks MAX <3
def __init__(self, red: Red):
    self.bot = red
    datacheck()


class PokeFusion(commands.Cog):
    """
    Fuse Gen1 Pkmns in a terrible fashion
    """

    @commands.command()
    async def pokefuse(self, ctx, name1, name2):
        """Searches for pokemons.."""

        # checks if pokemon exists in the database

        veri = VerifyName(names, name1)
        if veri == False:
            return await ctx.send(
                f"The pokemon {name1} does not exist, Please type it again. Veri1"
            )
        else:
            try:  # obtain id of such pokemon
                id1 = GetID(ids, name1)
            except:
                return await ctx.send(f"Something happened, Idk LMAO. Veri1")
            finally:
                # nothing
                # Assuming name and ID were OK, we go on
                # UNUSED url1 = f"https://images.alexonsager.net/pokemon/{id1}"

                # checks if pokemon exists in the database
                veri = VerifyName(names, name2)
                if veri == False:
                    return await ctx.send(
                        f"The pokemon {name2} does not exist, Please type it again. Veri2"
                    )
                else:
                    try:  # obtain id of such pokemon
                        id2 = GetID(ids, name2)
                    except:
                        return await ctx.send(f"Something happened, Idk LMAO. Veri2")
                    else:
                        # Assuming name and ID were OK, we go on
                        # UNUSED url2 = f"https://images.alexonsager.net/pokemon/{id1}"
                        name3 = "PLACEHOLDER UNTIL I FIND A WAY"  # Pending, create method to fuse names
                        url3 = (
                            f"https://images.alexonsager.net/pokemon/fused/{id1}/{id1}.{id2}.png"
                        )
                        em = discord.Embed(description=f"{name1} + {name2} = {name3}")
                        em.title = "Pokemon Fusion"
                        em.color = discord.Color(8599000)
                        em.timestamp = datetime.now()
                        em.set_image(url=url3)
                        await ctx.send(embed=em)
