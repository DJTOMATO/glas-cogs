import discord
from rapidfuzz import process
from redbot.core import commands
from redbot.core.commands import BadArgument, MemberConverter
from unidecode import unidecode
from redbot.core.data_manager import bundled_data_path
import regex as re
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance
import io, os, random, re
from redbot.core.app_commands import Choice
import logging
import textwrap


async def get_font(self):
    image_width = 640
    image_height = 480
    base_font_size = 30
    font_size = max(
        int((base_font_size * min(image_width, image_height)) / image_width),
        8,
    )

    return ImageFont.truetype(self.font_path, size=font_size)


async def wrap_text(self, draw, text, x, y, max_width):
    font = await get_font(self)
    line_height = font.getsize("A")[1]

    current_x, current_y = x, y

    for line in text.split(f"\\n"):
        self.log.error("Line: %s", line)
        words = re.findall(r"(\w+)?;(.*?)(?=\w+;|$)|([^\s]+)", line)
        self.log.error("Words: %s", words)
        for word in words:
            color, content, plain_text = word

            if color:
                text_color = COLOR_CHOICES.get(color, "white")
                words = content.split(" ")
                line = ""

                for word in words:
                    test_line = line + word + " "
                    length = draw.textlength(test_line, font=font)
                    test_width = length

                    if current_x + test_width > x + max_width:
                        draw.text(
                            (current_x, current_y), line, fill=text_color, font=font
                        )
                        current_y += line_height
                        line = word + " "
                        current_x = x
                    else:
                        line = test_line

                draw.text((current_x, current_y), line, fill=text_color, font=font)
                current_x += length - draw.textlength(" ", font=font)
            elif plain_text:
                words = plain_text.split(" ")
                line = ""

                for word in words:
                    test_line = line + word + " "
                    length = draw.textlength(test_line, font=font)
                    test_width = length

                    if current_x + test_width > x + max_width:
                        draw.text((current_x, current_y), line, fill="white", font=font)
                        current_y += line_height
                        line = word + " "
                        current_x = x
                    else:
                        line = test_line

                draw.text((current_x, current_y), line, fill="white", font=font)
                current_x += length - draw.textlength(" ", font=font)

        current_y += line_height
        current_x = x


COLOR_CHOICES = {
    "red": "#ff0000",
    "blue": "#5decff",
    "golden": "#ffcc00",
    "gold": "#ffcc00",
    "white": "#ffffff",
}


LOCATION_CHOICES = {
    "airport": "Airport",
    "aquarium": "Aquarium",
    "chapel": "Chapel",
    "city": "City",
    "forest": "Forest",
    "garden": "Garden",
    "guesthouse": "Guesthouse",
    "kawhouse": "Kawhouse",
    "kumhouse": "Kumhouse",
    "mainbuilding": "Main Building",
    "nanclinic": "Nan Clinic",
    "restaurant": "Restaurant",
    "rosehouse": "Rosehouse",
    "school": "School",
    "secrethouse": "Secret House",
    "ship": "Ship",
    "subway": "Subway",
}

CHARACTER_CHOICES = {
    "Ange Ushiromiya": "ange",
    "Battler Ushiromiya": "battler",
    "Beatrice": "beatrice",
    "Bernkastel": "bernkastel",
    "Chiester 4101": "chiester41",
    "Chiester 45": "chiester45",
    "Dlanor A. Knox": "dlanor",
    "Erika Furudo": "erika",
    "Eva Ushiromiya": "eva",
    "Eva-Beatrice": "evatrice",
    "Gaap": "gaap",
    "Genji Ronoue": "genji",
    "Gohda": "gohda",
    "Jessica Ushiromiya": "jessica",
    "Kinzo Ushiromiya": "kinzo",
    "Kumasawa": "kumasawa",
    "Kyrie Ushiromiya": "kyrie",
    "Lambda Delta": "lambda",
    "Maria Ushiromiya": "maria",
    "Terumasa Nanjo": "nanjo",
    "Natsuhi Ushiromiya": "natsuhi",
    "Rosa Ushiromiya": "rosa",
    "Rudolf Ushiromiya": "rudolf",
    "Shannon": "shannon",
    "Virgilia": "virgilia",
    "Satan": "satan",
    "Beelzebub": "beelze",
    "Kanon": "kanon",
    "Sakutaro": "sakutaro",
    "Willard H. Wright": "will",
    "Zepar": "zepar",
    "Claire Vauxof Bernardus": "claire",
    "Cornelia": "cornelia",
    "Leviathan": "levia",
    "Belphegor": "belphe",
    "Amakusa": "amakusa",
    "Chiester 00": "chiester00",
    "Asmodeus": "asmo",
    "Featherine Augustus Aurora": "featherine",
    "Furfur": "furfur",
    "Lion Ushiromiya": "lion",
    "Gertrude": "gertrude",
    "Hideyoshi Ushiromiya": "hideyoshi",
    "Lucifer": "luci",
    "Mammon": "mammon",
    "Ronove": "ronove",
    "Krauss Ushiromiya": "krauss",
}


