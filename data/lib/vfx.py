import abc
import dataclasses
import math
import random
from dataclasses import dataclass
from typing import Tuple, Dict, List

import pygame

from data.constants import Color, ResEffect
from data.lib import sprites
from data.lib.vfx_utils import draw_gradient_lines, get_outline


@dataclasses.dataclass
class TextureRenderData:
    surface: pygame.Surface

    position: Tuple[float, float] = (0, 0)
    direction: Tuple[float, float] = (0, 0)

    color: Tuple[int, int, int] = (255, 255, 255)

    size: float = 1

    outline: bool = False
    outline_color: Tuple[int, int, int] = (0, 0, 0)
    outline_width: float = 1


class Texture:
    def __init__(self):
        pass

    def render(self, data: TextureRenderData):
        pass


class CircleTexture(Texture):
    def __init__(self):
        super().__init__()

    def render(self, data: TextureRenderData):
        if data.outline:
            pygame.draw.circle(data.surface, data.outline_color, data.position, data.size + data.outline_width)
        pygame.draw.circle(data.surface, data.color, data.position, data.size)


class RectTexture(Texture):
    def __init__(self):
        super().__init__()

    def render(self, data: TextureRenderData):
        if data.outline:
            pygame.draw.rect(data.surface, data.outline_color, (
                data.position[0] - data.outline_width,
                data.position[1] - data.outline_width,
                data.size + data.outline_width * 2,
                data.size + data.outline_width * 2))
        pygame.draw.rect(data.surface, data.color, (*data.position, data.size, data.size))


class LineTexture(Texture):
    def __init__(self):
        super().__init__()

    def render(self, data: TextureRenderData):
        if data.outline:
            pygame.draw.line(data.surface, data.outline_color,
                             (data.position[0] - data.direction[0] * data.outline_width,
                              data.position[1] - data.direction[1] * data.outline_width),
                             (data.position[0] + ((data.size + data.outline_width * 2) * data.direction[0]),
                              data.position[1] + ((data.size + data.outline_width * 2) * data.direction[1])),
                             width=int(1 + data.outline_width * 2))
        pygame.draw.line(data.surface, data.color, data.position,
                         (data.position[0] + data.size * data.direction[0],
                          data.position[1] + data.size * data.direction[1]))


class PlusTexture(Texture):
    def __init__(self):
        super().__init__()

    def render(self, data: TextureRenderData):
        if data.outline:
            pygame.draw.polygon(data.surface, data.outline_color, (
                (data.position[0] - 1 / 3 * data.size - 1 * data.outline_width,
                 data.position[1] - 1 * data.size - 1 * data.outline_width),
                (data.position[0] + 1 / 3 * data.size + 1 * data.outline_width,
                 data.position[1] - 1 * data.size - 1 * data.outline_width),
                (data.position[0] + 1 / 3 * data.size + 1 * data.outline_width,
                 data.position[1] + 1 * data.size + 1 * data.outline_width),
                (data.position[0] - 1 / 3 * data.size - 1 * data.outline_width,
                 data.position[1] + 1 * data.size + 1 * data.outline_width),
                (data.position[0] - 1 / 3 * data.size - 1 * data.outline_width,
                 data.position[1] - 1 * data.size - 1 * data.outline_width)))
            pygame.draw.polygon(data.surface, data.outline_color, (
                (data.position[0] - 1 * data.size - 1 * data.outline_width,
                 data.position[1] - 1 / 3 * data.size - 1 * data.outline_width),
                (data.position[0] + 1 * data.size + 1 * data.outline_width,
                 data.position[1] - 1 / 3 * data.size - 1 * data.outline_width),
                (data.position[0] + 1 * data.size + 1 * data.outline_width,
                 data.position[1] + 1 / 3 * data.size + 1 * data.outline_width),
                (data.position[0] - 1 * data.size - 1 * data.outline_width,
                 data.position[1] + 1 / 3 * data.size + 1 * data.outline_width),
                (data.position[0] - 1 * data.size - 1 * data.outline_width,
                 data.position[1] - 1 / 3 * data.size - 1 * data.outline_width)))

        pygame.draw.polygon(data.surface, data.color, (
            (data.position[0] - 1 / 3 * data.size, data.position[1] - 1 * data.size),
            (data.position[0] + 1 / 3 * data.size, data.position[1] - 1 * data.size),
            (data.position[0] + 1 / 3 * data.size, data.position[1] + 1 * data.size),
            (data.position[0] - 1 / 3 * data.size, data.position[1] + 1 * data.size),
            (data.position[0] - 1 / 3 * data.size, data.position[1] - 1 * data.size)))
        pygame.draw.polygon(data.surface, data.color, (
            (data.position[0] - 1 * data.size, data.position[1] - 1 / 3 * data.size),
            (data.position[0] + 1 * data.size, data.position[1] - 1 / 3 * data.size),
            (data.position[0] + 1 * data.size, data.position[1] + 1 / 3 * data.size),
            (data.position[0] - 1 * data.size, data.position[1] + 1 / 3 * data.size),
            (data.position[0] - 1 * data.size, data.position[1] - 1 / 3 * data.size)))


