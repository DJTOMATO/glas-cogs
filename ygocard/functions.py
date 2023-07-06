"""
MIT License

Copyright (c) 2020-present phenom4n4n

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode



# original converter from https://github.com/TrustyJAID/Trusty-cogs/blob/master/serverstats/converters.py#L19
class FuzzyMember(MemberConverter):
    def __init__(self, response: bool = True):
        self.response = response
        super().__init__()

    async def convert(self, ctx: commands.Context, argument: str) -> discord.Role:
        try:
            member = await super().convert(ctx, argument)
        except BadArgument:
            guild = ctx.guild
            result = [
                (m[2], m[1])
                for m in process.extract(
                    argument,
                    {m: unidecode(m.display_name) for m in guild.members},
                    limit=None,
                    score_cutoff=75,
                )
            ]
            if not result:
                raise BadArgument(f'Member "{argument}" not found.' if self.response else None)

            sorted_result = sorted(result, key=lambda r: r[1], reverse=True)
            member = sorted_result[0][0]
        return member


async def datacheck(rarity, name, level, layout, atk, defe, serial, copyright, id, attribute):
    rarity = Fixer(rarity)
    # Name Length Check
    if name.length > 15:
        pass
    else:
        raise ValueError(
            f"Error: The foil must be one of the following: \n - Normal \n - Gold \n - Platinum "
        )
    # Level Check
    if level >= 0 and level <= 13:
        pass
    else:
        raise ValueError(f"Error: The card level must be between 0 and 13")
    layout = FixerC(layout)
    # layout Check
    accepted_layout = {
        "Normal",
        "Effect",
        "Fusion",
        "Synchro",
        "Xyz",
        "Link",
        "Ritual",
        "Spell",
        "Trap",
        "Token",
    }
    if layout not in accepted_layout:
        raise ValueError(
            f"Error: The cardtype must be one of the following: \n - Normal \n - Effect \n - Fusion \n - Synchro \n - Xyz \n - Link \n - Ritual \n - Spell \n - Trap \n - Token"
        )
    # Attribute check
    accepted_attribute = {
        "Dark",
        "Earth",
        "Fire",
        "Light",
        "Water",
        "Wind",
        "Divine",
        "Spell",
        "Trap",
    }
    if attribute not in accepted_attribute:  # Ty Flame
        raise ValueError(
            f"Error: The attribute must be one of the following: 'Dark', 'Earth', 'Fire','Light', 'Water','Wind', 'Divine', 'Spell', 'Trap'"
        )
    # SetID Check
    if setid.length > 60:
        pass
    else:
        raise ValueError(f"Error: The setid must be smaller than 60 characters ")
    # CreatureType Check
    if creaturetype.length > 34:
        pass
    else:
        raise ValueError(f"Error: The creaturetype must be smaller than 34 characters ")
    # Description Check
    if desc.length > 305:
        pass
    else:
        raise ValueError(f"Error: The creaturetype must be smaller than 305 characters ")
    # ATK & DEF Check
    if atk < 9999:
        pass
    else:
        raise ValueError(f"Error: The Atk must be smaller than 9999")
    if defe < 9999:
        pass
    else:
        raise ValueError(f"Error: The Def must be smaller than 9999")
    # PWD Check
    if pwd.length > 9:
        pass
    else:
        raise ValueError(f"Error: The password must be smaller than 9 characters ")
    # Creator Check
    if creator.length > 33:
        pass
    else:
        raise ValueError(f"Error: The creator must be smaller than 33 characters ")
    # If all goes ok, create the card url


async def Fixer(a):
    try:
        n = a
        n = n.lower()
        # n = n.title()
        return n
    except ValueError:
        raise ValueError("Error: Couln't fix name for {a}")


async def FixerC(a):
    try:
        n = a
        n = n.lower()
        n = n.title()
        return n
    except ValueError:
        raise ValueError("Error: Couln't fix name for {a}")
