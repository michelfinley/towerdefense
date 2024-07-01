import math
import operator
from typing import Tuple, List, Callable, Any

from PIL import Image
import numpy as np
import pygame

from data.constants import AimMode, Sprite, ResEffect, TurretType, MapLayer
from data.lib.entity_objects import Projectile, Entity, Enemy, Turret, DefenseEntity, ProjectileData, PreviewTurret
from data.lib.map_objects import MapSurface
from data.lib.sprites import SpriteData, load_sprite
from data.lib.vfx import VFXManager, BulletImpactEffect, BulletImpactEffectData, BeamShootEffect, BeamShootEffectData


class Bullet(Projectile):
    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float], /, enemy_list: List[Enemy],
                 projectile_list: List[Entity], turret_aim_mode: AimMode, turret_range: float, vfx_manager: VFXManager,
                 *, max_jumps: int = 1):
        super().__init__(sprite_data, position, enemy_list, projectile_list, turret_aim_mode, turret_range, vfx_manager)

        self.rect.topleft = (self.origin[0] - self.sprite_data.images[0].get_width() / 2,
                             self.origin[1] - self.sprite_data.images[0].get_height() / 2)

        self.current_jumps = 0
        self.max_jumps = max_jumps

        self.speed = 400
        self.damage = 10

        self.impact = False
        self.__remove = False

    def remove(self):
        self.projectile_list.remove(self)
        del self
        return

    def update(self, timedelta: float) -> None:
        if self.__remove:
            if not self.vfx_manager.get_effects(self):
                self.remove()
            return

        if self.impact:
            self.vfx_manager.add_effect(self, BulletImpactEffect(
                BulletImpactEffectData(0.33, (self.target.rect.left + 8, self.target.rect.top + 8))
            ))
            self.target.damage(self.damage)
            self.target.unbuffer_damage()
            self.current_jumps += 1
            if self.current_jumps < self.max_jumps:
                self.retarget()
                self.impact = False
            else:
                self.__remove = True
                return

        if not self.target.alive:
            self.retarget()

        target_position = self.target.rect.center
        distance_vector = tuple(map(operator.sub, self.rect.center, self.target.rect.center))

        distance_total = abs(distance_vector[0]) + abs(distance_vector[1])
        if distance_total:
            self.rect.topleft = (
                self.rect.x + self.speed * timedelta * ((target_position[0] - self.rect.x) / distance_total),
                self.rect.y + self.speed * timedelta * ((target_position[1] - self.rect.y) / distance_total),
            )
        else:
            self.rect.topleft = target_position

        if self.target.rect.colliderect(self.rect):
            self.impact = True

        degree = math.degrees(math.atan2(distance_vector[0], distance_vector[1])) + 180

        if 0 <= degree < 22.5 or 157.5 <= degree < 202.5 or 337.5 <= degree <= 360:
            self.image = self.sprite_data.images[0]
        elif 22.5 <= degree < 62.5 or 202.5 <= degree < 247.5:
            self.image = self.sprite_data.images[3]
        elif 62.5 <= degree < 112.5 or 247.5 <= degree < 292.5:
            self.image = self.sprite_data.images[2]
        elif 112.5 <= degree < 157.5 or 292.5 <= degree < 337.5:
            self.image = self.sprite_data.images[1]
        return

    def render(self, surface: MapSurface):
        self.vfx_manager.render(self, surface.get_surface(MapLayer.VFX))
        if not self.__remove:
            super().render(surface)


class DefaultEnemy(Enemy):
    default_sprite_data: SpriteData = None

    def __init__(self, position: Tuple[float, float], speed: float,
                 /, path: List[Tuple[float, float]], enemy_list: List[Entity], live_points: float,
                 *, level: int = 0):
        if DefaultEnemy.default_sprite_data is None:
            DefaultEnemy.default_sprite_data = SpriteData(load_sprite(Sprite.ENEMIES, (32, 32))[0])
        super().__init__(DefaultEnemy.default_sprite_data, position, speed, path, enemy_list, live_points, level=level)


class BlueTurret(Turret):
    def __init__(self, position: Tuple[float, float],
                 /, defense_range: float, turret_list: List[DefenseEntity], enemy_list: List[Enemy],
                 vfx_manager: VFXManager,
                 *, aim_mode: AimMode = AimMode.First, level: int = 1):
        if BlueTurret.default_sprite_data is None:
            BlueTurret.default_sprite_data = SpriteData(load_sprite(Sprite.BLUE_TURRET, (32, 32))[0])

        projectile_data = ProjectileData(Bullet, SpriteData(load_sprite(ResEffect.BULLET, (16, 16))[0]))

        turret_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(turret_surf, (7, 0, 21), (9, 11, 14, 12))
        pygame.draw.rect(turret_surf, (7, 0, 21), (9, 9, 4, 2))
        pygame.draw.rect(turret_surf, (7, 0, 21), (19, 9, 4, 2))
        pygame.draw.rect(turret_surf, (54, 44, 74), (11, 11, 10, 10))

        super().__init__(position, defense_range, turret_list, enemy_list,
                         projectile_data, 1, turret_surf, vfx_manager,
                         sprite_data=BlueTurret.default_sprite_data, aim_mode=aim_mode, level=level)


