import math
from typing import Tuple, Any

import pygame


def get_brightness(color: Tuple[int, int, int] | Tuple[int, int, int, int], perceived: bool = True) -> int:
    if perceived:
        return int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
    else:
        return sum(color[:2]) // 3


def get_outline(surface: pygame.Surface, outline_color: Tuple[int, int, int] = (0, 0, 0),
                resize: bool = False) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface)
    colorkey = (255, 255, 255)
    colorkey = colorkey if outline_color != colorkey else (0, 0, 0)
    mask_surf = mask.to_surface(setcolor=outline_color, unsetcolor=colorkey)
    mask_surf.set_colorkey(colorkey)

    if resize:
        outline = pygame.Surface((surface.get_width() + 2, surface.get_height() + 2), pygame.SRCALPHA)
        outline.blit(mask_surf, (2, 1))
        outline.blit(mask_surf, (0, 1))
        outline.blit(mask_surf, (1, 2))
        outline.blit(mask_surf, (1, 0))
        outline.blit(surface, (1, 1))
    else:
        outline = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        outline.blit(mask_surf, (1, 0))
        outline.blit(mask_surf, (-1, 0))
        outline.blit(mask_surf, (0, 1))
        outline.blit(mask_surf, (0, -1))
        outline.blit(surface, (0, 0))
    return outline


# taken from https://stackoverflow.com/a/52050040
def vertical(size: Tuple[int, int], start_color: Tuple[int, int, int, int], end_color: Tuple[int, int, int, int]):
    """
    Draws a vertical linear gradient filling the entire surface. Returns a
    surface filled with the gradient (numeric is only 2-3 times faster).
    """
    height = int(size[1])
    surface = pygame.Surface((1, height)).convert_alpha()
    dd = 1.0 / height
    sr, sg, sb, sa = start_color
    er, eg, eb, ea = (int(i) for i in end_color)
    rm = (er - sr) * dd
    gm = (eg - sg) * dd
    bm = (eb - sb) * dd
    am = (ea - sa) * dd
    for y in range(height):
        try:
            surface.set_at((0, y),
                           (int(sr + rm * y),
                            int(sg + gm * y),
                            int(sb + bm * y),
                            int(sa + am * y))
                           )
        except ValueError:
            continue
    return pygame.transform.scale(surface, size)


def draw_gradient_lines(surface: pygame.Surface, start_color: Any, end_color: Any, closed: bool, points: list,
                        width: int = 1):
    if closed:
        points.append(points[0])
    path_length = 0
    for pos, point in enumerate(points):
        if pos < len(points) - 1:
            path_length += ((point[0] - points[pos + 1][0]) ** 2 + (point[1] - points[pos + 1][1]) ** 2) ** 0.5

    walked_path_length = 0
    for pos, point in enumerate(points):
        if pos < len(points) - 1:
            line_length = ((point[0] - points[pos + 1][0]) ** 2 + (point[1] - points[pos + 1][1]) ** 2) ** 0.5

            sr, sg, sb, sa = start_color
            er, eg, eb, ea = end_color
            cr = sr + (er - sr) * walked_path_length / (path_length or 0.01)
            cg = sg + (eg - sg) * walked_path_length / (path_length or 0.01)
            cb = sb + (eb - sb) * walked_path_length / (path_length or 0.01)
            ca = sa + (ea - sa) * walked_path_length / (path_length or 0.01)
            line_start_color = (cr, cg, cb, ca)

            walked_path_length += line_length

            sr, sg, sb, sa = start_color
            er, eg, eb, ea = end_color
            cr = sr + (er - sr) * walked_path_length / (path_length or 0.01)
            cg = sg + (eg - sg) * walked_path_length / (path_length or 0.01)
            cb = sb + (eb - sb) * walked_path_length / (path_length or 0.01)
            ca = sa + (ea - sa) * walked_path_length / (path_length or 0.01)
            line_end_color = (cr, cg, cb, ca)

            line = vertical((width, int(line_length) or 1), line_start_color, line_end_color)

            y_diff = (points[pos + 1][1] - point[1])
            angle = math.degrees(math.atan((points[pos + 1][0] - point[0]) / (y_diff or 0.01)))
            if y_diff < 0:
                angle += 180
            line = pygame.transform.rotate(line, angle)

            pivot = point
            offset = pygame.math.Vector2(line_length / 2 * math.sin(math.radians(angle)),
                                         line_length / 2 * math.cos(math.radians(angle)))
            rect = line.get_rect(center=(pivot + offset))
            position = rect.topleft
            surface.blit(line, position)
