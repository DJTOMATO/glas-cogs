import csv
import os
import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode


global names
global ids


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


def VerifyName(self, ctx, names, a):
    # Compare Pokemon name `a` with the list `data`
    if a in names:
        return True
    else:
        return False


async def GetID(self, ctx, ids, name):
    # Compare Pokemon ID `a` with the list `data`
    name.lower()
    name.title()
    try:
        a = ids.index(name)
        return a
    except:
        return await ctx.send(f"Fucky wucky happened while retreiving the ID, Value: {a}")

    else:
        return False
