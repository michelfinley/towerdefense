import sys

import pygame

from config import Config
from data.constants import Icon, IconManager
from data.scenes import SceneManager, IntroScene


class Game:
    config: Config
    screen: pygame.Surface
    clock: pygame.time.Clock
    scene_manager: SceneManager

    def __init__(self):
        """
        Objekt, welches alle notwendigen Funktionen für das letztendliche Spiel beinhaltet
        """
        self.config = Config()

        pygame.init()
        self.screen = pygame.display.set_mode(Config.INITIAL_SCREEN_SIZE, pygame.SRCALPHA | pygame.RESIZABLE)

        IconManager.pre_load()

        pygame.display.set_caption("towerdefense")

        pygame.display.set_icon(IconManager.get_icon(Icon.SETTINGS))

        self.clock = pygame.time.Clock()

        self.scene_manager = SceneManager(IntroScene(self.screen, self.config))

    def loop(self):
        """
        Der Loop des Spiels, welcher die aktuelle Szene aktualisiert und rendert
        """
        while True:
            timedelta = self.clock.tick(Config.FPS) / 1000

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.scene_manager.scene.handle_events(events)
            self.scene_manager.scene.update(timedelta)
            self.scene_manager.scene.render()

            pygame.display.update()
