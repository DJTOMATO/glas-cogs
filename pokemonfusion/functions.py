import csv
import os
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode

# ~~Global~~ vars to store data
names = []
ids = []


def datacheck():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(f"{dir_path}/pkmn.csv", newline="") as csvfile:
        csv_reader = list(csv.reader(csvfile, delimiter=" ", quotechar="|"))
        for row in csv_reader:
            id = row[0]
            name = row[1]
            names.append(name)
            ids.append(id)


datacheck()


def VerifyName(names, name):
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


async def GetID(ids, name):
    # Obtains ID by name provided
    try:
        a = ids.index(name)
        return a
    except ValueError:
        return f"Fucky wucky happened while retrieving the ID, Value: {name}"