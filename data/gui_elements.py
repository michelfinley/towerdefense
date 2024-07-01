from typing import Tuple, Callable, List

import pygame

from data.constants import UI
from data.lib import sprites
from data.lib.vfx import VFXManager


class PreprocessedBoxImage:
    def __init__(self, raw_image: pygame.Surface):
        sheet = sprites.Spritesheet(raw_image)
        self.top = sheet.image_at((8, 0, 32, 8))
        self.right = sheet.image_at((40, 8, 8, 32))
        self.bot = sheet.image_at((8, 40, 32, 8))
        self.left = sheet.image_at((0, 8, 8, 32))

        self.borders = [self.top, self.right, self.bot, self.left]

        self.center = sheet.image_at((8, 8, 32, 32))

        self.top_left = sheet.image_at((0, 0, 8, 8))
        self.top_right = sheet.image_at((40, 0, 8, 8))
        self.bot_left = sheet.image_at((0, 40, 8, 8))
        self.bot_right = sheet.image_at((40, 40, 8, 8))

        self.corners = [self.top_left, self.top_right, self.bot_left, self.bot_right]


class BoxBase:
    def __init__(self, preprocessed: PreprocessedBoxImage,
                 *, pos: Tuple[float, float] = (0, 0), box_size: Tuple[float, float] = (0, 0)):
        self.__raw = preprocessed

        self.box = pygame.Surface((0, 0), pygame.SRCALPHA)

        self.pos = pos
        self.box_size = box_size
        return

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Tuple[float, float]):
        self._pos = value

    @property
    def box_size(self):
        return self._box_size

    @box_size.setter
    def box_size(self, value: Tuple[float, float]):
        self._box_size = (max(16., value[0]), max(16., value[1]))

        self.box = pygame.transform.scale(self.box, self.box_size)
        self.box.fill((0, 0, 0, 0))

        border_corner_width = self.__raw.top_left.get_width()
        border_corner_height = self.__raw.top_left.get_height()
        box_width = self.box_size[0] - 2 * border_corner_width
        box_height = self.box_size[1] - 2 * border_corner_height

        self.box.blit(pygame.transform.scale(self.__raw.top, (box_width, border_corner_height)),
                      (border_corner_width, 0))
        self.box.blit(pygame.transform.scale(self.__raw.right, (border_corner_width, box_height)),
                      (self.box_size[0] - border_corner_width, border_corner_height))
        self.box.blit(pygame.transform.scale(self.__raw.bot, (box_width, border_corner_height)),
                      (border_corner_width, self.box_size[1] - border_corner_height))
        self.box.blit(pygame.transform.scale(self.__raw.left, (border_corner_width, box_height)),
                      (0, border_corner_height))
        self.box.blit(pygame.transform.scale(self.__raw.center, (box_width, box_height)),
                      (border_corner_width, border_corner_height))

        self.box.blit(self.__raw.top_left, (0, 0))
        self.box.blit(self.__raw.top_right, (border_corner_width + box_width, 0))
        self.box.blit(self.__raw.bot_left, (0, border_corner_height + box_height))
        self.box.blit(self.__raw.bot_right, (border_corner_width + box_width, border_corner_height + box_height))

    def render(self, dest: pygame.Surface):
        dest.blit(self.box, self.pos)


class Box(BoxBase):
    image = None

    def __init__(self,
                 *, pos: Tuple[float, float] = (0, 0), box_size: Tuple[float, float] = (0, 0)):
        if not Box.image:
            Box.image = PreprocessedBoxImage(pygame.image.load(UI.BOX).convert_alpha())
        super().__init__(Box.image, pos=pos, box_size=box_size)


class Button:
    rect: pygame.Rect

    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager):
        self.image = image

        self.vfx_manager = vfx_manager

        self._pos = (0, 0)

        self.clicked = False
        self.__on_click_funcs: List[Callable[[], None]] = []

        self.toggled = False
        self.__on_toggle_funcs: List[Callable[[], None]] = []

        self.hovered = False
        self.__on_hover_funcs: List[Callable[[], None]] = []

        self.lock = False

        self.rect = pygame.Rect((0, 0, 0, 0))

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value):
        self._rect = value

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Tuple[float, float]):
        self._pos = value

    def on_toggle(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_toggle_funcs.append(func)
        return func

    def toggle(self):
        self.toggled = not self.toggled
        for func in self.__on_toggle_funcs:
            func()

    def on_click(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_click_funcs.append(func)
        return func

    def click(self):
        self.clicked = not self.clicked
        for func in self.__on_click_funcs:
            func()

    def on_hover(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_hover_funcs.append(func)
        return func

    def update(self, click: bool, mouse_pos: Tuple[int, int] = None):
        if mouse_pos is None:
            mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(*mouse_pos) and not self.lock:
            if not self.hovered:
                for func in self.__on_hover_funcs:
                    func()
                self.hovered = True
            if click:
                self.clicked = True
                self.toggle()
                for func in self.__on_click_funcs:
                    func()
            else:
                self.clicked = False
        else:
            self.clicked = False
            self.hovered = False

        self.vfx_manager.transform_object(self, self.rect.topleft, self.rect.size)

    def render(self, dest: pygame.Surface):
        self.vfx_manager.render(self, dest)
        dest.blit(self.image, self.pos)
        return


class ButtonImage(Button):
    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager):
        super().__init__(image, vfx_manager)

    @Button.pos.setter
    def pos(self, value: Tuple[float, float]):
        self._pos = value
        self.rect = self.image.get_rect(topleft=self.pos)


class ButtonBox(Box, Button):
    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager):
        Button.__init__(self, image, vfx_manager)
        Box.__init__(self)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Tuple[float, float]):
        self._pos = value
        try:
            self.rect = self.box.get_rect(topleft=self.pos)
            self.box.blit(self.image, (self.rect.width / 2 - self.image.get_width() / 2,
                                       self.rect.height / 2 - self.image.get_height() / 2))
        except AttributeError:
            # Wenn Button.__init__ bei der Initialisierung dieser Klasse self.pos setzt,
            #  ist self.box noch nicht definiert
            pass