class StarTexture(Texture):
    def __init__(self):
        super().__init__()
        # Äußere Koordinaten eines Pentagramms als (cos(pi*x), sin(pi*x)): (0.1, 0.5, 0.9, 1.3, 1.7)
        # Innere Koordinaten eines Pentagramms als (cos(pi*x), sin(pi*x)): (0.3, 0.7, 1.1, 1.5, 1.9)
        __raw_star_points = tuple(0.1 + i * 0.2 for i in range(10))
        __raw_star_points = (0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9, 0.1)
        self.star_points = []
        self.star_points = tuple(
            ((1 - 2 / 3 * ((i + 1) % 2)) * math.cos(math.pi * __raw_star_points[i]),
             (1 - 2 / 3 * ((i + 1) % 2)) * math.sin(math.pi * __raw_star_points[i])) for i in
            range(len(__raw_star_points))
        )

    def render(self, data: TextureRenderData):
        if data.outline:
            raise NotImplemented
        pygame.draw.polygon(data.surface, data.color,
                            [(i[0] * data.size + data.position[0], i[1] * data.size + data.position[1])
                             for i in self.star_points])


@dataclass
class ParticleData:
    position: Tuple[float, float] = (0, 0)
    direction: Tuple[float, float] = (0, 0)

    lifetime: float = 1

    texture: Texture = CircleTexture()

    initial_color: Tuple[int, int, int] = (255, 255, 255)
    color: Tuple[int, int, int] = initial_color
    final_color: Tuple[int, int, int] = (255, 255, 255)

    initial_size: float = 10
    size: float = initial_size
    final_size: float = 0

    initial_speed: float = 60
    speed: float = initial_speed
    final_speed: float = 0
    gravity_multiplier: float = 0

    outline: bool = False
    outline_color: Tuple[int, int, int] = (0, 0, 0)
    outline_width: float = 1


@dataclass
class ParticleEmitterData:
    particle_data: ParticleData = dataclasses.field(default_factory=ParticleData)

    position: Tuple[float, float] | Tuple[Tuple[float, float], Tuple[float, float]] = (0, 0)
    max_particles: int = 100
    particles_per_second: float = 0

    direction_of_emission: Tuple[int, int] = (0, 360)  # in Grad, gegen den Uhrzeigersinn, 0° ist nach unten gerichtet

    area_emission_direction: int = 0  # 0: in eine zufällige Richtung, 1: in Richtung des Mittelpunktes


