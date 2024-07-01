import abc
import math
import random
from dataclasses import dataclass
from typing import Tuple, List, Type, Callable, Any

import pygame

from data.constants import MapLayer, AimMode, Color, TurretType
from data.lib.map_objects import MapSurface
from data.lib.sprites import SpriteData
from data.lib.vfx import VFXManager
from data.lib.vfx_utils import get_outline


class Entity:
    sprite_data: SpriteData
    image: pygame.Surface
    rect: pygame.Rect

    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float]):
        """
        Superklasse für jedes Objekt, das auf dem Bildschirm dargestellt werden soll.
        :param sprite_data: Eine Liste aller Einzelbilder des Objekts zum Erstellen von Animationen o.ä.
        :param position: Koordinate an welcher das Objekt erzeugt werden soll
        """
        super().__init__()
        self.sprite_data = sprite_data
        self.image = self.sprite_data.images[0]
        self.rect = self.image.get_rect(topleft=position)

    def update(self, timedelta: float) -> bool:
        """
        Platzhalter-Funktion um Berechnungen durchzuführen
        :param timedelta: Zeit in Sekunden, die seit dem letzten Funktionsaufruf verstrichen ist
        """
        return False

    def render(self, surface: MapSurface):
        """
        Gibt das derzeitige Bild an der momentanen Position aus
        :param surface: Oberfläche auf welcher das Objekt ausgegeben werden soll
        """
        surface.blit(MapLayer.Default, self.image, self.rect.topleft)
        return


