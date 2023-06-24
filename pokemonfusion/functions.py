import csv
import os
import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode


def datacheck():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}\\pkmn.csv", newline="") as csvfile:
        csv_reader = list(csv.reader(csvfile, delimiter=" ", quotechar="|"))
        names = []
        ids = []
        for row in csv_reader:
            id = row[0]
            name = row[1]
            names.append(name)
            ids.append(id)
    # print(f"The First pokemon is : {names[1]} and it's ID number is {ids[1]}")  # Output Sample


def VerifyName(self, ctx, names, name):
    # Compare Pokemon name `a` with the list `data`
    print(f"Nombre Orig: {name}")
    name.lower()
    print(f"Nombre Lower: {name}")
    name.title()
    print(f"Nombre Final: {name}")
    if name in names:
        print(names)

        return True
    else:
        return False


async def GetID(self, ctx, ids, name):
    # Obtains ID by name provided
    try:
        a = ids.index(name)
        return a
    except:
        return await ctx.send(f"Fucky wucky happened while retreiving the ID, Value: {a}")

    else:
        return False
