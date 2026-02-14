from random import choice
import discord

from .ogeys import ogey


async def summon_ogey(self, ctx, type: str):
    """Summon a Ogey."""
    # Check if the bot has embed_links permission
    if not ctx.channel.permissions_for(ctx.me).embed_links:
        return await ctx.send("I don't have permission to send embeds in this channel.")
    
    e = discord.Embed(color=await ctx.embed_color())
    if type == "random":
        # Fixed: ogey_calling_ritual function is not defined, so we'll use the image list directly
        e.title = f"Here's a Random Ogey! 🐀"
        e.set_image(url=choice(ogey["image"]))  # Fallback to image list
        e.set_footer(
            text="Source: https://fumoapi.herokuapp.com/",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    else:
        e.title = f"Here's a Random Ogey {type.title()}! 🐀"
        e.set_image(url=choice(ogey[type]))
        e.set_footer(
            text="Code by Kuro",
            icon_url="https://i.kym-cdn.com/photos/images/newsfeed/002/240/804/333.png",
        )
    await ctx.send(embed=e)