class Enemy(Entity):
    position: Tuple[float, float]

    speed: float

    spawn: Tuple[float, float]
    path: List[Tuple[float, float]]

    # derzeitiger Zielpunkt als Index auf dem gegebenen Pfad
    target: int

    enemy_list: List[Entity]

    level: int

    max_live_points: float
    live_points: float
    damage_buffer: float

    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float],
                 /, speed: float, path: List[Tuple[float, float]], enemy_list: List[Entity], live_points: float,
                 *, level: int = 0):
        """
        Subklasse von Entity zum Erzeugen eines Gegners
        :param position: Position an welcher der Gegner starten soll.
        :param path: Pfad, welchem der Gegner auf der Karte folgen soll.
        :param sprite_data: Bilder, welche für die Animation des Gegners verwendet werden sollen.
        :param live_points: Anzahl der Lebenspunkte, die der Gegner zu Beginn haben soll.
        :param speed: Geschwindigkeit in Pixel pro Sekunde, mit welcher sich der Gegner fortbewegen soll.
        :param level: Position des Bildes, welches verwendet werden soll, in der Liste aller Bilder der Sprite-Daten.
        """
        super().__init__(sprite_data, position)

        self.speed = speed

        self.path = path
        self.spawn = self.rect.topleft
        self.target = 0

        self.position = self.spawn

        self.enemy_list = enemy_list
        self.enemy_list.append(self)

        self.level = level

        self.image = self.sprite_data.images[self.level]
        self.rect = self.image.get_rect(topleft=self.rect.topleft)

        self.max_live_points = live_points
        self.live_points = self.max_live_points
        self.damage_buffer = 0
        self.__damage_buffer_boundary = 5

        self.alive = True

        self.__on_kill_funcs = []
        self.__on_success_funcs = []
        self.__on_unbuffering_damage_funcs = []

    def on_kill(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_kill_funcs.append(func)
        return func

    def on_success(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_success_funcs.append(func)
        return func

    def on_unbuffering_damage(self, func: Callable[[], None]) -> Callable[[], None]:
        self.__on_unbuffering_damage_funcs.append(func)
        return func

    def damage(self, damage_points: float):
        if self.live_points is None:
            return
        else:
            self.live_points -= damage_points
            self.damage_buffer += damage_points

        if self.live_points <= 0:
            self.unbuffer_damage(True)
            if self.alive:
                for func in self.__on_kill_funcs:
                    func()
            self.alive = False
            self.remove()
        return

    def unbuffer_damage(self, ignore_damage_buffer_boundary: bool = False):
        self.damage_buffer = min(self.max_live_points, self.damage_buffer)
        if self.__damage_buffer_boundary < self.damage_buffer or ignore_damage_buffer_boundary:
            for func in self.__on_unbuffering_damage_funcs:
                func()
            self.damage_buffer = 0
        return

    def remove(self):
        """
        Entfernt den Gegner aus der Liste der aktiven Gegner und löscht alle Geschosse, die diesen Gegner treffen sollen
        """
        if self in self.enemy_list:
            self.enemy_list.remove(self)
        return

    def update(self, timedelta: float) -> bool:
        """
        Berechnet die nächste Position des Gegners
        :return: True, wenn der Gegner einen anderen Startpunkt erreicht. Ansonsten wird False zurückgegeben.
        """
        next_position = self.position
        remaining_speed = self.speed * timedelta

        while remaining_speed:
            if next_position == self.path[self.target]:
                self.target += 1
            if self.target > len(self.path) - 1:
                for func in self.__on_success_funcs:
                    func()
                self.remove()
                return True

            dx = self.path[self.target][0] - next_position[0]
            dy = self.path[self.target][1] - next_position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if remaining_speed >= distance:
                next_position = self.path[self.target]
                remaining_speed -= distance
            else:
                next_position = (
                    next_position[0] + dx * remaining_speed / distance,
                    next_position[1] + dy * remaining_speed / distance
                )
                remaining_speed = 0

        self.position = next_position
        self.rect.topleft = next_position
        return False

    def render(self, surface: MapSurface):
        surface.blit(MapLayer.Enemy, self.image, self.rect.topleft)
        return


class Projectile(Entity):
    origin: pygame.math.Vector2
    enemy_list: List[Enemy]
    target: Enemy | Tuple[float, float] | None

    projectile_list: List[Entity]

    turret_aim_mode: AimMode
    turret_range: float

    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float],
                 /, enemy_list: List[Enemy], projectile_list: List[Entity],
                 turret_aim_mode: AimMode, turret_range: float, vfx_manager: VFXManager):
        super().__init__(sprite_data, position)

        self.vfx_manager = vfx_manager

        self.origin = pygame.math.Vector2(self.rect.topleft)

        self.enemy_list = enemy_list
        self.target = None

        self.projectile_list = projectile_list
        self.projectile_list.append(self)

        self.turret_aim_mode = turret_aim_mode
        self.turret_range = turret_range

        self.retarget()

    def retarget(self):
        if self.enemy_list:
            enemies_in_range = [
                enemy for enemy in self.enemy_list

                if ((enemy.rect.centerx - self.origin.x) ** 2 + (enemy.rect.centery - self.origin.y) ** 2) ** 0.5
                <= self.turret_range and enemy.alive
            ]
            if enemies_in_range:
                possible_enemies = {}
                if self.turret_aim_mode == AimMode.First:
                    for enemy in enemies_in_range:
                        possible_enemies[
                            (enemy.target, abs(sum(enemy.path[enemy.target]) - sum(enemy.rect.topleft)))
                        ] = enemy
                    self.target = possible_enemies[max([
                        e_target for e_target in possible_enemies.keys() if e_target == max(possible_enemies.keys())
                    ], key=lambda x: x[1])]

                elif self.turret_aim_mode == AimMode.Nearest:
                    self.target = min(
                        enemies_in_range, key=lambda enemy: (
                                ((enemy.rect.x - self.rect.x) ** 2 + (enemy.rect.y - self.rect.y) ** 2) ** 0.5
                        )
                    )

                elif self.turret_aim_mode == AimMode.Last:
                    self.target = max(
                        enemies_in_range, key=lambda enemy: (
                                ((enemy.rect.x - self.rect.x) ** 2 + (enemy.rect.y - self.rect.y) ** 2) ** 0.5
                        )
                    )

                elif self.turret_aim_mode == AimMode.Random:
                    self.target = random.choice(enemies_in_range)

                else:
                    raise ValueError("self.aiming not in AimModes")
            else:
                self.remove()
        else:
            self.remove()

    @abc.abstractmethod
    def remove(self):
        pass

    @abc.abstractmethod
    def update(self, timedelta: float):
        pass

    def render(self, surface: MapSurface):
        surface.blit(MapLayer.Projectiles, self.image, self.rect.topleft)
        return


