import discord
from datetime import datetime
from redbot.core import commands
import aiohttp
from redbot.core.i18n import Translator

# Initialize the translator
# The first argument is a unique name for your cog's translations (usually the cog name).
_ = Translator("RedBus", __file__)


class RedBus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def red(self, ctx: commands.Context, stop: commands.Range[str, 1, 6] = None):
        """Check the status of a bus stop in Santiago, Chile.

        Provide a bus stop ID (like PAXXX, e.g., PA417) to get information about the stop and its incoming buses.
        Usage: [p]red <stop_id>"""

        if not ctx.channel.permissions_for(ctx.me).embed_links:
            await ctx.send(_("I don't have permission to embed links in this channel."))
            return
        if not stop:
            await ctx.send(
                _("Please provide a valid bus stop ID. Like PAXXX (Ex: PA417)")
            )
            return

        query = f"https://api.xor.cl/red/bus-stop/{stop}"
        async with aiohttp.ClientSession() as session:
            async with session.get(query) as response:
                if response.status != 200:
                    await ctx.send(
                        _("Failed to retrieve data. Status code: {status}").format(
                            status=response.status
                        )
                    )
                    return

                data = await response.json()

        stop_id = data["id"]
        stop_name = data["name"]
        status_code = data["status_code"]
        status_description = data["status_description"]
        services = data["services"]

        services_info = ""
        for service in services:
            service_id = service["id"]
            service_status = service["status_description"]
            buses_info = ""
            for bus in service["buses"]:
                bus_id = bus["id"]
                meters_distance = bus["meters_distance"]
                min_arrival_time = bus["min_arrival_time"]
                max_arrival_time = bus["max_arrival_time"]
                # Previous diff changed Spanish to English:
                # buses_info += f"\n    ID: {bus_id}, Distance: {meters_distance}m, Arrival: **{min_arrival_time}-{max_arrival_time} minutes**"
                # Now, make it translatable:
                bus_line_format = _(
                    "\n    ID: {bus_id}, Distance: {meters_distance}m, Arrival: **{min_arrival_time}-{max_arrival_time} minutes**"
                )
                buses_info += bus_line_format.format(
                    bus_id=bus_id,
                    meters_distance=meters_distance,
                    min_arrival_time=min_arrival_time,
                    max_arrival_time=max_arrival_time,
                )

            # Previous diff changed Spanish to English:
            # services_info += f"\nBus: {service_id}, Status: {service_status}{buses_info}\n"
            # Now, make it translatable:
            service_line_format = _(
                "\nBus: {service_id}, Status: {service_status}{buses_info}\n"
            )
            services_info += service_line_format.format(
                service_id=service_id,
                service_status=service_status,
                buses_info=buses_info,
            )

        embed_description_format = _(
            "__Stop ID__: {stop_id}\n__Name__: {stop_name}\n__Status__: {status_description}\n\n__**Incoming Buses**__:{services_info}"
        )
        em = discord.Embed(
            description=embed_description_format.format(
                stop_id=stop_id,
                stop_name=stop_name,
                status_description=status_description,
                services_info=services_info,
            )
        )
        em.set_image(url=f"https://c.tenor.com/E4JPqf5mDskAAAAC/tenor.gif")
        em.color = discord.Color(0x859900)
        em.timestamp = datetime.utcnow()

        await ctx.send(embed=em)

    # Command that should return bus card balance, but afaik it's broken.
    # @commands.command()
    # async def saldo(self, ctx: commands.Context, card_id: str):
    #     # Delete the command message
    #     await ctx.message.delete()

    #     query = f"https://api.xor.cl/red/balance/{card_id}"

    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(query) as response:
    #             if response.status != 200:
    #                 await ctx.send(
    #                     _("Failed to retrieve data. Status code: {status}").format(
    #                         status=response.status
    #                     )
    #                 )
    #                 return

    #             data = await response.json()

    #     card_id = data["id"]
    #     masked_card_id = "XXXXXXX" + card_id[-3:]
    #     status_code = data["status_code"]
    #     status_description = data["status_description"]
    #     balance = data["balance"]

    #     embed_saldo_desc_format = _("__BIP! Card__: {masked_card_id}\n__Status__: {status_code} - {status_description}\n__Balance__: ${balance}")
    #     em = discord.Embed(
    #         description=embed_saldo_desc_format.format(masked_card_id=masked_card_id, status_code=status_code, status_description=status_description, balance=balance)
    #     )
    #     em.color = discord.Color(0x859900)
    #     em.timestamp = datetime.utcnow()

    #     await ctx.send(embed=em)