class Particle:
    def __init__(self, data: ParticleData):
        self.data = data

        self.alive = True

        self.__ctime = 0

    def update(self, timedelta: float):
        self.__ctime += timedelta
        relative_time = self.__ctime / self.data.lifetime

        self.data.color = tuple(
            self.data.initial_color[i] + relative_time * (self.data.final_color[i] - self.data.initial_color[i])
            for i in range(3))

        self.data.speed = timedelta * (self.data.initial_speed + relative_time *
                                       (self.data.final_speed - self.data.initial_speed))

        self.data.direction = (self.data.direction[0],
                               self.data.direction[1] + timedelta * (self.data.gravity_multiplier * 0.5))

        self.data.position = (self.data.position[0] + self.data.speed * self.data.direction[0],
                              self.data.position[1] + self.data.speed * self.data.direction[1])

        self.data.size = self.data.initial_size - relative_time * (self.data.initial_size - self.data.final_size)

        if self.__ctime > self.data.lifetime:
            self.alive = False

    def render(self, surface: pygame.Surface):
        texture_render_data = TextureRenderData(surface=surface, color=self.data.color, position=self.data.position,
                                                size=self.data.size, direction=self.data.direction,
                                                outline=self.data.outline, outline_color=self.data.outline_color,
                                                outline_width=self.data.outline_width)
        self.data.texture.render(texture_render_data)


class ParticleEmitter:
    def __init__(self, data: ParticleEmitterData):
        self.data = data

        self.__time_buffer = 1 / self.data.particles_per_second
        self.__particles = []

    def update(self, timedelta: float):
        self.__time_buffer += timedelta
        for particle_to_spawn in range(int(self.__time_buffer * self.data.particles_per_second)):
            if self.data.max_particles > len(self.__particles):
                if all(isinstance(i, tuple) for i in self.data.position):
                    self.data.particle_data.position = (
                        random.randint(self.data.position[0][0], self.data.position[1][0]),
                        random.randint(self.data.position[0][1], self.data.position[1][1]),
                    )
                    if self.data.area_emission_direction == 1:
                        direction = math.atan2(
                            (self.data.position[0][0] + self.data.position[1][0] / 2 - self.data.particle_data.position[0]),
                            (self.data.position[0][1] + self.data.position[1][1] / 2 - self.data.particle_data.position[1]),
                        )
                        self.data.particle_data.direction = (math.sin(direction),
                                                             math.cos(direction))
                    else:
                        self.data.particle_data.direction = (random.random() * 2 - 1, random.random() * 2 - 1)

                else:
                    self.data.particle_data.position = self.data.position
                    direction = (self.data.direction_of_emission[0] + random.random()
                                 * (self.data.direction_of_emission[1] - self.data.direction_of_emission[0]))
                    self.data.particle_data.direction = (math.sin(math.radians(direction)),
                                                         math.cos(math.radians(direction)))
                self.__particles.append(Particle(dataclasses.replace(self.data.particle_data)))
            self.__time_buffer -= 1 / self.data.particles_per_second

        remove_list = []
        for particle in self.__particles:
            particle.update(timedelta)
            if not particle.alive:
                remove_list.append(particle)
        for particle in remove_list:
            self.__particles.remove(particle)

    def render(self, surface: pygame.Surface):
        for particle in self.__particles:
            particle.render(surface)

    def particle_count(self):
        return len(self.__particles)


@dataclass
class EffectData:
    pass


@dataclass
class DefaultEffectData(EffectData):
    duration: float = -1

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class Effect(abc.ABC):
    def __init__(self, data: EffectData):
        self.data = data
        self.done = False

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        self.data.parent_pos = pos
        self.data.parent_size = size

    @abc.abstractmethod
    def render(self, surface: pygame.Surface):
        pass


class MenuBackgroundEffect(Effect):
    def __init__(self):
        super().__init__(DefaultEffectData())

        self.emitter = ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=30,

                texture=CircleTexture(),

                initial_color=(32, 30, 44),
                final_color=Color.BACKGROUND,

                initial_size=256,
                final_size=0,

                initial_speed=120,
                final_speed=0,

                outline=False,
            ),
            position=((0, 0), (0, 0)),
            particles_per_second=0.5,
            max_particles=60,
            direction_of_emission=(0, 360),
            area_emission_direction=1
        ))

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)
        self.emitter.data.position = (pos, (pos[0] + size[0], pos[1] + size[1]))
        self.emitter.update(timedelta)

    def render(self, surface: pygame.Surface):
        self.emitter.render(surface)