class PreviewBlueTurret(PreviewTurret):
    def __init__(self,
                 /, turret_range: float, turret_list: List[DefenseEntity], collision_checker: Callable[[Any], None],
                 *, level: int = 1):
        if BlueTurret.default_sprite_data is None:
            BlueTurret.default_sprite_data = SpriteData(load_sprite(Sprite.BLUE_TURRET, (32, 32))[0])
        super().__init__(turret_range, TurretType.BLUE, BlueTurret, turret_list, collision_checker, level=level)


# Die beiden folgenden Funktionen stammen von:
# https://stackoverflow.com/questions/59553156/pygame-detecting-collision-of-a-rotating-rectangle
# bzw. https://stackoverflow.com/a/59553589
def collide_line_line(p0, p1, q0, q1):
    d = (p1[0] - p0[0]) * (q1[1] - q0[1]) + (p1[1] - p0[1]) * (q0[0] - q1[0])
    if d == 0:
        return False
    t = ((q0[0] - p0[0]) * (q1[1] - q0[1]) + (q0[1] - p0[1]) * (q0[0] - q1[0])) / d
    u = ((q0[0] - p0[0]) * (p1[1] - p0[1]) + (q0[1] - p0[1]) * (p0[0] - p1[0])) / d
    return 0 <= t <= 1 and 0 <= u <= 1


def collide_rect_line(rect, p1, p2):
    return (collide_line_line(p1, p2, rect.topleft, rect.bottomleft) or
            collide_line_line(p1, p2, rect.bottomleft, rect.bottomright) or
            collide_line_line(p1, p2, rect.bottomright, rect.topright) or
            collide_line_line(p1, p2, rect.topright, rect.topleft))


class Beam(Projectile):
    length: float
    origin: Tuple[float, float]
    position: Tuple[float, float]
    c_damaged_targets: List[Enemy]
    damage_per_shot: float
    current_damage: float
    bps: float
    pivot: Tuple[float, float]
    offset: pygame.Vector2

    def __init__(self, sprite_data: SpriteData, position: Tuple[float, float],
                 /, enemy_list: List[Enemy],
                 projectile_list: List[Entity], turret_aim_mode: AimMode, turret_range: float, vfx_manager: VFXManager):
        """
        Subklasse von Entity zum Erzeugen eines Geschossstrahls
        :param sprite_data: Sprite-Daten, auf welche zur Animation des Geschossstrahls zurückgegriffen werden soll
        :param position: Position an welcher der Strahl starten soll
        """
        super().__init__(sprite_data, position, enemy_list, projectile_list, turret_aim_mode, turret_range, vfx_manager)

        self.image: pygame.Surface

        self.length = turret_range

        self.position = (self.origin[0] - self.length, self.origin[1])

        self.target = None
        self.c_damaged_targets = []

        self.damage_per_shot = 20
        self.current_damage = 0
        self.bps = 0.2

        self.pivot = (0, 0)
        self.offset = pygame.math.Vector2(0, 0)

        self.__animation_timer = 0

        self.__shoot_effect = BeamShootEffect(BeamShootEffectData(duration=sum(self.sprite_data.animation_duration)*2))
        self.vfx_manager.add_effect(self, self.__shoot_effect)

        self.__remove = False

    def remove(self):
        try:
            self.projectile_list.remove(self)
        except ValueError:
            pass
        del self

    def update(self, timedelta: float) -> None:
        """
        Berechnet das nächste Bild des Strahls.
        """
        if self.__remove:
            self.__shoot_effect.data.duration = 0
            if not self.vfx_manager.get_effects(self):
                self.remove()
            return

        self.retarget()

        self.__animation_timer += timedelta

        if self.__animation_timer >= sum(self.sprite_data.animation_duration):
            self.__remove = True
            return

        current_animation_index = 0
        test = self.__animation_timer

        while test > 0:
            test -= self.sprite_data.animation_duration[current_animation_index]
            current_animation_index += 1
        current_animation_index -= 1

        self.image = pygame.transform.scale(self.sprite_data.images[current_animation_index],
                                            (self.sprite_data.images[0].get_width(), self.length))

        if self.target is None:
            self.__remove = True
            return

        x_diff = (self.target.rect.centerx - self.origin[0])
        y_diff = (self.target.rect.centery - self.origin[1])

        if y_diff == 0:
            y_diff = 0.01

        angle = math.degrees(math.atan2(x_diff, y_diff))
        self.image = pygame.transform.rotate(self.image, angle)
        self.__shoot_effect.emitter.data.direction_of_emission = (angle - 45, angle + 45)
        self.__shoot_effect.update(timedelta, self.origin, (0, 0))

        # Bei den folgenden Zeilen habe ich auf Codeabschnitte folgender Quelle zurückgegriffen:
        # https://stackoverflow.com/questions/15098900/how-to-set-the-pivot-point-center-of-rotation-for-pygame-transform-rotate
        # bzw. https://stackoverflow.com/a/49413006
        self.pivot = self.origin
        self.offset = pygame.math.Vector2(self.length / 2 * math.sin(math.radians(angle)),
                                          self.length / 2 * math.cos(math.radians(angle)))

        # noinspection PyTypeChecker
        rect = self.image.get_rect(center=(self.pivot + self.offset))
        self.position = rect.topleft

        # Der Rest dieser Funktion stammt größtenteils aus https://stackoverflow.com/a/59553589
        if self.sprite_data.inflicted_damage[current_animation_index]:
            if angle < 90 or (180 < angle < 270):
                laserline = [rect.topleft, rect.bottomright]
            else:
                laserline = [rect.bottomleft, rect.topright]

            new_damage = (self.damage_per_shot
                          * self.sprite_data.inflicted_damage[current_animation_index]
                          / self.sprite_data.animation_duration[current_animation_index]
                          * timedelta)
            self.current_damage += new_damage
            for target in self.enemy_list:
                if collide_rect_line(target.rect, *laserline):
                    target.damage(new_damage)
                    if target not in self.c_damaged_targets:
                        self.c_damaged_targets.append(target)

        elif self.current_damage:
            if angle < 90 or (180 < angle < 270):
                laserline = [rect.topleft, rect.bottomright]
            else:
                laserline = [rect.bottomleft, rect.topright]

            new_damage = self.damage_per_shot - self.current_damage
            for target in self.enemy_list:
                if collide_rect_line(target.rect, *laserline):
                    target.damage(new_damage)
                    if target not in self.c_damaged_targets:
                        self.c_damaged_targets.append(target)
            self.current_damage = 0

        elif self.c_damaged_targets:
            for target in self.c_damaged_targets:
                target.unbuffer_damage()
            self.c_damaged_targets = []
        self.rect.topleft = self.position
        return

    def render(self, surface: MapSurface):
        self.vfx_manager.render(self, surface.get_surface(MapLayer.Projectiles))
        if not self.__remove:
            super().render(surface)


