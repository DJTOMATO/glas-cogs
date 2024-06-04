import discord
import random
from datetime import datetime
from redbot.core import commands
import aiohttp


class redbusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def red(self, ctx: commands.Context, stop: commands.Range[str, 1, 6] = None):
        if not stop:
            await ctx.send("Please provide a valid bus stop ID.")
            return

        query = f"https://api.xor.cl/red/bus-stop/{stop}"

        async with aiohttp.ClientSession() as session:
            async with session.get(query) as response:
                if response.status != 200:
                    await ctx.send(
                        f"Failed to retrieve data. Status code: {response.status}"
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
                buses_info += f"\n    Patente: {bus_id}, Distancia: {meters_distance}m, Arrivo: **{min_arrival_time}-{max_arrival_time} minutos**"

            services_info += (
                f"\nBus: {service_id}, Estado: {service_status}{buses_info}\n"
            )

        em = discord.Embed(
            description=f"__Paradero__: {stop_id}\n__Nombre__: {stop_name}\n__Estado__: {status_description}\n\n__**Buses en Camino**__:{services_info}"
        )
        em.set_image(url=f"https://c.tenor.com/E4JPqf5mDskAAAAC/tenor.gif")
        em.color = discord.Color(0x859900)
        em.timestamp = datetime.utcnow()

        await ctx.send(embed=em)