def convert_to_discord_file(image):
    with io.BytesIO() as file_content:
        image.save(file_content, format="PNG")
        file_content.seek(0)
        return discord.File(file_content, filename="image.png")


def convert_to_image(canvas):
    # If canvas is already an Image object, return it
    if isinstance(canvas, Image.Image):
        return canvas

    # Otherwise, handle the conversion logic here
    # For example, open the canvas as an image
    return Image.open(canvas)


async def background_randomizer(self, ctx, type):
    path = f"{bundled_data_path(self)}/backgrounds/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/backgrounds/{type}/{random_file}"
    return final_path


async def character_randomizer(self, ctx, type):
    type = str(type)
    path = f"{bundled_data_path(self)}/sprites/{type}"
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    random_file = random.choice(files)
    final_path = f"{bundled_data_path(self)}/sprites/{type}/{random_file}"

    try:
        # Load the image using PIL
        character_image = Image.open(final_path).convert("RGBA")

        # Check if the image has transparency
        if "A" not in character_image.getbands():
            # If the image does not have an alpha channel, create one
            alpha_image = Image.new("L", character_image.size, 255)
            character_image.putalpha(alpha_image)

    except Exception as e:
        # Log the error details
        self.log.error("An error occurred while processing the image:")
        self.log.error(str(e))
        character_image = None

    return final_path, character_image


async def generate(self, ctx, **parameters):
    # Create a dictionary with default values
    default_values = {
        "text1": "",
        "text2": "",
        "left": "",
        "center": "",
        "right": "",
        "metaleft": "",
        "metacenter": "",
        "metaright": "",
        "bg": "",
    }
    parameters = {
        key: parameters.get(key, default_value)
        for key, default_value in default_values.items()
    }

    # BG
    if parameters["bg"] is None:
        parameters["bg"] = "mainbuilding"

    final_path = await background_randomizer(self, ctx, parameters["bg"])

    # Load the background image directly as the canvas
    # Create a new transparent canvas
    canvas = Image.new("RGBA", (640, 480), (0, 0, 0, 255))

    # Load the background image
    self.log.info("Selected Background Image Path: %s", final_path)
    background = Image.open(final_path).convert("RGBA")
    self.log.info("Selected Background Image Size: %s", background.size)
    self.log.error("Background Size:: %s", background.size)
    self.log.error("Canvas Size:: %s", canvas.size)
    # Paste the background onto the canvas
    canvas.paste(background, (0, 0), background)
    self.log.info("Canvas Size after Loading Background: %s", canvas.size)
    meta_image = Image.open(
        f"{bundled_data_path(self)}/metaworld/hana1.webp"
    )  # Replace with the correct image path

    imageContainer = []
    for position in ["left", "right", "center", "metaleft", "metaright", "metacenter"]:
        if parameters[position]:
            image_path, character = await character_randomizer(
                self, ctx, CHARACTER_CHOICES[parameters[position]]
            )
            imageContainer.append((position, character))

    world = "meta"
    brightness = 0.55
    enhancer = ImageEnhance.Brightness(canvas)
    canvas = enhancer.enhance(brightness)
    canvas = canvas.filter(ImageFilter.BLUR)  # Assuming you want to remove the filter
    for position, character in imageContainer:
        if character.mode != "RGBA":
            character = character.convert("RGBA")

        if world == "meta":
            meta_position = position
            if meta_position == "left":
                # Use direct paste without alpha_composite
                canvas.paste(
                    character,
                    (int(canvas.width * -0.25), int(canvas.width * -0.05)),
                    character,
                )
            elif meta_position == "right":
                canvas.paste(
                    character,
                    (int(canvas.width * 0.41), int(canvas.width * -0.05)),
                    character,
                )
            elif meta_position == "center":
                canvas.paste(
                    character,
                    (int(canvas.width * 0.15), int(canvas.width * -0.05)),
                    character,
                )
        else:
            # Non-meta world
            if position == "left":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * -0.13),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )
            elif position == "right":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * 0.41),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )
            elif position == "center":
                canvas.paste(
                    character,
                    (
                        int(canvas.width * 0.15),
                        int(canvas.width * -0.05),
                    ),
                    character,
                )

    draw = ImageDraw.Draw(canvas)

    # Adjusted text position (start from top-left corner)
    text_position = (
        canvas.width * 0.065,
        canvas.height * 0.055,
    )
    max_width = canvas.width * 0.9

    # Wrap text using the new function
    await wrap_text(
        self, draw, parameters["text1"], text_position[0], text_position[1], max_width
    )

    # Convert the canvas to an Image object
    image = convert_to_image(canvas)

    return image


CHOICE_DESC = {
    "left": "Left character",
    "center": "Center character",
    "right": "Right character.",
    "text1": "Top text.",
    "text2": "Center text (optional).",
    "metaleft": "Meta Character",
    "metaright": "Meta Character",
    "metacenter": "Meta Character",
}

CHOICES = {
    "bg": [
        Choice(name=title, value=value) for value, title in LOCATION_CHOICES.items()
    ],
}
