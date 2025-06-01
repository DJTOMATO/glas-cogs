import csv
import os
from redbot.core.data_manager import bundled_data_path


def load_pokemon_data(cog_instance):
    """Loads pokemon names and IDs from the bundled CSV file."""
    loaded_names = []
    loaded_ids = []
    file_path = bundled_data_path(cog_instance) / "pkmn.csv"
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        csv_reader = list(csv.reader(csvfile, delimiter=",", quotechar="|"))
        for row in csv_reader:
            # Assuming row[0] is the ID and row[1] is the Name
            pkmn_id = row[0]
            name = row[1]
            loaded_names.append(name)
            loaded_ids.append(pkmn_id)
    return loaded_names, loaded_ids


def VerifyName(available_names, name_to_check):
    """
    Verifies if a Pokemon name exists in the provided list of names.
    Names are normalized to lower-case then title-case before comparison.
    """
    n = name_to_check
    n = n.lower()
    n = n.title()
    return n in available_names


def GetID(available_names, available_ids, name_to_find):
    """
    Retrieves the ID for a given Pokemon name from the provided lists.
    Names are normalized to lower-case then title-case before searching.
    """
    try:
        n = name_to_find
        n = n.lower()
        n = n.title()
        idx = available_names.index(n)
        return available_ids[idx]
    except ValueError:
        raise ValueError(
            f"Error: Failed to retrieve the ID for the pokemon {name_to_find}"
        )


# Thanks Autto! <3
def mix_names(a, b):
    half_a = a[: len(a) // 2 + 1]  # Take the first half of name a
    half_b = b[len(b) // 2 - 1 :]  # Take the first half of name b
    mixed_name = half_a + half_b  # Join the two halves
    return mixed_name
