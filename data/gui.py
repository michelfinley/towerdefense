from typing import Tuple, List

import pygame
import pygame.gfxdraw

from data.constants import UI, Sprite, Font, Direction, TurretType, Icon, IconManager, FontManager, Color
from data.lib import sprites
from data import gui_elements
from data.lib.vfx import ButtonHighlightEffect, GradientLineEffect, GradientLineEffectData, VFXManager, \
    TextParticleEffect, TextParticleEffectData, OverlayFadeOutEffect, OverlayFadeOutEffectData, InGameBlendInEffect, \
    InGameBlendInEffectData
from data.lib.vfx_utils import get_outline


class ShopItemButton(gui_elements.Box, gui_elements.Button):
    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager):
        gui_elements.Button.__init__(self, image, vfx_manager)
        gui_elements.Box.__init__(self)

        self.cost_image = sprites.Spritesheet(pygame.image.load(UI.ICONS).convert_alpha()).image_at((16, 0, 16, 16))
        self.font = FontManager.get_font(Font.PIXEL, 10)
        self.text = ""
        self.affordable = False
        self.__affordable_animation_played = self.affordable

        self.box_size = (self.image.get_width() * 1.5,
                         self.image.get_height() * 1.5 + self.__text_rendered.get_height())

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.__text_rendered = self.font.render(f"{self.text}", False, (255, 180, 100))
        return

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: Tuple[float, float]):
        self._pos = value
        try:
            self.rect = self.box.get_rect(topleft=self.pos)
        except AttributeError:
            # Wenn Button.__init__ bei der Initialisierung dieser Klasse self.pos setzt,
            #  ist self.box noch nicht definiert
            # → siehe data.gui_elements.ButtonBox
            pass

    def update(self, click: bool, mouse_pos: Tuple[int, int] = None):
        super().update(click, mouse_pos)

        # redrawing self.box
        self.box_size = self.box_size

        surf = pygame.Surface((self.rect.w, self.rect.h))
        if self.affordable:
            surf.fill((63, 255, 63))
        else:
            surf.fill((255, 63, 63))
        self.box.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.box.blit(self.image, (self.image.get_width() * 1.5 / 2 - self.image.get_width() / 2,
                                   self.image.get_height() * 1.5 / 2 - self.image.get_height() / 2))

        self.box.blit(self.cost_image, (self.image.get_width() * 1.5 / 2 - self.__text_rendered.get_width() / 2 -
                                        self.cost_image.get_width() / 2,
                                        self.image.get_height() * 1.5 - self.cost_image.get_height() / 2 + 2))

        self.box.blit(self.__text_rendered, (self.image.get_width() * 1.5 / 2 - self.__text_rendered.get_width() / 2 +
                                             self.cost_image.get_width() / 2,
                                             self.image.get_height() * 1.5 - self.__text_rendered.get_height() / 2 + 1))

        if self.affordable and not self.__affordable_animation_played:
            self.vfx_manager.add_effect(self, GradientLineEffect(GradientLineEffectData(
                path=[(4 / 48, -1 / 48), (44 / 48, -1 / 48),
                      (1, 4 / 48), (1, 44 / 48),
                      (44 / 48, 1), (4 / 48, 1),
                      (-1 / 48, 44 / 48), (-1 / 48, 4 / 48),
                      (4 / 48, -1 / 48)],
                line_length=1, loop_duration=1.5, loop_count=1)))

        self.__affordable_animation_played = self.affordable

    def render(self, dest: pygame.Surface):
        self.vfx_manager.render(self, dest)
        if self.hovered:
            dest.blit(get_outline(self.box, (255, 255, 64), True),
                      (self.pos[0] - 1, self.pos[1] - 1))
        else:
            dest.blit(self.box, self.pos)
        return


