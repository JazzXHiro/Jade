from settings import *
from os.path  import join
from os import walk
from pytmx.util_pygame import load_pygame

def import_folder(*path):
    frames = []
    full_path = join(*path)
    print(f"Importing from folder: {full_path}")
    for folder_path, sub_folders, image_names in walk(full_path):
        print(f"Found images: {image_names}")
        for image_name in sorted(image_names, key=lambda name: int(name.split('.')[0])):
            full_path = join(folder_path, image_name)
            print(f"Loading image: {full_path}")
            surf = pygame.image.load(full_path).convert_alpha()
            frames.append(surf)
    return frames


