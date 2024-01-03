import os

def traverse_directory(root_dir):
    sprite_map = {}

    for dirpath, _, filenames in os.walk(root_dir):
        folder_name = os.path.basename(dirpath)
        sprite_paths = [os.path.join('assets/sprites', folder_name, filename) for filename in filenames if filename.endswith(".webp")]
        thumbnail_paths = [os.path.join('assets/thumbnails/sprites', folder_name, filename.rsplit(".", 1)[0] + "_thumb.webp") for filename in filenames if filename.endswith(".webp")]
        sprite_paths.sort()  # Sort the sprite paths
        thumbnail_paths.sort()  # Sort the thumbnail paths
        sprite_map[folder_name] = {'sprites': sprite_paths, 'thumbnails': thumbnail_paths}

    return sprite_map

def generate_js_file(sprite_map, output_file):
    with open(output_file, 'w') as f:
        f.write('const spriteMap = {\n')
        for folder_name, paths in sorted(sprite_map.items()):  # Sort the sprite_map items by folder_name
            if folder_name == "sprites":
                continue
            f.write(f"  '{folder_name}': [\n")
            for thumbnail_path, sprite_path in zip(paths['thumbnails'], paths['sprites']):
                f.write(f"    {{thumbnail: '{thumbnail_path}', sprite: '{sprite_path}'}},\n")
            f.write('  ],\n')
        f.write('};\n\n')

if __name__ == "__main__":
    sprites_dir = 'assets/sprites'
    output_sprites = 'sprite_map.js'

    sprite_map = traverse_directory(sprites_dir)
    generate_js_file(sprite_map, output_sprites)