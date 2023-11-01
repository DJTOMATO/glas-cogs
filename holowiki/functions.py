import json
import discord
import re

# Function to search for names
def search(names, keyword):
    matching_names = []
    for entry in names:
        if keyword.lower() in entry["Name"].lower():
            matching_names.append(entry)
    return matching_names

# Thank you AAA3A <3
def get_emoji_by_iurl(self, iurl):
    for entry in self.chuubas:
        if iurl in entry['url']:
            return entry['emoji']
    return None

def import_json_file(ctx, file_path):
    print(file_path)
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data
async def on_error(self, interaction, error, item):
    await self.ctx.cog.log.error("Exception in a view.", exc_info=error)

async def callback(self, interaction: discord.Interaction, image_url: str, embed: discord.Embed):
    emb = embed
    emb.set_image(url=image_url)
    #Thanks Flame!!
    await interaction.response.edit_message(embed=emb)
    

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

async def extract_label(self, url):
  
    file_name = url.split('/')[-1]
    file_name = file_name.replace('_', ' ')

    if 'Portrait' in file_name and 'Portrait 3D' not in file_name:
        label = 'Portrait'
        number = re.search(r'(\d+)(?=[\d]*\.(png|jpg))', file_name)
    elif 'Portrait 3D' in file_name:
        label = 'Portrait 3D'
        number = re.search(r'(\d+)(?=[\d]*\.(png|jpg))', file_name)
    elif '3D Model' in file_name:
        label = '3D Model'
        number = re.search(r'(\d+)(?=[\d]*\.(png|jpg))', file_name)
    elif 'Signature' in file_name:
        label = 'Signature'
        number = None
    elif 'Alternative' in file_name:
        label = 'Alternative Costume'
        number = None
    elif 'YouTube Profile Picture' in file_name:
        label = 'YouTube Profile Picture'
        number = None
    else:
        label = None
        number = None
    
    if number:
        number = number.group(0)
        label += " " + number
    
    return label

