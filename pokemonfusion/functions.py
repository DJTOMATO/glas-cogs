import csv
import os
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode
import discord

# ~~Global~~ vars to store data
names = []
ids = []


async def datacheck():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}/pkmn.csv", newline="") as csvfile:
        csv_reader = list(csv.reader(csvfile, delimiter=" ", quotechar="|"))
        for row in csv_reader:
            id = row[0]
            name = row[1]
            names.append(name)
            ids.append(id)


async def VerifyName(names, name):
    # Compare Pokemon name `a` with the list `data`
    n = name
    n = n.lower()
    n = n.title()
    if n in names:
        print(f"{n} = true")
        return True
    else:
        print(f"{n} = false")
        return False


async def GetID(ids, name):
    # Obtains ID by name provided
    try:
        a = ids.index(name)
        return a
    except ValueError:
        return await ctx.send(f"Fucky wucky happened while retrieving the ID, Value: {name}")
