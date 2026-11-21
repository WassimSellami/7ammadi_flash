import pygame as p
from data.color import Color
from data.settings import d_width, d_height

BRUSH_LABEL = "bria-rmbg3-cutout"
ICON_LABEL = "bria-rmbg3-cutout"
ICON_SIZE = (80, 80)
ICON_MARGIN = 4


class Image:
    def __init__(self, label, size=(80, 80)):
        self.size = size
        self.label = label

    def load(self):
        surface = p.image.load(f"data/icons/{self.label}.png")
        if p.display.get_surface() is not None:
            return surface.convert_alpha()
        return surface

    def transform(self):
        key = (self.label, self.size)
        surface = _transform_cache.get(key)
        if surface is None:
            surface = p.transform.scale(self.load(), self.size)
            _transform_cache[key] = surface
        return surface.copy()

    @staticmethod
    def background():
        background = _background_cache.get("scaled")
        if background is None:
            source = _background_cache.get("source")
            if source is None:
                source = p.image.load("data/icons/bg.jpg").convert()
                _background_cache["source"] = source
            background = p.transform.scale(source, (d_width, d_height))
            _background_cache["scaled"] = background
        return background.copy()

    @staticmethod
    def normal(player):
        if player == "Player_A":
            return normal_icon_A
        return normal_icon_B

    @staticmethod
    def prepare_icons():
        prepare_icons()


_brush_source = None
_icon_cache = {}
_swing_layer_cache = {}
_transform_cache = {}
_background_cache = {}
normal_icon_A = None
normal_icon_B = None


def _main_sprite_rect(surface):
    rects = p.mask.from_surface(surface).get_bounding_rects()
    if not rects:
        return surface.get_rect()
    return max(rects, key=lambda rect: rect.width * rect.height)


def _load_brush_source():
    global _brush_source
    if _brush_source is None:
        surface = p.image.load(f"data/icons/{BRUSH_LABEL}.png")
        if p.display.get_surface() is not None:
            surface = surface.convert_alpha()
        rect = _main_sprite_rect(surface)
        _brush_source = surface.subsurface(rect).copy()
    return _brush_source


def _is_paint_green(red, green, blue, alpha):
    return alpha > 16 and green > 90 and green > red * 1.35 and green > blue * 1.35


def _recolor_paint(surface, color):
    out = surface.copy()
    pixels = p.PixelArray(out)
    target = (color[0], color[1], color[2])
    width, height = out.get_size()
    try:
        for x in range(width):
            for y in range(height):
                red, green, blue, alpha = out.unmap_rgb(pixels[x, y])
                if _is_paint_green(red, green, blue, alpha):
                    pixels[x, y] = out.map_rgb((target[0], target[1], target[2], alpha))
    finally:
        del pixels
    return out


def _fit_icon(surface):
    width, height = surface.get_size()
    available_width = max(1, ICON_SIZE[0] - 2 * ICON_MARGIN)
    available_height = max(1, ICON_SIZE[1] - 2 * ICON_MARGIN)
    scale = min(available_width / width, available_height / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    scaled = p.transform.smoothscale(surface, new_size)
    icon = p.Surface(ICON_SIZE, p.SRCALPHA)
    icon.blit(scaled, scaled.get_rect(center=(ICON_SIZE[0] // 2, ICON_SIZE[1] // 2)))
    return icon


def _bristle_top(icon):
    width, height = icon.get_size()
    threshold = max(4, width // 4)
    for y in range(height):
        cream = 0
        for x in range(width):
            red, green, blue, alpha = icon.get_at((x, y))
            if (
                alpha > 16
                and red > 200
                and green > 185
                and blue > 150
                and blue < 235
            ):
                cream += 1
        if cream >= threshold:
            return y
    return int(height * 0.62)


def swing_layers(icon):
    key = (id(icon), icon.get_size())
    layers = _swing_layer_cache.get(key)
    if layers is not None:
        return layers
    width, height = icon.get_size()
    split_y = _bristle_top(icon)
    overlap = max(4, height // 12)
    upper = p.Surface((width, height), p.SRCALPHA)
    upper.blit(icon, (0, 0), p.Rect(0, 0, width, min(height, split_y + overlap)))
    lower = p.Surface((width, height), p.SRCALPHA)
    lower.blit(icon, (0, split_y), p.Rect(0, split_y, width, height - split_y))
    pivot = (width // 2, max(0, split_y - 5))
    layers = (upper, lower, pivot)
    _swing_layer_cache[key] = layers
    return layers


def _player_icon(color):
    key = tuple(color)[:3]
    icon = _icon_cache.get(key)
    if icon is None:
        icon = _fit_icon(_recolor_paint(_load_brush_source(), key))
        _icon_cache[key] = icon
    return icon


def prepare_icons():
    global normal_icon_A, normal_icon_B
    normal_icon_A = _player_icon(Color.color_A)
    normal_icon_B = _player_icon(Color.color_B)


def load_window_icon():
    try:
        icon = p.image.load(f"data/icons/{ICON_LABEL}.ico")
        if p.display.get_surface() is not None:
            icon = icon.convert_alpha()
        if icon.get_at((0, 0))[3] == 0:
            return icon
    except (p.error, FileNotFoundError, OSError):
        pass
    return _fit_icon(_load_brush_source())


prepare_icons()
