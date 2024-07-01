import json
from dataclasses import dataclass
from typing import List, Dict

import pygame

from config import Config
from data.lib.camera import Camera
from data.constants import TurretType, Resources, FontManager, Font
from data.entities import PreviewBlueTurret, PreviewRedTurret, DefaultEnemy
from data.gui import GUI
from data.lib.entity_objects import Enemy, DefenseEntity, PreviewTurret
from data.lib.map import Map
from data.lib.vfx import VFXManager, EnemyKillEffect, EnemyKillEffectData, TextParticleEffect, TextParticleEffectData


@dataclass
class TurretInfo:
    preview: PreviewTurret
    cost: int


class GameData:
    config: Config
    screen: pygame.Surface

    map: Map
    gui: GUI
    camera: Camera

    enemies: List[Enemy]
    defenses: List[DefenseEntity]
    pause: bool
    lock: bool
    turret_preview: TurretType | None
    turret_info: Dict[TurretType, TurretInfo]

    selected_turret: DefenseEntity | None

    game_speed_index: int

    real_timedelta: float
    real_ingame_time: float
    effective_timedelta: float
    effective_ingame_time: float

    def __init__(self, screen: pygame.Surface, config: Config):
        self.config = config

        self.screen = screen

        self.enemies: List[Enemy] = []
        self.defenses: List[DefenseEntity] = []
        self.pause = False
        self.lock = False

        self.click = False

        self.quit = False

        self.turret_preview = None
        self.turret_info = {
            TurretType.BLUE: TurretInfo(
                preview=PreviewBlueTurret(100, self.defenses, self.preview_turret_collision_checker),
                cost=50
            ),
            TurretType.RED: TurretInfo(
                preview=PreviewRedTurret(140, self.defenses, self.preview_turret_collision_checker),
                cost=150
            ),
        }

        self.selected_turret = None

        self.__game_speed_options = self.config.SPEED_OPTIONS
        self.game_speed_index = 0

        self.real_timedelta = 0
        self.real_ingame_time = 0
        self.effective_timedelta = 0
        self.effective_ingame_time = 0

        self.__surface = pygame.Surface((0, 0), pygame.SRCALPHA)

        self.coins = 50
        self.lives = 100

        self.start_next_wave = False
        self.wave = 0
        self.wave_time_passed = 0
        self.wave_active = False

        with open("data/waves.json") as file:
            self.wave_info = json.load(file)

        self.wave_control_info = {}

        self.game_won = False

        self.vfx_manager = VFXManager()

        self.map = Map(Resources.MAP, self.vfx_manager)
        self.gui = GUI(self)
        self.gui.resize(self.screen.get_size())
        self.camera = Camera(self.map.map_surface.surface, initial_offset=(-self.gui.shop.box.get_width(), 0))

    @property
    def game_speed(self):
        return self.__game_speed_options[self.game_speed_index]

    @property
    def quit(self):
        return self._quit

    @quit.setter
    def quit(self, value: bool):
        if value:
            self.enemies = []
            self.defenses = []
        self._quit = value

    def resize(self):
        self.gui.resize(self.screen.get_size())

    def preview_turret_collision_checker(self, preview_turret: PreviewTurret):
        """
        Berechnet, ob ein Vorschau-Turm sich auf einer zur Bebauung markierten Fläche befindet
        oder mit einem Objekt kollidiert.
        """
        preview_turret.rect.center = self.camera.canvas.translate_vector(pygame.mouse.get_pos())

        preview_turret.colliding = self.coins < self.turret_info[preview_turret.turret_type].cost
        while not preview_turret.colliding:
            for zone in self.map.construction_zones:
                if preview_turret.rect.colliderect(zone):
                    break
            else:
                preview_turret.colliding = True

            for turret in preview_turret.turret_list:
                if preview_turret.rect.colliderect(turret.rect):
                    preview_turret.colliding = True
                    break
            break
        return

    def unselect_defenses(self):
        if self.selected_turret:
            self.selected_turret.overlay = False
        self.selected_turret = None

    def handle_events(self, events: List[pygame.event.Event]):
        self.click = False

        for event in events:
            if not self.lock:
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                    if event.type == pygame.MOUSEBUTTONUP and event.button not in (4, 5):
                        self.click = True
                        if self.turret_preview:
                            defenses = len(self.defenses)
                            self.turret_info[self.turret_preview].preview.place(self.enemies, self.vfx_manager)
                            if len(self.defenses) > defenses:
                                self.coins -= self.turret_info[self.turret_preview].cost
                            self.turret_preview = None
                        else:
                            for defense in self.defenses:
                                if defense.rect.collidepoint(
                                        self.camera.canvas.translate_vector(pygame.mouse.get_pos())
                                ):
                                    if defense != self.selected_turret:
                                        self.unselect_defenses()
                                        defense.overlay = True
                                        self.selected_turret = defense
                                    else:
                                        self.unselect_defenses()

                    if not self.turret_preview or event.button in (4, 5):
                        self.camera.move(event)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.pause = not self.pause
                    elif event.key == pygame.K_o:
                        self.game_speed_index -= 1 if self.game_speed_index != 0 else 0
                    elif event.key == pygame.K_p:
                        self.game_speed_index += 1 if self.game_speed_index != len(self.__game_speed_options) - 1 else 0
                    elif event.key == pygame.K_RETURN:
                        self.gui.next_wave_button.click()
            if event.type == pygame.MOUSEBUTTONUP and event.button not in (4, 5):
                self.click = True
            elif event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                self.gui.settings_button.click()
            elif event.type == pygame.VIDEORESIZE:
                self.resize()

        self.camera.update()

    def update(self, timedelta: float):
        self.real_timedelta = timedelta
        self.real_ingame_time += self.real_timedelta

        # Durch die einfache Multiplikation der verstrichenen Zeit mit der derzeitigen Spielgeschwindigkeit gibt es bei
        # hohen Geschwindigkeiten zwar weniger virtuelle Frames, dafür wird jedoch weniger Rechenleistung benötigt als
        # bei mehrfachem Aufrufen der update-Funktion
        self.effective_timedelta = self.real_timedelta * self.game_speed * (not self.pause)
        self.effective_ingame_time += self.effective_timedelta

        if not self.pause:
            if self.wave_active:
                self.wave_time_passed += self.effective_timedelta
                if self.wave_info[str(self.wave)] == self.wave_control_info:
                    if not self.wave == max([int(i) for i in self.wave_info.keys()]):
                        self.wave_active = False
                        self.wave_control_info = {}
                        self.wave_time_passed = 0
                    elif not self.enemies:
                        self.game_won = True
                        print("YOU WIN")
                else:
                    for wave_pulse in self.wave_info[str(self.wave)].keys():
                        if self.wave_time_passed < float(wave_pulse):
                            continue
                        for pulse_duration in self.wave_info[str(self.wave)][wave_pulse]:
                            for enemy_type in self.wave_info[str(self.wave)][wave_pulse][pulse_duration]:
                                enemies_to_spawn = int(
                                    int(self.wave_info[str(self.wave)][wave_pulse][pulse_duration][enemy_type])
                                    * min(1., ((self.wave_time_passed - float(wave_pulse)) / float(pulse_duration)))
                                )
                                try:
                                    if int(self.wave_control_info[wave_pulse][pulse_duration][enemy_type]) < enemies_to_spawn:
                                        for i in range(enemies_to_spawn - int(self.wave_control_info[wave_pulse][pulse_duration][enemy_type])):
                                            path = self.map.paths[0]
                                            new_enemy = DefaultEnemy(path[0], self.config.ENEMY_SPEED,
                                                                     path=path, enemy_list=self.enemies,
                                                                     live_points=int(enemy_type) * 10 + 10,
                                                                     level=int(enemy_type))

                                            @new_enemy.on_kill
                                            def _():
                                                coin_gain = {0: 1, 1: 2, 2: 5, 3: 10}[new_enemy.level]
                                                self.coins += coin_gain
                                                self.vfx_manager.add_effect(
                                                    self.map, EnemyKillEffect(
                                                        EnemyKillEffectData(0.33, new_enemy.position)
                                                    )
                                                )

                                            @new_enemy.on_success
                                            def _():
                                                self.lives -= {0: 5, 1: 10, 2: 25, 3: 50}[new_enemy.level]

                                            @new_enemy.on_unbuffering_damage
                                            def _():
                                                total_dmg = new_enemy.damage_buffer
                                                relative_dmg = min(1., total_dmg / new_enemy.max_live_points)
                                                text_color = (255, 0 + int((1 - relative_dmg) * 255), 0)
                                                self.vfx_manager.add_effect(self.map,
                                                                            TextParticleEffect(TextParticleEffectData(
                                                                                font=FontManager.get_font(
                                                                                    Font.PIXEL, 10),
                                                                                text=str(round(total_dmg, 1)),
                                                                                initial_color=text_color,
                                                                                final_color=text_color,
                                                                                position=new_enemy.position,
                                                                                initial_speed=15,
                                                                            )))

                                        self.wave_control_info[wave_pulse][pulse_duration][enemy_type] = str(enemies_to_spawn)
                                except KeyError:
                                    if wave_pulse not in self.wave_control_info:
                                        self.wave_control_info[wave_pulse] = {}
                                    if pulse_duration not in self.wave_control_info[wave_pulse]:
                                        self.wave_control_info[wave_pulse][pulse_duration] = {}
                                    if enemy_type not in self.wave_control_info[wave_pulse][pulse_duration]:
                                        self.wave_control_info[wave_pulse][pulse_duration][enemy_type] = str(0)
            else:
                if self.start_next_wave:
                    self.wave += 1
                    if not str(self.wave) in self.wave_info:
                        self.wave -= 1
                    self.wave_active = True
                    self.start_next_wave = False

            if self.lives <= 0:
                print("GAME OVER")

            self.update_entities()

        self.update_ui()

        self.vfx_manager.update(self.real_timedelta)

    def update_entities(self):
        for enemy in self.enemies:
            enemy.update(self.effective_timedelta)

        for defense in self.defenses:
            defense.update(self.effective_timedelta)

    def update_ui(self):
        if self.turret_preview:
            self.turret_info[self.turret_preview].preview.update(self.effective_timedelta)

        self.gui.update(self.click, pygame.mouse.get_pos(), self.camera.moving)

    def render(self, surface: pygame.Surface):
        if surface.get_size() != self.__surface.get_size():
            self.__surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        self.__surface.fill((0, 0, 0, 0))

        self.render_entities()

        self.map.render()

        if self.turret_preview:
            self.turret_info[self.turret_preview].preview.render(self.camera.overlay.surface)

        self.camera.render(self.__surface)

        self.gui.render(self.__surface)

        surface.blit(self.__surface, (0, 0))
        return

    def render_entities(self):
        for enemy in self.enemies:
            enemy.render(self.map.map_surface)

        for defense in self.defenses:
            defense.render(self.map.map_surface)
