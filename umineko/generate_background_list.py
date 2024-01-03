import os

def traverse_directory(root_dir):
    background_dict = {}

    for dirpath, _, filenames in os.walk(root_dir):
        location_name = os.path.basename(dirpath)
        location_backgrounds = []

        for filename in filenames:
            if filename.endswith(('.bmp', '.webp')):
                background_path = os.path.join(dirpath, filename).replace("\\", "/")
                location_backgrounds.append({
                    'thumbnail': generate_thumbnail_path(background_path),
                    'background': background_path
                })

        if location_backgrounds:
            background_dict[location_name] = location_backgrounds

    return background_dict

def generate_thumbnail_path(background_path):
    thumbnail_path = background_path.replace('assets/backgrounds', 'assets/thumbnails/backgrounds')
    base_name, extension = os.path.splitext(os.path.basename(thumbnail_path))
    thumbnail_path = os.path.join(os.path.dirname(thumbnail_path), f"{base_name}_thumb{extension}").replace("\\", "/")
    return thumbnail_path

def generate_js_file(background_dict, output_file):
    with open(output_file, 'w') as f:
        f.write('const backgroundList = {\n')
        for location_name, location_backgrounds in background_dict.items():
            f.write(f'  "{location_name}": [\n')
            for background_info in location_backgrounds:
                f.write(f"    {{thumbnail: '{background_info['thumbnail']}', background: '{background_info['background']}'}}")
                if background_info != location_backgrounds[-1]:
                    f.write(',')
                f.write('\n')
            f.write('  ]')
            if location_name != list(background_dict.keys())[-1]:
                f.write(',')
            f.write('\n')
        f.write('};\n')

if __name__ == "__main__":
    backgrounds = 'assets/backgrounds'
    output_sprites = 'background_list.js'

    background_dict = traverse_directory(backgrounds)
    generate_js_file(background_dict, output_sprites)
