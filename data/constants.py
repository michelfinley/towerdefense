from enum import Enum
from typing import Tuple, Dict

import pygame

from data.lib import sprites, vfx_utils


# <editor-fold desc="Resource locations">
class Resources:
    FONTS = "resources/fonts/"
    UI = "resources/visual/ui/"
    EFFECTS = "resources/visual/vfx/"
    MAP = "resources/visual/maps/pillowbyte_diceforce_td/td_512x288.tmx"
    SPRITES = "resources/visual/sprites/"


class Font(Enum):
    PIXEL = Resources.FONTS + "pixel-tandysoft-font/PixelTandysoft-0rJG.ttf"
    AZONIX = Resources.FONTS + "azonix-font/Azonix-1VB0.otf"


class UI:
    BOX = Resources.UI + "UI_box2.png"
    ICONS = Resources.UI + "UI_icons.png"


class ResEffect:
    BULLET = Resources.EFFECTS + "Bullet.png"
    BEAM = Resources.EFFECTS + "Laser.png"
    EXPLOSION = Resources.EFFECTS + "Explode_effect.png"
    BULLET_ANTICIPATION = Resources.EFFECTS + "Bullet_anticipation.png"
    BULLET_IMPACT = Resources.EFFECTS + "Bullet_impact.png"


class Sprite:
    BLUE_TURRET = Resources.SPRITES + "Tower_blue.png"
    RED_TURRET = Resources.SPRITES + "Tower_red.png"
    ENEMIES = Resources.SPRITES + "Enemies.png"
# </editor-fold>


# <editor-fold desc="General">
class Color:
    BACKGROUND = (36, 34, 52, 255)
    OVERLAY_COLLIDE = (255, 0, 0, 50)
    OVERLAY_VALID = (0, 255, 0, 50)
    OVERLAY_INFO = (0, 0, 255, 35)


class Direction(Enum):
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOT = 3
# </editor-fold>


# <editor-fold desc="Game">
class Map:
    SPAWN = "enemy_spawn"
    CONSTRUCTION_ZONE = "defense_area"


class MapLayer(Enum):
    Base = 0
    Default = 1

    Enemy = 10
    EnemyOverlay = 11

    TurretBase = 20
    TurretBaseOverlay = 21

    Projectiles = 100

    Turret = 200
    TurretOverlay = 201

    VFX = 5000


class TurretType:
    BLUE = 1
    RED = 2


class AimMode(Enum):
    """
    Zielmodi eines Turmes (erster, kürzeste Distanz, größte Distanz, zufälliger oder stärkster Gegner)
    """
    First = 0
    Nearest = 1
    Last = 2
    Random = 3
# </editor-fold>


# <editor-fold desc="Pre-loaded PyGame objects">
class FontManager:
    cache: Dict[Font, Dict[int, pygame.font.Font]] = {}

    @staticmethod
    def pre_load():
        FontManager.get_font(Font.PIXEL, 12)

    @staticmethod
    def get_font(font_type: Font, font_size: int):
        if font_type not in Font:
            raise ValueError("Not a valid font type")
        if font_type not in FontManager.cache.keys():
            FontManager.cache[font_type] = {}
        if font_size not in FontManager.cache[font_type].keys():
            font = pygame.font.Font(font_type.value, font_size)
            FontManager.cache[font_type][font_size] = font

        return FontManager.cache[font_type][font_size]


class Icon(Enum):
    SETTINGS = 0
    PAUSE = 1
    PLAY = 2
    DOUBLE_SPEED = 3
    TRIPLE_SPEED = 4
    HEART = 5


class IconManager:
    cache: Dict[Icon, Dict[Tuple[Tuple[int, int, int], bool], pygame.Surface]] = {}

    @staticmethod
    def pre_load():
        IconManager.get_icon(Icon.SETTINGS)
        IconManager.get_icon(Icon.PAUSE)
        IconManager.get_icon(Icon.PLAY)
        IconManager.get_icon(Icon.DOUBLE_SPEED)
        IconManager.get_icon(Icon.TRIPLE_SPEED)
        IconManager.get_icon(Icon.HEART, (255, 0, 0))

    @staticmethod
    def get_icon(icon_type: Icon, color: Tuple[int, int, int] = (255, 255, 255), outline: bool = True):
        if icon_type not in IconManager.cache.keys():
            IconManager.cache[icon_type] = {}
        if (color, outline) not in IconManager.cache[icon_type].keys():
            if icon_type == Icon.SETTINGS:
                icon = sprites.Spritesheet(UI.ICONS).image_at((16, 0, 16, 16))
                for x in range(icon.get_width()):
                    for y in range(icon.get_height()):
                        icon.set_at((x, y), (100, 100, 100, icon.get_at((x, y))[3]))
                icon = vfx_utils.get_outline(icon, (200, 200, 200))
                icon = pygame.transform.scale(icon, (32, 32))

            elif icon_type == Icon.PAUSE:
                icon = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.rect(icon, color, (5, 4, 2, 8))
                pygame.draw.rect(icon, color, (9, 4, 2, 8))
                if outline:
                    icon = vfx_utils.get_outline(icon)

            elif icon_type == Icon.PLAY:
                icon = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.polygon(icon, color, ((6, 4), (9, 7), (6, 11)))
                if outline:
                    icon = vfx_utils.get_outline(icon)

            elif icon_type == Icon.DOUBLE_SPEED:
                icon = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.polygon(icon, color, ((4, 4), (7, 7), (4, 11)))
                pygame.draw.polygon(icon, color, ((8, 4), (11, 7), (8, 11)))
                if outline:
                    icon = vfx_utils.get_outline(icon)

            elif icon_type == Icon.TRIPLE_SPEED:
                icon = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.polygon(icon, color, ((2, 4), (5, 7), (2, 11)))
                pygame.draw.polygon(icon, color, ((6, 4), (9, 7), (6, 11)))
                pygame.draw.polygon(icon, color, ((10, 4), (13, 7), (10, 11)))
                if outline:
                    icon = vfx_utils.get_outline(icon)

            elif icon_type == Icon.HEART:
                icon = pygame.Surface((16, 16), pygame.SRCALPHA)
                coords = ((8, 12), (9, 11), (10, 10), (11, 9), (12, 8), (12, 5), (11, 4), (10, 3), (9, 4), (8, 5),
                          (7, 5), (6, 4), (5, 3), (4, 4), (3, 5), (3, 8), (4, 9), (5, 10), (6, 11), (7, 12))
                pygame.draw.polygon(icon, color, coords, 0)
                if outline:
                    pygame.draw.polygon(icon, (255, 255, 255) if vfx_utils.get_brightness(color) < 64 else (0, 0, 0),
                                        coords, 1)

            else:
                raise ValueError

            IconManager.cache[icon_type][(color, outline)] = icon

        return IconManager.cache[icon_type][(color, outline)].copy()
# </editor-fold>
