import math
import random
from typing import List

import pygame

from config import Config
from data.lib import vfx
from data.constants import Color, FontManager, Font
from data.lib.vfx import WinCelebrationEffect
from data.scene_game import GameData


class WinCelebrationData:
    def __init__(self, screen: pygame.Surface, config: Config, game_data: GameData):
        self.config = config

        self.screen = screen

        self.game_data = game_data

        self.vfx_manager = vfx.VFXManager()
        self.vfx_manager.add_effect(self, WinCelebrationEffect())
        self.vfx_manager.transform_object(self, size=self.screen.get_size())

        self.click = False
        self.total_time = 0

        self.title_font = FontManager.get_font(Font.AZONIX, 64)
        self.title_text = self.title_font.render("YOU WIN", True, (255, 255, 255))

        self.quote_font = FontManager.get_font(Font.PIXEL, 32)
        self.quote_text = self.quote_font.render(f"\"{random.choice(self.config.WIN_CELEBRATION_QUOTES)}\"",
                                                 True, (127, 127, 127))

        self.desc_font = FontManager.get_font(Font.AZONIX, 24)
        self.desc_text = self.desc_font.render("Press any key to play again.", True, (192, 192, 192))

        self.desc_text_largest = (self.desc_text.get_width() * 1, self.desc_text.get_height() * 1)
        self.desc_text_smallest = (self.desc_text.get_width() * 0.95, self.desc_text.get_height() * 0.95)

        self.desc_text_hint_period_time = 1.5

        self.__surface = pygame.Surface((0, 0), pygame.SRCALPHA)

    def handle_events(self, events: List[pygame.event.Event]):
        self.click = False

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button not in (4, 5):
                self.click = True
            elif event.type == pygame.VIDEORESIZE:
                self.vfx_manager.transform_object(self, size=self.screen.get_size())

    def update(self, timedelta: float):
        self.vfx_manager.update(timedelta)
        self.total_time += timedelta
        if self.total_time > self.desc_text_hint_period_time:
            self.total_time -= self.desc_text_hint_period_time
        return

    def render(self, surface: pygame.Surface):
        if surface.get_size() != self.__surface.get_size():
            self.__surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        self.__surface.fill(Color.BACKGROUND)

        self.vfx_manager.render(self, self.__surface)

        self.__surface.blit(self.title_text, (surface.get_width() / 2 - self.title_text.get_width() / 2,
                                              surface.get_height() * 0.2))

        self.__surface.blit(self.quote_text, (surface.get_width() / 2 - self.quote_text.get_width() / 2,
                                              surface.get_height() * 0.4))

        x = (self.total_time % self.desc_text_hint_period_time) / self.desc_text_hint_period_time

        # Pulsating effect on the descriptive text
        current_desc_text_size = (
            self.desc_text_smallest[0] +
            (0.5 + 0.5 * math.sin(2 * math.pi * (x - (1 / 4))))
            * (self.desc_text_largest[0] - self.desc_text_smallest[0]),

            self.desc_text_smallest[1] +
            (0.5 + 0.5 * math.sin(2 * math.pi * (x - (1 / 4))))
            * (self.desc_text_largest[1] - self.desc_text_smallest[1])
        )

        current_desc_text = pygame.transform.smoothscale(self.desc_text, current_desc_text_size)
        self.__surface.blit(current_desc_text, (surface.get_width() / 2 - current_desc_text.get_width() / 2,
                                                surface.get_height() * 0.75))

        surface.blit(self.__surface, (0, 0))
        return