@dataclass
class ProjectileData:
    type: Type[Projectile]
    sprite_data: SpriteData


class DefenseEntity(Entity):
    range: float
    level: int

    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float],
                 /, defense_range: float,
                 *, level: int = 1):
        super().__init__(sprite_data, position)

        self.range = defense_range
        self.level = level

    def remove(self):
        del self
        return


class Turret(DefenseEntity):
    default_sprite_data: SpriteData = None
    default_projectile_sprite_data: SpriteData = None

    turret_list: List[DefenseEntity]
    enemy_list: List[Enemy]

    aim_mode: AimMode
    projectile_data: ProjectileData
    projectiles_per_second: float
    projectiles: List[Projectile]
    time_since_last_shot: float

    overlay: bool

    def __init__(self, position: Tuple[float, float],
                 /, defense_range: float,
                 turret_list: List[DefenseEntity], enemy_list: List[Enemy],
                 projectile_data: ProjectileData, projectiles_per_second: float, turret_image: pygame.Surface,
                 vfx_manager: VFXManager,
                 *, sprite_data: SpriteData = None, aim_mode: AimMode = AimMode.First, level: int = 1):
        """
        Subklasse von Entity zum Erzeugen eines Turmes
        :param position: Position, an welcher der Turm erzeugt werden soll.
        :param projectiles_per_second: Anzahl an Geschossen, welche pro Sekunde abgefeuert werden sollen.
        :param defense_range: Reichweite des Turmes in Pixeln.
        :param sprite_data: Sprite-Daten, welche für die Animation des Turmes verwendet werden sollen.
        :param aim_mode: Zielmodus des Turmes.
        :param level: Bild, welches für die Animation des Turmes verwendet werden soll.
        """
        super().__init__(sprite_data, position, defense_range, level=level)

        self.vfx_manager = vfx_manager

        self.base_image = self.sprite_data.images[self.level]
        self.rect = self.base_image.get_rect(topleft=self.rect.topleft)

        self.turret_image = turret_image
        self.__current_turret_image = self.turret_image
        self.turret_target_pos = self.rect.midtop

        self.turret_list = turret_list
        self.turret_list.append(self)

        self.enemy_list = enemy_list

        self.aim_mode = aim_mode
        self.projectile_data = projectile_data
        self.projectiles_per_second = projectiles_per_second
        self.projectiles = []
        self.time_since_last_shot = 1 / projectiles_per_second

        self.overlay = False

    def update(self, timedelta: float) -> None:
        """
        Errechnet, ob ein weiteres Geschoss abgefeuert werden soll. Wenn ja, wird dieses Objekt erzeugt.
        """
        self.time_since_last_shot += timedelta
        if self.enemy_list and self.time_since_last_shot >= (1 / self.projectiles_per_second):
            self.projectile_data.type(self.projectile_data.sprite_data, self.rect.center,
                                      self.enemy_list, self.projectiles, self.aim_mode, self.range, self.vfx_manager)
            self.time_since_last_shot -= 1 / self.projectiles_per_second
        elif self.time_since_last_shot > (1 / self.projectiles_per_second):
            self.time_since_last_shot = 1 / self.projectiles_per_second
        for projectile in self.projectiles:
            projectile.update(timedelta)
        if self.projectiles:
            if self.projectiles[-1].target:
                self.turret_target_pos = self.projectiles[-1].target.position
                self.__current_turret_image = pygame.transform.rotate(
                    self.turret_image, 450 - math.degrees(
                        math.atan2((self.rect.center[1] - self.turret_target_pos[1]),
                                   (self.rect.center[0] - self.turret_target_pos[0]))
                    )
                )
        return

    def render(self, surface: MapSurface):
        """
        Gibt den Turm, sowie ggf. eine grafische Darstellung der Reichweite dieses Turmes auf dem Bildschirm aus
        :param surface: Oberfläche auf welcher der Turm ausgegeben werden soll
        """
        if self.overlay:
            target_rect = pygame.Rect(self.rect.center, (0, 0)).inflate((self.range * 2, self.range * 2))
            range_surface = pygame.Surface(target_rect.size, pygame.SRCALPHA)
            pygame.draw.circle(range_surface, Color.OVERLAY_INFO, (self.range, self.range), self.range)
            surface.blit(MapLayer.TurretBaseOverlay, range_surface, target_rect)

            surface.blit(MapLayer.TurretBase, get_outline(self.base_image, (255, 255, 64)), self.rect.topleft)

        else:
            surface.blit(MapLayer.TurretBase, self.base_image, self.rect.topleft)

        surface.blit(MapLayer.Turret, self.__current_turret_image,
                     (self.rect.center[0] - self.__current_turret_image.get_width() / 2,
                      self.rect.center[1] - self.__current_turret_image.get_height() / 2))

        for projectile in self.projectiles:
            projectile.render(surface)
        return

    def remove(self):
        """
        Entfernt den Turm aus der Liste der aktiven Türme
        """
        self.turret_list.remove(self)
        del self
        return