class Shop(gui_elements.Box):
    def __init__(self, game_data):
        super().__init__()
        self.game_data = game_data

        self.hidden = False

        blue_turret_sprite = sprites.Spritesheet(Sprite.BLUE_TURRET).image_at((32, 0, 32, 32))
        self.__blue_turret_button = ShopItemButton(blue_turret_sprite, self.game_data.vfx_manager)
        self.__blue_turret_button.text = str(self.game_data.turret_info[TurretType.BLUE].cost)

        @self.__blue_turret_button.on_click
        def _():
            self.game_data.turret_preview = TurretType.BLUE

        red_turret_sprite = sprites.Spritesheet(Sprite.RED_TURRET).image_at((32, 0, 32, 32))
        self.__red_turret_button = ShopItemButton(red_turret_sprite, self.game_data.vfx_manager)
        self.__red_turret_button.text = str(self.game_data.turret_info[TurretType.RED].cost)

        @self.__red_turret_button.on_click
        def _():
            self.game_data.turret_preview = TurretType.RED

    def update(self, click: bool, any_hovered: bool, any_clicked: bool, mouse_pos: Tuple[int, int] = None):
        if self.game_data.coins >= self.game_data.turret_info[TurretType.BLUE].cost:
            self.__blue_turret_button.affordable = True
        else:
            self.__blue_turret_button.affordable = False

        if self.game_data.coins >= self.game_data.turret_info[TurretType.RED].cost:
            self.__red_turret_button.affordable = True
        else:
            self.__red_turret_button.affordable = False

        self.__blue_turret_button.update(click, mouse_pos)
        self.__red_turret_button.update(click, mouse_pos)
        any_hovered = any((any_hovered, self.__blue_turret_button.hovered, self.__red_turret_button.hovered))
        any_clicked = any((any_clicked, self.__blue_turret_button.clicked, self.__red_turret_button.clicked))
        return any_hovered, any_clicked

    def render(self, dest: pygame.Surface):
        dest.blit(self.box, self.pos)

        self.__blue_turret_button.render(dest)
        self.__red_turret_button.render(dest)
        return

    def resize(self, box_size: Tuple[int, int], pos: Tuple[int, int]):
        self.box_size = box_size
        self.pos = pos
        self.__blue_turret_button.pos = (self.pos[0] + 8, self.pos[1] + 8)
        self.__red_turret_button.pos = (self.pos[0] + 8, self.pos[1] + 80)


class SpeedBarButton(gui_elements.ButtonImage):
    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager,
                 index: int, speed_toggle_images: list[pygame.Surface]):
        super().__init__(image, vfx_manager)

        self.index = index
        self.speed_toggle_images = speed_toggle_images


class SpeedBar(gui_elements.Box):
    def __init__(self, game_data):
        super().__init__()
        self.hidden = False

        self.game_data = game_data

        self.__speed_button_list: List[SpeedBarButton] = []

        self.__pause_button = self.__init_speed_button(Icon.PAUSE, -1)
        self.__play_button = self.__init_speed_button(Icon.PLAY, 0)
        self.__double_speed_button = self.__init_speed_button(Icon.DOUBLE_SPEED, 1)
        self.__triple_speed_button = self.__init_speed_button(Icon.TRIPLE_SPEED, 2)

        self.__speed_button_list.append(self.__pause_button)
        self.__speed_button_list.append(self.__play_button)
        self.__speed_button_list.append(self.__double_speed_button)
        self.__speed_button_list.append(self.__triple_speed_button)

        self.__active_speed_button = self.__pause_button

    def __init_speed_button(self, icon_type: Icon, index: int) -> SpeedBarButton:
        speed_toggle_images = [IconManager.get_icon(icon_type, (128, 128, 128)),
                               IconManager.get_icon(icon_type, (255, 255, 255))]
        button = SpeedBarButton(speed_toggle_images[0], self.game_data.vfx_manager, index, speed_toggle_images)

        @button.on_toggle
        def _():
            if button.toggled:
                for i in self.__speed_button_list:
                    if i != button:
                        i.toggled = False

                        i.image = i.speed_toggle_images[0]
                if button.index == -1:
                    self.game_data.pause = True
                else:
                    self.game_data.game_speed_index = button.index
                    self.game_data.pause = False
                self.__active_speed_button = button
            else:
                button.toggled = True
            if button.toggled:
                scale = self.game_data.gui.surface.get_height() * 0.5
                self.game_data.vfx_manager.add_effect(self.game_data.gui, OverlayFadeOutEffect(OverlayFadeOutEffectData(
                    duration=(-1 if button.index == -1 else 0.5),
                    overlay=pygame.transform.scale(button.speed_toggle_images[1], (scale, scale)),
                    start_alpha=64,
                )), unique=True)
            button.image = button.speed_toggle_images[button.toggled]
        return button

    def update(self, click: bool, any_hovered: bool, any_clicked: bool, mouse_pos: Tuple[int, int] = None):
        if not self.game_data.pause and self.game_data.game_speed_index != self.__active_speed_button.index:
            for i in self.__speed_button_list:
                if i.index == self.game_data.game_speed_index:
                    i.toggle()
        elif self.game_data.pause and self.__active_speed_button.index != -1:
            self.__pause_button.toggle()

        self.__pause_button.update(click, mouse_pos)
        self.__play_button.update(click, mouse_pos)
        self.__double_speed_button.update(click, mouse_pos)
        self.__triple_speed_button.update(click, mouse_pos)

        any_hovered = any((any_hovered, self.__pause_button.hovered, self.__play_button.hovered,
                           self.__double_speed_button.hovered, self.__triple_speed_button.hovered))
        any_clicked = any((any_clicked, self.__pause_button.clicked, self.__play_button.clicked,
                           self.__double_speed_button.clicked, self.__triple_speed_button.clicked))
        return any_hovered, any_clicked

    def render(self, dest: pygame.Surface):
        dest.blit(self.box, self.pos)

        self.__pause_button.render(dest)
        self.__play_button.render(dest)
        self.__double_speed_button.render(dest)
        self.__triple_speed_button.render(dest)
        return

    def resize(self, pos: Tuple[int, int]):
        pos = (pos[0] - 72, pos[1])
        self.box_size = (72, 24)
        self.pos = pos
        self.__pause_button.pos = (pos[0] + 4, pos[1] + 4)
        self.__play_button.pos = (pos[0] + 20, pos[1] + 4)
        self.__double_speed_button.pos = (pos[0] + 36, pos[1] + 4)
        self.__triple_speed_button.pos = (pos[0] + 52, pos[1] + 4)


