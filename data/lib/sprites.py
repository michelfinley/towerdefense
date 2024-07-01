import math
from dataclasses import dataclass, field
from typing import Tuple, List

import pygame


@dataclass
class SpriteData:
    images: List[pygame.Surface]
    animation_duration: List[float] = field(default_factory=list)

    # Wird benötigt, um den Laserstrahl seinen Schaden über einen längeren Zeitraum zu bewirken
    inflicted_damage: List[float] = field(default_factory=list)

    def __len__(self):
        return len(self.images)


# Folgende Klasse wurde von https://www.pygame.org/wiki/Spritesheet übernommen und leicht bearbeitet
# This class handles sprite sheets
# This was taken from www.scriptefun.com/transcript-2-using
# sprite-sheets-and-drawing-the-background
# I've added some code to fail if the file wasn't found...
# Note: When calling images_at the rect is the format:
# (x, y, x + offset, y + offset)

class Spritesheet(object):
    def __init__(self, path_or_image: str | pygame.Surface):
        """
        Class to handle spritesheets
        :param path_or_image: Path to spritesheet or existing pygame.Surface
        """
        if isinstance(path_or_image, pygame.Surface):
            self.sheet = path_or_image
        else:
            try:
                self.sheet = pygame.image.load(path_or_image).convert_alpha()
            except pygame.error as message:
                print("Unable to load spritesheet image: ", path_or_image)
                raise SystemExit(message)

    def image_at(self, rect: Tuple[int, int, int, int], colorkey=None) -> pygame.Surface:
        """
        Loads image from given coordinate
        :param rect: X, Y, image width, image height
        :param colorkey: Colorkey that should be used
        :return: Image
        """
        """Loads image from x,y,x+offset,y+offset"""
        rect = pygame.Rect(rect)
        image = pygame.Surface(rect.size, pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image

    def images_at(self, rects: List[Tuple[int, int, int, int]], colorkey=None) -> List[pygame.Surface]:
        """
        Loads multiple images
        :param rects: List of coordinates
        :param colorkey: Colorkey that should be used
        :return: List of images
        """
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(self, rect: Tuple[int, int, int, int], image_count: int, colorkey=None) -> List[pygame.Surface]:
        """
        Loads a strip of images
        :param rect: Rectangle of the first image
        :param image_count: Number of images that should be loaded
        :param colorkey: Colorkey that should be used
        :return: List of images
        """
        """Loads a strip of images and returns them as a list"""
        rects = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3])
                 for x in range(image_count)]
        return self.images_at(rects, colorkey)


def load_sprite(path: str, size: Tuple[int, int]) -> List[List[pygame.Surface]]:
    """
    Lädt Charakteranimationen aus dem gegebenen Bild
    :param path: Pfad zu der Spritesheet
    :param size: Größe des Charakters in Pixeln
    :return: Liste aller Bildreihen der Spritesheet mit den jeweiligen Bildern
    """
    spritesheet = Spritesheet(path)
    sprite = []
    sheet_width = math.floor(spritesheet.sheet.get_width() / size[0])
    for i in range(math.floor(spritesheet.sheet.get_height() / size[1])):
        sprite.append(spritesheet.load_strip((0, i * size[1], size[0], size[1]), sheet_width))
    return sprite