@dataclass
class InGameBlendInEffectData(EffectData):
    color: Tuple[float, float, float]
    duration: float

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class InGameBlendInEffect(Effect):
    data: InGameBlendInEffectData

    def __init__(self, data: InGameBlendInEffectData):
        super().__init__(data)

        self.__surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.__surface.fill(self.data.color)

        self.__ctime = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        if self.data.parent_size != self.__surface.get_size():
            self.__surface = pygame.transform.scale(self.__surface, self.data.parent_size)

        self.__ctime += timedelta

        if self.__ctime > self.data.duration:
            self.done = True
            return

        self.__surface.set_alpha(int(255 - self.__ctime / self.data.duration * 255))

    def render(self, surface: pygame.Surface):
        surface.blit(self.__surface, (0, 0))


class InGameBackgroundEffect(Effect):
    def __init__(self):
        super().__init__(DefaultEffectData())

        self.emitter = ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=5,

                texture=CircleTexture(),

                initial_color=(191, 63, 0),
                final_color=(255, 0, 0),

                initial_size=3,
                final_size=0,

                initial_speed=128,
                final_speed=32,

                outline=False,
            ),
            position=((0, 0), (0, 0)),
            particles_per_second=2,
            max_particles=25,
            direction_of_emission=(0, 360)
        ))

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)
        self.emitter.data.position = (pos, (pos[0] + size[0], pos[1] + size[1]))
        self.emitter.update(timedelta)

    def render(self, surface: pygame.Surface):
        self.emitter.render(surface)


@dataclass
class OverlayFadeOutEffectData(EffectData):
    duration: float
    overlay: pygame.Surface
    start_alpha: int = 255
    delay: float = 0

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class OverlayFadeOutEffect(Effect):
    data: OverlayFadeOutEffectData

    def __init__(self, data: OverlayFadeOutEffectData):
        super().__init__(data)

        surf = pygame.Surface(self.data.overlay.get_size(), pygame.SRCALPHA)
        surf.blit(self.data.overlay, (0, 0))
        self.data.overlay = surf

        self.__surface_center = self.data.overlay.get_size()
        self.__c_time = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        self.__c_time += timedelta

        relative_time = 0 if self.data.duration == -1 else (max(0., (self.__c_time - self.data.delay))
                                                            / (self.data.duration - self.data.delay))

        if relative_time >= 1:
            self.done = True
            return

        self.data.overlay.set_alpha(int((1 - relative_time) * self.data.start_alpha))

    def render(self, surface: pygame.Surface):
        surface.blit(self.data.overlay,
                     (self.data.parent_pos[0] + (self.data.parent_size[0] - self.data.overlay.get_width()) / 2,
                      self.data.parent_pos[1] + (self.data.parent_size[1] - self.data.overlay.get_height()) / 2))