class InfoBar(gui_elements.Box):
    def __init__(self, image: pygame.Surface, vfx_manager: VFXManager,
                 *, expansion_direction: Direction = Direction.RIGHT, font: pygame.font.Font | None = None,
                 default_text: str | None = None, text_color: Tuple[int, int, int] | None = None):
        super().__init__()
        self.offset_pos = self.pos

        self.vfx_manager = vfx_manager

        self.image = image
        self.font = font or FontManager.get_font(Font.PIXEL, 10)
        self.text_color = text_color or (255, 255, 255)

        self.direction = expansion_direction

        self.default_text = default_text or ""
        self.text = self.default_text

        self.__last_text_len = len(self.text)

        self.__default_text_surf = self.font.render(self.text, False, self.text_color)
        self.__text_surf = self.__default_text_surf

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self.__text_surf = self.font.render(self.text, False, self.text_color)

    def resize(self, pos: Tuple[int, int]):
        self.box_size = (
            4 + self.image.get_width() + 8 + self.__text_surf.get_width() + 4,
            max(self.image.get_height(), self.__text_surf.get_height()) + 8
        )
        self.pos = pos
        if self.direction == Direction.RIGHT:
            self.offset_pos = (self.pos[0], self.pos[1])
        elif self.direction == Direction.LEFT:
            self.offset_pos = (self.pos[0] - self.box.get_width(), self.pos[1])
        self.box.blit(self.image, (4, 4))

    def update(self):
        if len(self.text) != self.__last_text_len:
            self.resize(self.pos)
        self.__last_text_len = len(self.text)

        self.vfx_manager.transform_object(self, self.offset_pos, self.box_size)

    def render(self, dest: pygame.Surface):
        surf = pygame.Surface(dest.get_size(), pygame.SRCALPHA)

        real_pos = self.pos
        self.pos = self.offset_pos
        super().render(surf)
        self.pos = real_pos

        surf.blit(self.__text_surf, (self.offset_pos[0] + self.box.get_width() - self.__text_surf.get_width() - 8,
                                     self.offset_pos[1] + 12 - self.__text_surf.get_height() / 2))
        self.vfx_manager.render(self, surf)

        dest.blit(surf, (0, 0))


class BalanceInfoBar(InfoBar):
    image = None

    def __init__(self, game_data, vfx_manager: VFXManager,
                 *, expansion_direction: Direction = Direction.RIGHT, font: pygame.font.Font | None = None):
        if BalanceInfoBar.image is None:
            BalanceInfoBar.image = sprites.Spritesheet(
                pygame.image.load(UI.ICONS).convert_alpha()
            ).image_at((16, 0, 16, 16))

        super().__init__(BalanceInfoBar.image, vfx_manager, expansion_direction=expansion_direction, font=font,
                         default_text="None", text_color=(255, 180, 100))

        self.game_data = game_data

        self.__last_coins = self.game_data.coins

    def update(self):
        self.text = str(self.game_data.coins)
        super().update()


