import discord
import csv
from datetime import datetime
from redbot.core import commands


class PokeFusion(commands.Cog):
    @commands.command()
    async def pokefuse(self, ctx, a, b):
        # checks if pokemon exists in the database
        # if CheckPkmn(a) == "ok":
        # else  error("The First Pokemon Typed is wrong")

        # if not crash or return error how idk
        # Error("First pokemon is wrong, type it again")
        name1 = VerifyName(a)
        try:
            id1 = VerifyID(name1)
        except:
            return ctx.send(f"The pokemon {a} does not exist, Please type it again.")
        url1 = f"https://images.alexonsager.net/pokemon/{id1}"

        name3 = "Test"  # Pending, create method to fuse names
        url3 = f"https://images.alexonsager.net/pokemon/fused/{id1}/{id1}.{id2}.png"

        em = discord.Embed(description=f"{name1} + {name2} = {name3}")
        em.title = "Pokemon Fusion"
        em.color = discord.Color(8599000)
        em.timestamp = datetime.now()
        em.set_image(url=url3)
        await ctx.send(embed=em)

    async def CheckPkmn(id1):
        with open("/pokefusion.csv", newline="") as f:
            reader = csv.reader(f)
            data = list(reader)
            print(reader[1, 1])
