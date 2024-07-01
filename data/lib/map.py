from operator import add
from typing import Tuple, List

import pygame
import pytmx

from data import constants
from data.constants import MapLayer
from data.lib.map_objects import MapSurface
from data.lib.vfx import VFXManager, InGameBackgroundEffect


class Map:
    adjacent_tile_coordinates = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    def __init__(self, path_to_tilemap: str, vfx_manager: VFXManager):
        """
        Hiermit lassen sich Karten erstellen, die eine Tilemap darstellen und
        ein pygame.Surface Objekt zur Verfügung stellen
        :param path_to_tilemap: Dateipfad der gewünschten Tilemap
        """

        self.vfx_manager = vfx_manager

        self.data = pytmx.load_pygame(path_to_tilemap)
        self.rect = (self.data.tilewidth * self.data.width, self.data.tileheight * self.data.height)
        self.center = (self.rect[0] / 2, self.rect[1] / 2)
        self.map_surface = MapSurface(pygame.Surface(self.rect, pygame.SRCALPHA))

        self.tilemap_image = None
        self.background_vfx = InGameBackgroundEffect()
        self.vfx_manager.add_effect(self.background_vfx, self.background_vfx)

        self.construction_zones: List[pygame.Rect] = []
        self.spawnpoints: List[Tuple[int, int]] = []
        self.paths: List[List[Tuple[int, int]]] = []
        self.__tilemap_setup()

    def __render_tilemap(self):
        """
        Lädt alle Bilder aus den Tile-Schichten der Tilemap aus self.data und überträgt sie auf self.tilemap_image
        """
        surface = pygame.Surface(self.rect, pygame.SRCALPHA)
        if self.data.background_color:
            surface.fill(pygame.Color(self.data.background_color))

        for layer in self.data.visible_layers:

            if isinstance(layer, pytmx.TiledTileLayer):

                for x, y, image in layer.tiles():
                    surface_w_2 = surface.get_width() / 2
                    surface_h_2 = surface.get_height() / 2
                    if ((self.center[0] - surface_w_2 - self.data.tilewidth) <= (x * self.data.tilewidth) < (self.center[0] + surface_w_2)
                            and (self.center[1] - surface_h_2 - self.data.tileheight) <= (y * self.data.tileheight) < (self.center[1] + surface_h_2)):
                        final_x = (x * self.data.tilewidth) - (self.center[0] - surface_w_2)
                        final_y = (y * self.data.tileheight) - (self.center[1] - surface_h_2)
                        surface.blit(
                            pygame.transform.scale(image, (self.data.tilewidth, self.data.tileheight)),
                            (final_x, final_y)
                        )
        self.tilemap_image = surface

    def render(self):
        """
        Setzt die Oberfläche auf ihren Ursprungszustand zurück
        """
        self.vfx_manager.transform_object(self, (0, 0), self.map_surface.get_surface(MapLayer.Base).get_size())
        self.vfx_manager.transform_object(self.background_vfx, (0, 0),
                                          self.map_surface.get_surface(MapLayer.Base).get_size())

        self.map_surface.blit(MapLayer.Base, self.tilemap_image, (0, 0))
        self.vfx_manager.render(self.background_vfx, self.map_surface.get_surface(MapLayer.Base))
        self.map_surface.render()
        self.vfx_manager.render(self, self.map_surface.get_surface(MapLayer.VFX))

    def __calculate_paths_from_spawn(self, spawn_coords: Tuple[int, int], path: List[Tuple[int, int]] = None):
        """
        Berechnet alle möglichen Wege auf der Karte für die gegebenen Startkoordinaten und fügt sie self.paths hinzu
        :param spawn_coords: Startkoordinaten (Erscheinungspunkt der Gegner)
        :param path: None
        """
        if path is None:
            path = [spawn_coords]

        for i in Map.adjacent_tile_coordinates:
            coordinate = tuple(map(add, path[-1], i))

            if -1 in coordinate or coordinate[1] == 9 or coordinate in path:
                continue

            # noinspection PyTypeChecker
            new_path = path + [coordinate]

            tile_properties = self.data.get_tile_properties(*coordinate, 0)
            if tile_properties and "enemy_spawn" in tile_properties and tile_properties["enemy_spawn"]:
                self.paths.append(new_path)
                continue

            if tile_properties and "enemy_path" in tile_properties and tile_properties["enemy_path"]:
                self.__calculate_paths_from_spawn(spawn_coords, new_path)

    def __tilemap_setup(self):
        """
        Liest alle Erscheinungspunkte für Gegner und alle bebaubaren Zonen auf der Karte ein und berechnet
        alle Pfade zwischen den Erscheinungspunkten. Sollte beim Laden der Karte einmalig aufgerufen werden
        """
        spawnpoints: List[Tuple[int, int]] = []
        construction_zones: List[Tuple[float, float]] = []

        for x in range(self.data.width):
            for y in range(self.data.height):
                tile_properties = self.data.get_tile_properties(x, y, 0)
                if (tile_properties
                        and constants.Map.SPAWN in tile_properties
                        and bool(tile_properties[constants.Map.SPAWN])):
                    spawnpoints.append((x, y))
                if (tile_properties
                        and constants.Map.CONSTRUCTION_ZONE in tile_properties
                        and bool(tile_properties[constants.Map.CONSTRUCTION_ZONE])):
                    construction_zones.append((x + 0.45, y + 0.45))

        for spawnpoint in spawnpoints:
            self.__calculate_paths_from_spawn(spawnpoint)

        # Jetzt werden alle vorher ermittelten Koordinaten auf der Tilemap mit der Größe der einzelnen Tiles
        # multipliziert, damit später direkt die Position der Zielpunkte auf dem Spielfenster ausgelesen werden kann
        for i in spawnpoints:
            self.spawnpoints.append((i[0] * self.data.tilewidth, i[1] * self.data.tileheight))

        for i in construction_zones:
            self.construction_zones.append(pygame.Rect(i[0] * self.data.tilewidth, i[1] * self.data.tileheight,
                                                       self.data.tilewidth * 0.1, self.data.tileheight * 0.1))

        for path in range(len(self.paths)):
            for p, i in enumerate(self.paths[path]):
                self.paths[path][p] = (i[0] * self.data.tilewidth, i[1] * self.data.tileheight)
            self.paths[path].append((
                self.paths[path][-1][0] + (self.paths[path][-1][0] - self.paths[path][-2][0]),
                self.paths[path][-1][1] + (self.paths[path][-1][1] - self.paths[path][-2][1])
            ))
        self.__render_tilemap()
        return