class LPInfoBar(InfoBar):
    image = None

    def __init__(self, game_data, vfx_manager: VFXManager,
                 *, expansion_direction: Direction = Direction.RIGHT, font: pygame.font.Font | None = None):
        if LPInfoBar.image is None:
            LPInfoBar.image = IconManager.get_icon(Icon.HEART, (255, 0, 0))
        super().__init__(LPInfoBar.image, vfx_manager, expansion_direction=expansion_direction, font=font,
                         default_text="None", text_color=(223, 0, 0))

        self.game_data = game_data

        self.__last_lp = self.game_data.lives

    def update(self):
        if self.game_data.lives != self.__last_lp:
            self.vfx_manager.add_effect(self, TextParticleEffect(TextParticleEffectData(
                font=FontManager.get_font(Font.PIXEL, 10),
                text=("+" if self.game_data.lives - self.__last_lp > 0 else "")
                + str(self.game_data.lives - self.__last_lp),
                initial_color=(0, 255, 0) if self.game_data.lives - self.__last_lp > 0 else (255, 0, 0),
                final_color=(0, 255, 0) if self.game_data.lives - self.__last_lp > 0 else (255, 0, 0),
                position=(self.box_size[0] - 8,
                          self.box_size[1] / 6),
                direction_of_emission=(110, 160),
                initial_speed=45,
                lifetime=0.5,
            )))
            self.__last_lp = self.game_data.lives
        self.text = str(round(self.game_data.lives))
        super().update()

    def render(self, dest: pygame.Surface):
        super().render(dest)


class WaveInfoBar(InfoBar):
    def __init__(self, game_data, vfx_manager: VFXManager,
                 *, expansion_direction: Direction = Direction.RIGHT, font: pygame.font.Font | None = None):
        super().__init__(sprites.Spritesheet(pygame.image.load(UI.ICONS).convert_alpha()).image_at((32, 0, 16, 16)),
                         vfx_manager,
                         expansion_direction=expansion_direction, font=font,
                         default_text="None", text_color=(255, 0, 0))

        self.game_data = game_data

        self.__last_wave = 0

    def update(self):
        if self.__last_wave != self.game_data.wave:
            surf = pygame.Surface(self.game_data.gui.surface.get_size(), pygame.SRCALPHA)
            text = FontManager.get_font(Font.AZONIX, 48).render(
                f"Wave {self.game_data.wave}", True, (200, 0, 0)
            )
            text = pygame.transform.scale(text, (
                (surf.get_height() * 0.1 / text.get_height()) * text.get_width(),
                (surf.get_height() * 0.1)
            ))
            surf.blit(text, ((surf.get_width() - text.get_width()) / 2, text.get_height()))
            surf = get_outline(surf, (95, 0, 0))
            self.game_data.vfx_manager.add_effect(self.game_data.gui, OverlayFadeOutEffect(OverlayFadeOutEffectData(
                duration=2,
                overlay=surf,
                start_alpha=255,
                delay=1,
            )), unique=True)
            self.__last_wave = self.game_data.wave
        self.text = ("0" if self.__last_wave < 10 else "") + str(self.__last_wave)
        super().update()


