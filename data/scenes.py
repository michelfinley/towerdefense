import abc
from typing import List

import pygame.event

from config import Config
from data.constants import Font, FontManager, Color
from data.scene_game import GameData
from data.scene_game_over import GameOverData
from data.scene_menu import MenuData
from data.scene_win_celebration import WinCelebrationData


class Scene(abc.ABC):
    def __init__(self, screen: pygame.Surface, config: Config):
        self.manager: SceneManager | None = None
        self.screen = screen
        self.config = config

    @abc.abstractmethod
    def handle_events(self, events: List[pygame.event.Event]):
        pass

    @abc.abstractmethod
    def update(self, timedelta: float):
        pass

    @abc.abstractmethod
    def render(self):
        pass


class SceneManager(object):
    def __init__(self, default_scene: Scene):
        self.default_scene = default_scene
        self.scene = None
        self.change_scene(self.default_scene)

    def change_scene(self, scene: Scene):
        self.scene = scene
        self.scene.manager = self
        return


class IntroScene(Scene):
    def __init__(self, screen: pygame.Surface, config: Config):
        super().__init__(screen, config)

        self.rect = self.screen.get_rect()

        self.intro_animation_length = 3
        self.ctime = 0

        self.title_font = FontManager.get_font(Font.AZONIX, 64)
        title_text = self.title_font.render("towerdefense", True, (255, 255, 255))

        self.desc_font = FontManager.get_font(Font.AZONIX, 12)
        desc_text = self.desc_font.render("a simple towerdefense game using pygame", True, (200, 200, 200))

        self.intro_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.intro_image.blit(title_text, (self.rect.w / 2 - title_text.get_width() / 2,
                                           self.rect.h / 2 - title_text.get_height() / 2))
        self.intro_image.blit(desc_text, (self.rect.w / 2 - desc_text.get_width() / 2,
                                          self.rect.h * 0.95 - desc_text.get_height() / 2))

    def update(self, timedelta: float):
        self.ctime += timedelta
        if self.config.SKIP_INTRO or self.ctime >= self.intro_animation_length:
            self.manager.change_scene(MenuScene(self.screen, self.config))
        return

    def render(self):
        self.screen.fill(Color.BACKGROUND)

        # Fades the intro image out over the second half of the intro animation
        # For the last sixth of the intro animation the screen will be blank
        self.intro_image.set_alpha(255 - int(
            ((self.ctime - self.intro_animation_length / 2) > 0) *
            (self.ctime - self.intro_animation_length / 2) / (self.intro_animation_length / 2) * 255 * 1.5
        ))

        self.screen.blit(self.intro_image, (0, 0))
        return

    def handle_events(self, events: List[pygame.event.Event]):
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.rect = self.screen.get_rect()

                title_text = self.title_font.render("towerdefense", True, (255, 255, 255))
                desc_text = self.desc_font.render("a simple towerdefense game using pygame", True, (200, 200, 200))

                self.intro_image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
                self.intro_image.blit(title_text, (self.rect.w / 2 - title_text.get_width() / 2,
                                                   self.rect.h / 2 - title_text.get_height() / 2))
                self.intro_image.blit(desc_text, (self.rect.w / 2 - desc_text.get_width() / 2,
                                                  self.rect.h * 0.95 - desc_text.get_height() / 2))


class MenuScene(Scene):
    def __init__(self, screen: pygame.Surface, config: Config):
        super().__init__(screen, config)

        self.menu_data = MenuData(self.screen, self.config)

    def update(self, timedelta: float):
        self.menu_data.update(timedelta)
        return

    def render(self):
        self.menu_data.render(self.screen)
        return

    def handle_events(self, events: List[pygame.event.Event]):
        for event in events:
            if event.type == pygame.KEYUP or event.type == pygame.MOUSEBUTTONUP:
                self.manager.change_scene(GameScene(self.screen, self.config))
        self.menu_data.handle_events(events)
        return


class GameScene(Scene):
    def __init__(self, screen: pygame.Surface, config: Config):
        super().__init__(screen, config)

        self.game_data = GameData(self.screen, self.config)

        self.click = False

    def update(self, timedelta: float):
        self.game_data.update(timedelta)
        if self.game_data.quit:
            self.manager.change_scene(MenuScene(self.screen, self.config))
        elif self.game_data.game_won:
            self.manager.change_scene(WinCelebrationScene(self.screen, self.config, self.game_data))
        elif self.game_data.lives <= 0:
            self.manager.change_scene(GameOverScene(self.screen, self.config))
        return

    def render(self):
        self.game_data.render(self.screen)
        return

    def handle_events(self, events: List[pygame.event.Event]):
        self.game_data.handle_events(events)
        return


class GameOverScene(Scene):
    def __init__(self, screen: pygame.Surface, config: Config):
        super().__init__(screen, config)

        self.game_over_data = GameOverData(self.screen, self.config)

    def update(self, timedelta: float):
        self.game_over_data.update(timedelta)
        return

    def render(self):
        self.game_over_data.render(self.screen)
        return

    def handle_events(self, events: List[pygame.event.Event]):
        for event in events:
            if event.type == pygame.KEYUP or event.type == pygame.MOUSEBUTTONUP:
                self.manager.change_scene(GameScene(self.screen, self.config))
        self.game_over_data.handle_events(events)
        return


class WinCelebrationScene(Scene):
    def __init__(self, screen: pygame.Surface, config: Config, game_data: GameData):
        super().__init__(screen, config)

        self.win_celebration_data = WinCelebrationData(self.screen, self.config, game_data)

    def update(self, timedelta: float):
        self.win_celebration_data.update(timedelta)
        return

    def render(self):
        self.win_celebration_data.render(self.screen)
        return

    def handle_events(self, events: List[pygame.event.Event]):
        for event in events:
            if event.type == pygame.KEYUP or event.type == pygame.MOUSEBUTTONUP:
                self.manager.change_scene(GameScene(self.screen, self.config))
        self.win_celebration_data.handle_events(events)
        return
