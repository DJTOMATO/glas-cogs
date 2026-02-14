import discord
from datetime import datetime
from redbot.core import commands
from redbot.core.bot import Red
from .functions import load_pokemon_data, VerifyName, GetID, mix_names


class PokeFuse(commands.Cog):
    """
    Fuse Gen1 Pkmns in a terrible fashion
    """

    # Thanks MAX <3
    def __init__(self, red: Red):
        self.bot = red
        self.pokemon_names, self.pokemon_ids = load_pokemon_data(self)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def pokefuse(self, ctx: commands.Context, name1: str, name2: str):
        """Searches for pokemons..

        Example: [p]pokefuse Pikachu Bulbasaur"""



        # Check Poke 1
        if not VerifyName(self.pokemon_names, name1):
            return await ctx.send(
                f"The pokemon '{name1}' does not exist. Please type it again. \nRemember! Only Gen 1 Pokemons are available."
            )
        try:
            id1 = GetID(self.pokemon_names, self.pokemon_ids, name1)
        except ValueError as e:
            return await ctx.send(str(e))

        # Check Poke 2
        if not VerifyName(self.pokemon_names, name2):
            return await ctx.send(
                f"The pokemon '{name2}' does not exist. Please type it again. \nRemember! Only Gen 1 Pokemons are available."
            )
        try:
            id2 = GetID(self.pokemon_names, self.pokemon_ids, name2)
        except ValueError as e:
            return await ctx.send(str(e))

        mixed_name = mix_names(name1, name2)
        url_id1 = id1
        url_id2 = id2

        # The URL structure is fused/HEAD_ID/HEAD_ID.BODY_ID.png
        # Here, name1 provides the body and name2 provides the head.
        # So, id1 is body, id2 is head.
        fusion_image_url = f"https://images.alexonsager.net/pokemon/fused/{url_id2}/{url_id2}.{url_id1}.png"

        em = discord.Embed(
            description=f"{name1.title()} + {name2.title()} = {mixed_name.title()}"
        )
        em.title = "GEN 1 - Pokemon Fusion"
        em.color = discord.Color(8599000)  # This is a specific shade of blue-green
        em.timestamp = datetime.utcnow()
        em.set_image(url=fusion_image_url)
        await ctx.send(embed=em)