class NextWaveButton(gui_elements.ButtonBox):
    def __init__(self, game_data):
        image = pygame.Surface((0, 0))
        super().__init__(image, game_data.vfx_manager)
        self.warning_image = sprites.Spritesheet(pygame.image.load(UI.ICONS).convert_alpha()).image_at((0, 0, 16, 16))
        self.font = FontManager.get_font(Font.PIXEL, 12)
        self.text = self.font.render(f"NEXT WAVE", False, (200, 100, 0))
        self.game_data = game_data

        self.__position_change = (0, 0)
        self.__max_position_change = (0, 24)
        self.__animation_duration = 0.67

        self.game_data.vfx_manager.add_effect(self, ButtonHighlightEffect())

    def update(self, click: bool, mouse_pos: Tuple[int, int] = None):
        super().update(click, mouse_pos)

        timedelta = self.game_data.real_timedelta

        self.game_data.vfx_manager.transform_object(self, self.pos, self.box_size)

        if self.game_data.wave_active or self.game_data.start_next_wave:
            if not self.lock:
                self.game_data.vfx_manager.clear_effects(self)
                self.lock = True
            if self.__position_change != self.__max_position_change:
                self.__position_change = (
                    min(self.__max_position_change[0], self.__position_change[0] + (
                            self.__max_position_change[0] * (timedelta / self.__animation_duration)
                    )),
                    min(self.__max_position_change[1], self.__position_change[1] + (
                            self.__max_position_change[1] * (timedelta / self.__animation_duration)
                    ))
                )
        else:
            if self.lock:
                self.game_data.vfx_manager.add_effect(self, ButtonHighlightEffect())
                self.lock = False
            if self.__position_change != (0, 0):
                self.__position_change = (
                    max(0., self.__position_change[0] - (
                            self.__max_position_change[0] * (timedelta / self.__animation_duration)
                    )),
                    max(0., self.__position_change[1] - (
                            self.__max_position_change[1] * (timedelta / self.__animation_duration)
                    ))
                )

    def render(self, dest: pygame.Surface):
        self.game_data.vfx_manager.render(self, dest)

        if self.hovered:
            dest.blit(get_outline(self.box, (255, 255, 64), True),
                      (self.pos[0] + self.__position_change[0] - 1, self.pos[1] + self.__position_change[1] - 1))
        else:
            dest.blit(self.box, (self.pos[0] + self.__position_change[0], self.pos[1] + self.__position_change[1]))
        return

    def resize(self, pos: Tuple[int, int]):
        self.box_size = (48 + self.text.get_width(), 24)
        self.pos = pos
        self.box.blit(self.warning_image, (4, 4))
        self.box.blit(self.text, (24, 12 - (self.text.get_height() / 2)))
        self.box.blit(self.warning_image, (self.rect.w - 20, 4))


class SettingsMenu(gui_elements.Box):
    def __init__(self, game_data):
        super().__init__()

        self.game_data = game_data

        quit_button_surf = pygame.Surface((140, 30), pygame.SRCALPHA)
        pygame.draw.rect(quit_button_surf, (32, 34, 54), quit_button_surf.get_rect(), 0, 5)
        pygame.draw.rect(quit_button_surf, (255, 63, 63), quit_button_surf.get_rect(), 2, 5)
        quit_text = FontManager.get_font(Font.PIXEL, 20).render("QUIT GAME", True, (255, 63, 63))
        quit_button_surf.blit(quit_text, (quit_button_surf.get_width() / 2 - quit_text.get_width() / 2,
                                          quit_button_surf.get_height() / 2 - quit_text.get_height() / 2 - 2))

        self.quit_button = gui_elements.ButtonImage(quit_button_surf, self.game_data.vfx_manager)

        @self.quit_button.on_click
        def _():
            self.game_data.quit = True

    def update(self, click: bool, mouse_pos: Tuple[int, int]):
        self.quit_button.update(click, mouse_pos)
        return self.quit_button.hovered, self.quit_button.clicked

    def render(self, dest: pygame.Surface):
        surf = pygame.Surface(self.box.get_size(), pygame.SRCALPHA)
        super().render(surf)
        dest.blit(surf, (dest.get_width() / 2 - surf.get_width() / 2,
                         dest.get_height() / 2 - surf.get_height() / 2))
        self.quit_button.pos = (dest.get_width() / 2 - self.quit_button.image.get_width() / 2,
                                dest.get_height() / 2 - self.quit_button.image.get_height() / 2)
        self.quit_button.render(dest)

    def resize(self):
        self.box_size = (140, 30)
        self.pos = (0, 0)