@dataclass
class TextParticleEffectData(EffectData):
    font: pygame.font.Font
    text: str

    outline: bool = True

    position: Tuple[float, float] = (0, 0)
    direction_of_emission: Tuple[int, int] = (0, 360)  # in Grad, gegen den Uhrzeigersinn, 0° ist nach unten gerichtet

    lifetime: float = 1

    initial_color: Tuple[int, int, int] = (255, 255, 255)
    color: Tuple[int, int, int] = initial_color
    final_color: Tuple[int, int, int] = (255, 255, 255)

    initial_speed: float = 60
    speed: float = initial_speed
    final_speed: float = 0
    gravity_multiplier: float = 0

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class TextParticleEffect(Effect):
    data: TextParticleEffectData

    def __init__(self, data: TextParticleEffectData):
        super().__init__(data)
        self.__text_surface = self.data.font.render(self.data.text, False, self.data.initial_color)
        if self.data.outline:
            self.__text_surface = get_outline(self.__text_surface, resize=True)

        direction = self.data.direction_of_emission[0] + random.random() * (
                self.data.direction_of_emission[1] - self.data.direction_of_emission[0])
        self.data.direction = (math.sin(math.radians(direction)), math.cos(math.radians(direction)))

        self.__previous_color = self.data.initial_color

        self.__origin = (0, 0)

        self.__ctime = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        if self.__ctime == 0:
            self.__origin = self.data.parent_pos

        self.__ctime += timedelta
        relative_time = self.__ctime / self.data.lifetime

        self.__text_surface.set_alpha(255 - min(255, int(255 * relative_time)))

        self.data.color = tuple(
            self.data.initial_color[i] + relative_time * (self.data.final_color[i] - self.data.initial_color[i])
            for i in range(3))
        
        self.data.color = (
            max(0, min(255, self.data.color[0])),
            max(0, min(255, self.data.color[1])),
            max(0, min(255, self.data.color[2])),
        )

        if self.data.color != self.__previous_color:
            self.__text_surface = self.data.font.render(self.data.text, False, self.data.color)
            if self.data.outline:
                self.__text_surface = get_outline(self.__text_surface, resize=True)

        self.data.speed = timedelta * (self.data.initial_speed + relative_time *
                                       (self.data.final_speed - self.data.initial_speed))

        self.data.direction = (self.data.direction[0],
                               self.data.direction[1] + timedelta * (self.data.gravity_multiplier * 0.5))

        self.data.position = (self.data.position[0] + self.data.speed * self.data.direction[0],
                              self.data.position[1] + self.data.speed * self.data.direction[1])

        if self.__ctime > self.data.lifetime:
            self.done = True

    def render(self, surface: pygame.Surface):
        surface.blit(self.__text_surface, (self.__origin[0] + self.data.position[0],
                                           self.__origin[1] + self.data.position[1]))


@dataclass
class EnemyKillEffectData(EffectData):
    duration: float

    position: Tuple[float, float] = (0, 0)

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class EnemyKillEffect(Effect):
    data: EnemyKillEffectData

    explosion_spritesheet: sprites.Spritesheet = None

    def __init__(self, data: EnemyKillEffectData):
        super().__init__(data)

        if EnemyKillEffect.explosion_spritesheet is None:
            EnemyKillEffect.explosion_spritesheet = sprites.Spritesheet(ResEffect.EXPLOSION)

        self.__image = EnemyKillEffect.explosion_spritesheet.image_at((3 * 32, 0, 32, 32))
        self.__image_num = 0

        self.__ctime = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)
        self.__ctime += timedelta

        current_image_num = int((self.__ctime / self.data.duration) * 5)
        if current_image_num != self.__image_num:
            self.__image = EnemyKillEffect.explosion_spritesheet.image_at((3 * 32 + current_image_num * 32, 0, 32, 32))

        if self.__ctime > self.data.duration:
            self.done = True

    def render(self, surface: pygame.Surface):
        surface.blit(self.__image, self.data.position)


@dataclass
class BulletImpactEffectData(EffectData):
    duration: float

    position: Tuple[float, float] = (0, 0)

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class BulletImpactEffect(Effect):
    data: BulletImpactEffectData

    impact_spritesheet: sprites.Spritesheet = None

    def __init__(self, data: BulletImpactEffectData):
        super().__init__(data)

        if BulletImpactEffect.impact_spritesheet is None:
            BulletImpactEffect.impact_spritesheet = sprites.Spritesheet(ResEffect.BULLET_IMPACT)

        self.__image = BulletImpactEffect.impact_spritesheet.image_at((0, 0, 16, 16))
        self.__image_num = 0

        self.__ctime = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)
        self.__ctime += timedelta

        current_image_num = int((self.__ctime / self.data.duration) * 3)
        if current_image_num != self.__image_num:
            self.__image = BulletImpactEffect.impact_spritesheet.image_at((current_image_num * 16, 0, 16, 16))

        if self.__ctime > self.data.duration:
            self.done = True

    def render(self, surface: pygame.Surface):
        surface.blit(self.__image, self.data.position)


