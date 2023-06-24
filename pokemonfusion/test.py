import csv
import os

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

    print(f"The First pokemon is : {names[1]} and it's ID number is {ids[1]}")  # Output Sample