class GUI:
    def __init__(self, game_data):
        self.__gui_size_multiplier = 2

        self.rect = pygame.Rect((0, 0, 0, 0))

        self.surface = pygame.Surface((0, 0), pygame.SRCALPHA)

        self.game_data = game_data

        self.game_data.vfx_manager.add_effect(self, InGameBlendInEffect(InGameBlendInEffectData(color=Color.BACKGROUND,
                                                                                                duration=1)))

        self.shop = Shop(self.game_data)

        self.balance_info_bar = BalanceInfoBar(self.game_data, self.game_data.vfx_manager,
                                               expansion_direction=Direction.LEFT)

        self.speed_bar = SpeedBar(self.game_data)

        self.LP_info_bar = LPInfoBar(self.game_data, self.game_data.vfx_manager,
                                     expansion_direction=Direction.LEFT)

        self.wave_info_bar = WaveInfoBar(self.game_data, self.game_data.vfx_manager,
                                         expansion_direction=Direction.LEFT)

        self.next_wave_button = NextWaveButton(self.game_data)

        @self.next_wave_button.on_click
        def _():
            if not (self.game_data.wave_active or self.game_data.start_next_wave):
                self.game_data.start_next_wave = True

        self.settings_button = gui_elements.ButtonImage(IconManager.get_icon(Icon.SETTINGS), self.game_data.vfx_manager)

        self.settings_menu = SettingsMenu(self.game_data)

        self.display_settings_menu = False

        @self.settings_button.on_click
        def _():
            self.game_data.lock = not self.game_data.lock
            self.display_settings_menu = not self.display_settings_menu
            if self.display_settings_menu:
                self.settings_menu.resize()

    def translate_vector(self, vector: Tuple[int, int]) -> Tuple[int, int]:
        return vector[0] // self.__gui_size_multiplier, vector[1] // self.__gui_size_multiplier

    def update(self, event_mouseup: bool, mouse_position: Tuple[int, int], camera_moving: bool):
        mouse_position = self.translate_vector(mouse_position)
        any_hovered = False
        any_clicked = False
        if not self.display_settings_menu:
            any_hovered, any_clicked = self.shop.update(event_mouseup, any_hovered, any_clicked, mouse_position)
            any_hovered, any_clicked = self.speed_bar.update(event_mouseup, any_hovered, any_clicked, mouse_position)
            self.next_wave_button.update(event_mouseup, mouse_position)
            any_hovered, any_clicked = (any((any_hovered, self.next_wave_button.hovered)),
                                        any((any_clicked, self.next_wave_button.clicked)))
        else:
            any_hovered, any_clicked = self.settings_menu.update(event_mouseup, mouse_position)
        self.settings_button.update(event_mouseup, mouse_position)
        any_hovered, any_clicked = (any((any_hovered, self.settings_button.hovered)),
                                    any((any_clicked, self.settings_button.clicked)))
        if any_hovered or any_clicked:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        elif camera_moving:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEALL)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if any_clicked:
            self.game_data.unselect_defenses()
        self.balance_info_bar.update()
        self.LP_info_bar.update()
        self.wave_info_bar.update()

    def resize(self, size: Tuple[int, int]):
        self.rect = pygame.Rect((0, 0, size[0], size[1]))

        self.surface = pygame.transform.scale(self.surface, (int(self.rect.w / self.__gui_size_multiplier),
                                                             int(self.rect.h / self.__gui_size_multiplier)))

        self.shop.resize((64, self.surface.get_height()), (self.surface.get_width() - 64, 0))
        self.balance_info_bar.resize((self.surface.get_width() - 64, 24 - 1))
        self.speed_bar.resize((self.surface.get_width() - 64, 0))
        self.LP_info_bar.resize((self.surface.get_width() - 64, 0 + 48 - 2))
        self.wave_info_bar.resize((self.surface.get_width() - 64, self.surface.get_height() - 24))
        self.next_wave_button.resize(((self.surface.get_width() - 64) // 2 - 55, self.surface.get_height() - 24))
        self.settings_button.pos = (0, 0)
        if self.display_settings_menu:
            self.settings_menu.resize()

        self.game_data.vfx_manager.transform_object(self, (0, 0), self.surface.get_size())

    def render(self, surface: pygame.Surface):
        self.surface.fill((0, 0, 0, 0))
        self.shop.render(self.surface)
        self.balance_info_bar.render(self.surface)
        self.speed_bar.render(self.surface)
        self.LP_info_bar.render(self.surface)
        self.wave_info_bar.render(self.surface)
        self.next_wave_button.render(self.surface)
        if self.display_settings_menu:
            surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            surf.fill((0, 0, 0, 159))
            self.surface.blit(surf, (0, 0))
            self.settings_menu.render(self.surface)
        self.settings_button.render(self.surface)
        self.game_data.vfx_manager.render(self, self.surface)
        surface.blit(pygame.transform.scale(self.surface, self.rect.size), (0, 0))