@dataclass
class BeamShootEffectData(EffectData):
    duration: float

    position: Tuple[float, float] = (0, 0)

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class BeamShootEffect(Effect):
    data: BeamShootEffectData

    def __init__(self, data: BeamShootEffectData):
        super().__init__(data)

        self.emitter = ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=0.25,

                texture=LineTexture(),

                initial_color=(255, 0, 0),
                final_color=(192, 128, 0),

                initial_size=5,
                final_size=0,

                initial_speed=198,
                final_speed=64,

                outline=False,
            ),
            position=(0, 0),
            particles_per_second=15,
            max_particles=8,
            direction_of_emission=(135, 225)
        ))

        self.__c_time = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        self.__c_time += timedelta

        if self.__c_time > self.data.duration:
            self.emitter.data.particles_per_second = 0
            if not self.emitter.particle_count():
                self.done = True

        if pos != (0, 0):
            self.emitter.data.position = pos
        self.emitter.update(timedelta)

    def render(self, surface: pygame.Surface):
        self.emitter.render(surface)


class ButtonHighlightEffect(Effect):
    data: DefaultEffectData

    def __init__(self):
        super().__init__(EffectData())
        self.highlight_rects = []
        self.__ctime = 0
        self.counter = 0

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        self.__ctime += timedelta

        if self.counter == 2 and self.__ctime > 2:
            self.__ctime -= 2
            self.highlight_rects.append({"pos": pygame.Vector2((0, 0)), "alpha": 255})
            self.counter = 0
        elif self.counter != 2 and self.__ctime > 0.5:
            self.__ctime -= 0.5
            self.highlight_rects.append({"pos": pygame.Vector2((0, 0)), "alpha": 255})
            self.counter += 1

        for highlight_rect in self.highlight_rects:
            highlight_rect["pos"].x -= 16 * timedelta
            highlight_rect["pos"].y -= 16 * timedelta
            highlight_rect["alpha"] -= 512 * timedelta
            if highlight_rect["alpha"] <= 0:
                self.highlight_rects.remove(highlight_rect)

    def render(self, surface: pygame.Surface):
        for highlight_rect in self.highlight_rects:
            pygame.draw.rect(surface, (200, 100, 0, highlight_rect["alpha"]),
                             (self.data.parent_pos[0] + highlight_rect["pos"].x,
                              self.data.parent_pos[1] + highlight_rect["pos"].y,
                              self.data.parent_size[0] + abs(highlight_rect["pos"].x) * 2 + 2,
                              self.data.parent_size[1] + abs(highlight_rect["pos"].y) * 2 + 2),
                             2, 6)


@dataclass
class GradientLineEffectData(EffectData):
    path: List[Tuple[float, float]]
    line_length: float

    loop_duration: float

    # -1 für eine Dauerschleife
    loop_count: float = 1

    parent_pos: Tuple[float, float] = (0, 0)
    parent_size: Tuple[float, float] = (0, 0)