class RedTurret(Turret):
    beam: Beam
    enemies_in_range: List[Enemy] | None

    def __init__(self, position: Tuple[float, float],
                 /, defense_range: float, turret_list: List[DefenseEntity], enemy_list: List[Enemy],
                 vfx_manager: VFXManager,
                 *, aim_mode: AimMode = AimMode.First, level: int = 1):
        if RedTurret.default_sprite_data is None:
            RedTurret.default_sprite_data = SpriteData(load_sprite(Sprite.RED_TURRET, (32, 32))[0])

        images = []

        original_image = np.array(Image.open(ResEffect.BEAM).convert("RGBA"))
        w, h = 16, 16
        tiles = [original_image[x:x + w, y:y + h] for x in range(0, original_image.shape[0], w) for y in
                 range(0, original_image.shape[1], h)]

        for p, image in enumerate(tiles):
            arr = np.array(np.asarray(image))

            red, green, blue, alpha = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
            mask1 = (red == 0) & (green == 0) & (blue == 0) & (alpha == 0)
            arr[:, :, :4][mask1] = [255, 255, 255, 255]

            alpha = 255 * (1 - arr[:, :, :3].sum(axis=2) / (3 * 255))
            arr[:, :, 3] = alpha.astype(np.uint8)

            image = arr

            images.append(
                pygame.image.frombuffer(image.tobytes(), image.shape[1::-1], "RGBA").convert_alpha()
            )

        projectile_sprite_data = SpriteData([images[0], images[3], images[1], images[3], images[0]])
        projectile_sprite_data.animation_duration = [0.5, 0.5, 1, 0.1, 0.1]

        projectile_sprite_data.inflicted_damage = [0.2, 0.2, 0.4, 0.1, 0.1]

        projectile_data = ProjectileData(Beam, projectile_sprite_data)

        turret_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(turret_surf, (7, 0, 21), (9, 11, 14, 12))
        pygame.draw.rect(turret_surf, (7, 0, 21), (9, 9, 4, 2))
        pygame.draw.rect(turret_surf, (7, 0, 21), (19, 9, 4, 2))
        pygame.draw.rect(turret_surf, (74, 44, 54), (11, 11, 10, 10))

        super().__init__(position, defense_range, turret_list, enemy_list,
                         projectile_data, 0.33, turret_surf, vfx_manager,
                         sprite_data=RedTurret.default_sprite_data, aim_mode=aim_mode, level=level)

        self.enemies_in_range = None

    def render(self, surface: MapSurface):
        super().render(surface)


class PreviewRedTurret(PreviewTurret):
    def __init__(self,
                 /, turret_range: float, turret_list: List[DefenseEntity], collision_checker: Callable[[Any], None],
                 *, level: int = 1):
        if RedTurret.default_sprite_data is None:
            RedTurret.default_sprite_data = SpriteData(load_sprite(Sprite.RED_TURRET, (32, 32))[0])
        super().__init__(turret_range, TurretType.RED, RedTurret, turret_list, collision_checker, level=level)