class PreviewTurret(DefenseEntity):
    turret_type: TurretType
    turret_class: Type[Turret]
    turret_list: List[DefenseEntity]

    colliding: bool

    def __init__(self,
                 /, defense_range: float, turret_type: TurretType, turret_class: Type[Turret],
                 turret_list: List[DefenseEntity],
                 collision_checker: Callable[[Any], None],
                 *, level: int = 1):
        """
        Subklasse von Entity zum Erzeugen eines Vorschau-Turmes
        :param defense_range: Reichweite des Turmes in Pixeln.
        :param turret_type: Typ des Turmes.
        :param turret_class: Subklasse von Turret, welche zur Erzeugung des Turms verwendet werden soll.
        :param collision_checker: Funktion, welche überprüft, ob der Vorschau-Turm mit einem Objekt kollidiert.
        :param level: Bild, welches für die Animation des Turmes verwendet werden soll.
        """
        super().__init__(turret_class.default_sprite_data, (0, 0), defense_range, level=level)

        self.__original_image = self.sprite_data.images[self.level]
        self.image = self.__original_image
        self.rect = self.image.get_rect(center=(0, 0))

        self.turret_type = turret_type
        self.turret_class = turret_class
        self.turret_list = turret_list

        self.colliding = False
        self.collision_checker = collision_checker

    def update(self, timedelta: float) -> None:
        self.collision_checker(self)
        return

    def render(self, surface: pygame.Surface):
        """
        Gibt den Turm, sowie eine Markierung zur Vorschau der Reichweite dieses Turmes auf dem Bildschirm aus
        :param surface: Oberfläche auf welcher der Turm ausgegeben werden soll
        """
        target_rect = pygame.Rect(self.rect.center, (0, 0)).inflate((self.range * 2, self.range * 2))
        range_surface = pygame.Surface(target_rect.size, pygame.SRCALPHA)

        pygame.draw.circle(range_surface, (Color.OVERLAY_COLLIDE if self.colliding else Color.OVERLAY_VALID),
                           (self.range, self.range), self.range)

        surface.blit(range_surface, target_rect)

        surface.blit(self.image, self.rect.topleft)

    def place(self, enemy_list: List[Enemy], vfx_manager: VFXManager,
              *, aim_mode: AimMode = AimMode.First):
        """
        Erstellt einen neuen Turm an der derzeitigen Position, sofern er nicht mit anderen Objekten kollidiert.
        """
        if not self.colliding:
            new_position = pygame.Rect(self.rect.x, self.rect.y, 1, 1)
            new_position = (new_position.x, new_position.y)

            # Unterklassen von Turret haben die Parameter projectile_data, projectiles_per_second und turret_image
            #  nicht in ihrer Initialisierungsfunktion
            # noinspection PyArgumentList
            self.turret_class(new_position, self.range, self.turret_list, enemy_list, vfx_manager,
                              aim_mode=aim_mode, level=self.level)
        self.remove()