class GradientLineEffect(Effect):
    data: GradientLineEffectData

    def __init__(self, data: GradientLineEffectData):
        super().__init__(data)

        self.emitter = ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=0.5,

                texture=CircleTexture(),

                initial_color=(255, 255, 255),
                final_color=(200, 200, 200),

                initial_size=3,
                final_size=0,

                initial_speed=20,
                final_speed=0,

                outline=False,
            ),
            position=((0, 0), (0, 0)),
            particles_per_second=30,
            max_particles=30,
            direction_of_emission=(0, 360)
        ))

        self.__front_index = 0
        self.__front_pos = self.data.path[0]
        self.__end_reached = False
        self.__counter = 0
        self.__points = []

        self.__current_loop = 0

        self.__path_length = 0
        for pos, point in enumerate(self.data.path):
            if pos < len(self.data.path) - 1:
                self.__path_length += ((point[0] - self.data.path[pos+1][0]) ** 2
                                       + (point[1] - self.data.path[pos+1][1]) ** 2) ** 0.5

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        self.__points = []

        next_position = self.__front_pos
        remaining_speed = self.__path_length / self.data.loop_duration * timedelta

        while remaining_speed and not self.__end_reached:
            if next_position == self.data.path[self.__front_index]:
                self.__points.append(next_position)
                self.__front_index += 1
            if self.__front_index >= len(self.data.path):
                if self.data.loop_count != -1:
                    self.__current_loop += 1
                    if self.__current_loop >= self.data.loop_count:
                        self.__end_reached = True
                        break
                self.__front_index = 0

            dx = self.data.path[self.__front_index][0] - next_position[0]
            dy = self.data.path[self.__front_index][1] - next_position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if remaining_speed >= distance:
                next_position = self.data.path[self.__front_index]
                remaining_speed -= distance
            else:
                next_position = (
                    next_position[0] + dx * remaining_speed / distance,
                    next_position[1] + dy * remaining_speed / distance
                )
                remaining_speed = 0

        self.__points.append(next_position)

        self.__front_pos = next_position

        if self.__end_reached:
            self.__counter += timedelta
            remaining_speed = self.data.line_length - self.__counter * (self.__path_length / self.data.loop_duration)
            self.emitter.data.particles_per_second = 10
            if remaining_speed <= 0:
                self.emitter.data.particles_per_second = 0
                if not self.emitter.particle_count():
                    self.done = True
                self.emitter.update(timedelta)
                return
            back_index = (self.__front_index - 1) if self.__front_index > 0 else 0
        else:
            remaining_speed = self.data.line_length
            back_index = (self.__front_index - 1) if self.__front_index > 0 else 0

        while remaining_speed:
            if next_position == self.data.path[back_index]:
                self.__points.insert(0, next_position)
                back_index -= 1
            if back_index < 0:
                break

            dx = self.data.path[back_index][0] - next_position[0]
            dy = self.data.path[back_index][1] - next_position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if remaining_speed >= distance:
                next_position = self.data.path[back_index]
                remaining_speed -= distance
            else:
                next_position = (
                    next_position[0] + dx * remaining_speed / distance,
                    next_position[1] + dy * remaining_speed / distance
                )
                remaining_speed = 0

        self.__points.insert(0, next_position)

        for i in range(len(self.__points)):
            self.__points[i] = (self.data.parent_pos[0] + self.__points[i][0] * self.data.parent_size[0],
                                self.data.parent_pos[1] + self.__points[i][1] * self.data.parent_size[1])

        self.emitter.data.position = (self.data.parent_pos[0] + self.__front_pos[0] * self.data.parent_size[0],
                                      self.data.parent_pos[1] + self.__front_pos[1] * self.data.parent_size[1])
        self.emitter.update(timedelta)
        return

    def render(self, surface: pygame.Surface):
        draw_gradient_lines(surface, (255, 255, 255, 0), (255, 255, 255, 255), False,
                            self.__points, 1)
        self.emitter.render(surface)


