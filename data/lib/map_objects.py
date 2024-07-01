from typing import Dict, Tuple, Any

import pygame

from data.constants import MapLayer, Color


class MapSurfaceLayer:
    def __init__(self, surface_size: Tuple[int, int], layer: int):
        self.surface = pygame.Surface(surface_size, pygame.SRCALPHA)
        self.layer = layer

    def render(self, surface: pygame.Surface):
        surface.blit(self.surface, (0, 0))
        self.surface.fill((0, 0, 0, 0))


class MapSurface:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface

        self.__blit_list = {}

        self.surfaces: Dict[MapLayer, MapSurfaceLayer] = {}
        for element in MapLayer:
            self.surfaces[element] = MapSurfaceLayer(self.surface.get_size(), element.value)
            self.__blit_list[element.value] = self.surfaces[element]
        self.__blit_list = dict(sorted(self.__blit_list.items())).values()

    def blit(self, layer: MapLayer, source: pygame.Surface, dest: Any):
        self.surfaces[layer].surface.blit(source, dest)
        return

    def get_surface(self, layer: MapLayer):
        return self.surfaces[layer].surface

    def render(self, surface: pygame.Surface = None):
        self.surface.fill(Color.BACKGROUND)
        for surf in self.__blit_list:
            surf.render(self.surface)
        if surface:
            surface.blit(self.surface, (0, 0))
        return

    def get_width(self):
        return self.surface.get_width()

    def get_height(self):
        return self.surface.get_height()

    def get_size(self):
        return self.surface.get_size()
