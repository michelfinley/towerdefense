from typing import Tuple, List

import pygame

from data.constants import Color


class Canvas:
    surface: pygame.Surface
    rect: pygame.Rect
    view_rect: pygame.Rect
    last_mouse_position: Tuple[int, int]
    static: List[Tuple[pygame.Surface, Tuple[int, int]]]

    def __init__(self, size: Tuple[int, int]):
        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.rect = self.surface.get_rect()

        self.view_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)

        self.last_mouse_position = pygame.mouse.get_pos()

        self.static = []

    def add_static(self, surface: pygame.Surface, position: Tuple[int, int] = None):
        self.static.append((surface, (position or (0, 0))))
        return

    def render(self, surface: pygame.Surface):
        self.surface.fill((0, 0, 0, 0))
        for item in self.static:
            self.surface.blit(item[0], item[1])

        surface.blit(self.surface, (0, 0))
        return

    def translate_vector(self, viewed_coordinate: Tuple[float, float]) -> Tuple[float, float]:
        return (
            (viewed_coordinate[0] - self.view_rect.x) / self.view_rect.w * self.rect.w,
            (viewed_coordinate[1] - self.view_rect.y) / self.view_rect.h * self.rect.h
        )


class Overlay:
    surface: pygame.Surface

    def __init__(self, canvas: Canvas):
        self.surface = pygame.Surface(canvas.rect.size, pygame.SRCALPHA)

    def render(self, surface: pygame.Surface):
        surface.blit(self.surface, (0, 0))
        self.surface.fill((0, 0, 0, 0))
        return


class Camera:
    canvas: Canvas
    overlay: Overlay
    initial_offset: pygame.math.Vector2
    scrolling: float
    default_scrolling: float
    scroll_speed: float
    scroll_max: float
    scroll_min: float
    moving: bool
    last_mouse_position: Tuple[int, int]

    def __init__(self, canvas_surface: pygame.Surface,
                 *, initial_offset: Tuple[int, int] = None):
        """
        Hiermit lässt sich eine Kamera erstellen, die Interaktionen mit der gegebenen Karte ermöglicht und
        bei jeder Aktualisierung Bilder aus der derzeitigen Kameraperspektive erstellt.
        :param canvas_surface: Oberfläche, welche aufgezeichnet werden soll
        """
        self.canvas = Canvas(canvas_surface.get_size())
        self.canvas.add_static(canvas_surface, (0, 0))

        self.overlay = Overlay(self.canvas)

        self.__screen_size = (0, 0)

        self.__captured_surface = pygame.Surface(self.canvas.rect.size, pygame.SRCALPHA)

        self.initial_offset = pygame.math.Vector2(initial_offset)

        self.scrolling = 0
        self.default_scrolling = 0

        self.scroll_speed = 0.05
        self.scroll_max = 2
        self.scroll_min = 0.5

        self.moving = False
        self.last_mouse_position = pygame.mouse.get_pos()

    def reset(self):
        screen_width, screen_height = self.__screen_size

        if self.initial_offset:
            screen_width -= abs(self.initial_offset.x) * 2
            screen_height -= abs(self.initial_offset.y) * 2

        self.scrolling = min((screen_width / self.canvas.rect.w),
                             (screen_height / self.canvas.rect.h))
        self.default_scrolling = self.scrolling

        self.canvas.view_rect.w = self.canvas.rect.w * self.scrolling
        self.canvas.view_rect.h = self.canvas.rect.h * self.scrolling

        self.canvas.view_rect.x = (screen_width - self.canvas.view_rect.w) / 2 + (self.initial_offset.x * 2
                                                                                  if self.initial_offset.x > 0 else 0)
        self.canvas.view_rect.y = (screen_height - self.canvas.view_rect.h) / 2 + (self.initial_offset.y * 2
                                                                                   if self.initial_offset.y > 0 else 0)
        return

    def move(self, event: pygame.event.Event):
        """
        Bewegt die Kamera je nach Interaktion des Benutzers mit dem Fenster.
        Sollte zu Beginn jedes Frames aufgerufen werden.
        :param event: PyGame-Event, für welches eine Bewegung geprüft werden soll
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.moving = True

            elif event.button in (4, 5):
                if event.button == 4 and self.scrolling < self.default_scrolling * self.scroll_max:
                    self.scrolling += self.scroll_speed
                elif event.button == 5 and self.scrolling > self.default_scrolling * self.scroll_min:
                    self.scrolling -= self.scroll_speed

                mouse_position = pygame.mouse.get_pos()
                mouse_x, mouse_y = self.canvas.translate_vector(mouse_position)

                self.canvas.view_rect.w = self.canvas.rect.w * self.scrolling
                self.canvas.view_rect.h = self.canvas.rect.h * self.scrolling

                mouse_x_new, mouse_y_new = self.canvas.translate_vector(mouse_position)

                self.canvas.view_rect.x += round((mouse_x_new - mouse_x) * self.scrolling)
                self.canvas.view_rect.y += round((mouse_y_new - mouse_y) * self.scrolling)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.moving = False
        return

    def update(self):
        """
        Aktualisiert den Kamerafokus
        """
        mouse_position = pygame.mouse.get_pos()
        if self.moving:
            self.canvas.view_rect.x += mouse_position[0] - self.last_mouse_position[0]
            self.canvas.view_rect.y += mouse_position[1] - self.last_mouse_position[1]
        self.last_mouse_position = mouse_position
        return

    def render(self, surface: pygame.Surface):
        """
        Aktualisiert das Bild der Kamera.
        Als neues Bild wird die momentane Oberfläche der aufzunehmenden Karte verwendet
        """
        if surface.get_size() != self.__screen_size:
            self.__screen_size = surface.get_size()
            self.reset()

        surface.fill(Color.BACKGROUND)

        self.canvas.render(self.__captured_surface)
        self.overlay.render(self.__captured_surface)

        surface.blit(pygame.transform.scale(self.__captured_surface, self.canvas.view_rect.size),
                     (self.canvas.view_rect.x, self.canvas.view_rect.y))

        self.__captured_surface.fill(Color.BACKGROUND)
        return