class WinCelebrationEffect(Effect):
    def __init__(self):
        super().__init__(DefaultEffectData())

        self.emitters = []

        self.emitters.append(ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=1.5,

                texture=LineTexture(),

                initial_color=(255, 255, 0),
                final_color=(218, 145, 0),

                initial_size=16,
                final_size=4,

                initial_speed=512,
                final_speed=0,

                gravity_multiplier=0.5,

                outline=False,
            ),
            position=(0, 0),
            particles_per_second=256,
            max_particles=99999,
            direction_of_emission=(155, 170)
        )))

        self.emitters.append(ParticleEmitter(ParticleEmitterData(
            particle_data=ParticleData(
                lifetime=1.5,

                texture=LineTexture(),

                initial_color=(255, 255, 0),
                final_color=(218, 145, 0),

                initial_size=16,
                final_size=4,

                initial_speed=512,
                final_speed=0,

                gravity_multiplier=0.5,

                outline=False,
            ),
            position=(0, 0),
            particles_per_second=256,
            max_particles=99999,
            direction_of_emission=(190, 205)
        )))

        self.__c_time = 0
        self.__duration = 2

    def update(self, timedelta: float, pos: Tuple[float, float], size: Tuple[float, float]):
        super().update(timedelta, pos, size)

        self.__c_time += timedelta

        if self.__c_time > self.__duration:
            for emitter in self.emitters:
                emitter.data.particles_per_second = 0
                if not emitter.particle_count():
                    self.emitters = []

        for emitter in self.emitters[:len(self.emitters) // 2]:
            emitter.data.position = (pos[0], pos[1] + size[1])
        for emitter in self.emitters[len(self.emitters) // 2:]:
            emitter.data.position = (pos[0] + size[0], pos[1] + size[1])
        for emitter in self.emitters:
            emitter.update(timedelta)

    def render(self, surface: pygame.Surface):
        for emitter in self.emitters:
            emitter.render(surface)


@dataclass
class VFXManagedObjectData:
    identifier: int
    rendered: bool
    parent_pos: Tuple[float, float]
    parent_size: Tuple[float, float]
    effects: List[Effect]


class VFXManager:
    __effects: Dict[int, VFXManagedObjectData]

    def __init__(self):
        self.__effects = {}

    def __check_obj(self, obj: object):
        if hash(obj) not in self.__effects:
            self.clear_effects(obj)
        return

    def add_effect(self, obj: object, effect: Effect, unique: bool = False):
        self.__check_obj(obj)
        if unique:
            remove_list = []
            for fx in self.__effects[hash(obj)].effects:
                if type(fx) == type(effect):
                    remove_list.append(fx)
            for fx in remove_list:
                self.__effects[hash(obj)].effects.remove(fx)
        self.__effects[hash(obj)].effects.append(effect)

    def remove_effect(self, obj: object, effect: Effect):
        self.__check_obj(obj)
        if effect in self.__effects[hash(obj)]:
            self.__effects[hash(obj)].effects.remove(effect)

    def clear_effects(self, obj: object):
        if hash(obj) in self.__effects.keys():
            self.__effects[hash(obj)].effects = []
        else:
            self.__effects[hash(obj)] = VFXManagedObjectData(hash(obj), True, (0, 0), (0, 0), [])

    def get_effects(self, obj: object) -> int:
        self.__check_obj(obj)
        return len(self.__effects[hash(obj)].effects)

    def transform_object(self, obj: object, pos: Tuple[float, float] = None, size: Tuple[float, float] = None):
        self.__check_obj(obj)
        if pos:
            self.__effects[hash(obj)].parent_pos = pos
        if size:
            self.__effects[hash(obj)].parent_size = size

    def update(self, timedelta: float):
        remove_obj_list = []
        for obj_hash in self.__effects.keys():
            remove_vfx_list = []
            if not self.__effects[obj_hash].rendered:
                remove_obj_list.append(obj_hash)
                continue
            for effect in self.__effects[obj_hash].effects:
                effect.update(timedelta, self.__effects[obj_hash].parent_pos, self.__effects[obj_hash].parent_size)
                if effect.done:
                    remove_vfx_list.append(effect)
            for effect in remove_vfx_list:
                self.__effects[obj_hash].effects.remove(effect)

        for obj_hash in remove_obj_list:
            del self.__effects[obj_hash]

    def render(self, obj: object, surface: pygame.Surface):
        self.__check_obj(obj)
        for effect in self.__effects[hash(obj)].effects:
            effect.render(surface)
        self.__effects[hash(obj)].rendered = True
