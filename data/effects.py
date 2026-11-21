import math
import random
from dataclasses import dataclass

import pygame as p

from data.image import swing_layers
from data.settings import (
    idle_shadow_offset,
    jump_shadow_offset,
    jump_visual_height,
    rain_delay,
    swing_angle,
    swing_speed,
    swing_upper_factor,
)

MAX_EFFECTS = 420
MAX_TRAIL_EFFECTS = 180
MAX_BUBBLE_EFFECTS = 120
TRAIL_LIFETIME = 0.45
TRAIL_SPACING_FACTOR = 1.4
TRAIL_RADIUS_FACTOR = 0.36
TRAIL_OFFSET_FACTOR = 1.15
BUBBLE_SPACING_FACTOR = {
    "fast": 2.2,
    "fat": 0.8,
}
BUBBLE_MODE_COLORS = {
    "fast": ((120, 240, 255), (255, 235, 120), (185, 255, 255)),
    "fat": ((255, 196, 40), (255, 236, 120), (255, 170, 40)),
}


def _shift_hue(rgb, degrees):
    r, g, b = (c / 255.0 for c in rgb[:3])
    mx, mn = max(r, g, b), min(r, g, b)
    diff = mx - mn
    if diff == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / diff) % 6
    elif mx == g:
        h = (b - r) / diff + 2
    else:
        h = (r - g) / diff + 4
    h = (h * 60.0 + degrees) % 360.0
    s = 0.0 if mx == 0 else diff / mx
    v = min(1.0, mx * 1.05)
    c = v * s
    x = c * (1.0 - abs((h / 60.0) % 2 - 1.0))
    m = v - c
    if h < 60:
        r1, g1, b1 = c, x, 0.0
    elif h < 120:
        r1, g1, b1 = x, c, 0.0
    elif h < 180:
        r1, g1, b1 = 0.0, c, x
    elif h < 240:
        r1, g1, b1 = 0.0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x
    return (
        max(0, min(255, round((r1 + m) * 255))),
        max(0, min(255, round((g1 + m) * 255))),
        max(0, min(255, round((b1 + m) * 255))),
    )


@dataclass
class Effect:
    kind: str
    pos: p.Vector2
    color: tuple
    life: float
    size: float
    velocity: p.Vector2
    age: float = 0.0
    delay: float = 0.0
    text: str = ""


class EffectsManager:
    def __init__(self, size, playfield_rect):
        self.scale = min(size[0] / 1440, size[1] / 900)
        self.bounds = p.Rect(playfield_rect)
        self.layer = p.Surface(size, p.SRCALPHA)
        self.items = []
        self.trails = {}
        self.swings = {}
        self.swing_cache = {}
        self.trail_phase = 0
        self.fonts = {}
        self.text_cache = {}
        self.time = 0.0
        self._trail_count = 0
        self._bubble_count = 0

    def clear(self):
        self.items.clear()
        self.trails.clear()
        self.swings.clear()
        self.swing_cache.clear()
        self.trail_phase = 0
        self.text_cache.clear()
        self.time = 0.0
        self._trail_count = 0
        self._bubble_count = 0

    def _drop_first(self, predicate):
        for index, item in enumerate(self.items):
            if predicate(item):
                return self.items.pop(index)
        return None

    @staticmethod
    def _is_limited(item):
        return item.kind == "trail" or item.kind.startswith("bubble_")

    def add(self, kind, pos, color, life, size, velocity=(0, 0), delay=0.0, text=""):
        if kind == "trail":
            if self._trail_count >= MAX_TRAIL_EFFECTS:
                dropped = self._drop_first(lambda item: item.kind == "trail")
                if dropped is not None:
                    self._trail_count -= 1
        elif kind.startswith("bubble_"):
            if self._bubble_count >= MAX_BUBBLE_EFFECTS:
                dropped = self._drop_first(lambda item: item.kind.startswith("bubble_"))
                if dropped is not None:
                    self._bubble_count -= 1

        if len(self.items) >= MAX_EFFECTS:
            dropped = self._drop_first(self._is_limited)
            if dropped is None:
                return
            if dropped.kind == "trail":
                self._trail_count = max(0, self._trail_count - 1)
            else:
                self._bubble_count = max(0, self._bubble_count - 1)

        self.items.append(
            Effect(
                kind=kind,
                pos=p.Vector2(pos),
                color=tuple(color)[:3],
                life=life,
                size=size,
                velocity=p.Vector2(velocity),
                delay=delay,
                text=text,
            )
        )
        if kind == "trail":
            self._trail_count += 1
        elif kind.startswith("bubble_"):
            self._bubble_count += 1

    def burst(self, pos, color, count=10, speed=150, delay=0.0):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            velocity = (
                p.Vector2(math.cos(angle), math.sin(angle))
                * random.uniform(speed * 0.35, speed)
                * self.scale
            )

            self.add(
                "drop",
                pos,
                color,
                life=random.uniform(0.2, 0.4),
                size=random.uniform(2, 5) * self.scale,
                velocity=velocity,
                delay=delay,
            )

    def pickup(self, pos, color):
        self.add("ring", pos, color, 0.32, 48 * self.scale)
        self.burst(pos, color, count=12)

    def punch(self, pos, color):
        self.add("star", pos, (255, 227, 130), 0.2, 40 * self.scale)
        self.burst(pos, color, count=16, speed=260)

    def explosion(self, pos, color, radius=40, delay=0.0):
        large = radius >= 80
        self.add(
            "pixel_ring",
            pos,
            (120, 64, 18),
            0.34,
            radius * 1.45,
            delay=delay,
        )
        self.add(
            "pixel_ring",
            pos,
            (255, 214, 90),
            0.3,
            radius * 1.3,
            delay=delay,
        )
        self.add(
            "burst_star",
            pos,
            (255, 200, 50),
            0.22,
            radius * (1.0 if large else 0.8),
            delay=delay,
        )
        if large:
            self.add(
                "pixel_ring",
                pos,
                (230, 120, 30),
                0.26,
                radius * 0.75,
                delay=delay,
            )
            self.add(
                "flash",
                pos,
                (255, 248, 205),
                0.15,
                radius * 0.22,
                delay=delay,
            )
        shard_colors = (
            (255, 200, 50),
            (230, 120, 30),
            (255, 240, 190),
            color,
        )
        count = 16 if large else 4
        size_scale = 1.6 if large else 1.0
        speed_scale = 1.8 if large else 1.0
        for index in range(count):
            angle = index * math.tau / count + random.uniform(-0.25, 0.25)
            speed = random.uniform(100, 260) * self.scale * speed_scale
            self.add(
                "shard",
                pos,
                shard_colors[index % len(shard_colors)],
                life=random.uniform(0.25, 0.45),
                size=random.uniform(3.0, 6.0) * self.scale * size_scale,
                velocity=(math.cos(angle) * speed, math.sin(angle) * speed),
                delay=delay,
            )
        puff_count = 5 if large else 1
        for _ in range(puff_count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(20, 70) * self.scale
            self.add(
                "puff",
                (
                    pos[0] + random.uniform(-radius * 0.18, radius * 0.18),
                    pos[1] + random.uniform(-radius * 0.18, radius * 0.18),
                ),
                (140, 74, 24),
                life=random.uniform(0.35, 0.6),
                size=radius * (0.38 if large else 0.3),
                velocity=(math.cos(angle) * speed, math.sin(angle) * speed),
                delay=delay,
            )

    def boom(self, pos, color, radius=200):
        self.explosion(pos, color, radius=radius)

    def rain(self, positions, color, radius):
        for index, pos in enumerate(positions):
            delay = rain_delay * index
            self.add(
                "pixel_ring",
                pos,
                color,
                0.2,
                radius,
                delay=delay,
            )
            self.explosion(pos, color, radius, delay=delay)

    def label(self, pos, color, text):
        self.add(
            "label",
            (pos[0], pos[1] - 26 * self.scale),
            color,
            life=1.0,
            size=max(16, round(26 * self.scale)),
            velocity=(0, -46 * self.scale),
            text=str(text),
        )

    def ripple(self, pos, color):
        self.add("ring", pos, color, 0.34, 30 * self.scale)
        self.add("ring", pos, color, 0.5, 44 * self.scale, delay=0.07)

    def _font(self, size):
        size = int(max(12, size))
        font = self.fonts.get(size)
        if font is None:
            font = p.font.SysFont("Comic Sans MS", size, bold=True)
            self.fonts[size] = font
        return font

    def _text_surface(self, text, color, size):
        key = (text, tuple(color)[:3], int(size))
        surface = self.text_cache.get(key)
        if surface is None:
            surface = self._font(size).render(text, True, tuple(color)[:3])
            if len(self.text_cache) >= 256:
                self.text_cache.clear()
            self.text_cache[key] = surface
        return surface

    @staticmethod
    def _special_mode(player):
        powerup = getattr(player, "powerup", None)
        if powerup == "fat":
            return "fat"
        if powerup == "speed":
            return "fast"
        return None

    @staticmethod
    def _bubble_size(mode, player):
        if mode == "fast":
            return max(3.0, player.radius * 0.3)
        return max(10.0, player.radius * 0.7)

    def _spawn_bubble(self, mode, pos, direction, player, size):
        if mode == "fat":
            color = (255, 196, 40)
        else:
            accent = random.choice(BUBBLE_MODE_COLORS[mode])
            player_color = tuple(player.color)[:3]
            color = tuple(
                round(accent[i] * 0.65 + player_color[i] * 0.35)
                for i in range(3)
            )
        perp_x, perp_y = -direction.y, direction.x

        if mode == "fast":
            jitter = random.uniform(-12.0, 12.0)
            velocity = (
                direction.x * 60.0 + perp_x * jitter,
                direction.y * 60.0 + perp_y * jitter,
            )
            life = 0.30
        else:
            velocity = (0.0, 0.0)
            life = 0.62

        self.add("bubble_" + mode, pos, color, life=life, size=size, velocity=velocity)

    def observe_players(self, players, dt):
        dt = max(0.0, min(dt, 0.1))
        shared_jump = any(getattr(other, "jumping", False) for other in players)

        for player in players:
            name = player.name
            current = p.Vector2(player.x, player.y)
            previous, accumulator = self.trails.get(name, (current.copy(), 0.0))

            wall_event = getattr(player, "wall_event", None)
            if wall_event is not None:
                player.wall_event = None
                self.ripple(wall_event, player.color)

            delta = current - previous
            painting = not (
                shared_jump
                or getattr(player, "jumping", False)
                or getattr(player, "beaten", False)
                or getattr(player, "broken_visual", False)
                or getattr(player, "jumping_to_wall", False)
                or getattr(player, "mode", (0, 0))[1] <= 0
            )

            distance = delta.length()
            teleport_limit = max(80.0, player.radius * 4.0)

            swing = self.swings.get(name)
            if swing is None:
                swing = {
                    "phase": 0.0 if name == "Player_A" else math.pi,
                    "angle": 0.0,
                }
                self.swings[name] = swing
            if 0.01 < distance < teleport_limit:
                swing["phase"] += dt * swing_speed
                target = math.sin(swing["phase"]) * swing_angle
            else:
                swing["phase"] = 0.0 if name == "Player_A" else math.pi
                target = 0.0
            swing["angle"] += (target - swing["angle"]) * min(1.0, dt * 14.0)

            if (
                not painting
                or distance <= 0.01
                or distance >= teleport_limit
            ):
                if not painting or distance >= teleport_limit:
                    accumulator = 0.0
            else:
                direction = delta / distance
                special = self._special_mode(player)
                if special is None:
                    circle_radius = max(4.0, player.radius * TRAIL_RADIUS_FACTOR)
                    spacing = max(8.0, circle_radius * TRAIL_SPACING_FACTOR)
                else:
                    circle_radius = self._bubble_size(special, player)
                    spacing = max(
                        8.0, circle_radius * BUBBLE_SPACING_FACTOR[special]
                    )
                offset = 0.0 if special == "fat" else player.radius * TRAIL_OFFSET_FACTOR
                total = accumulator + distance
                hue_offsets = (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0)

                while total >= spacing:
                    total -= spacing
                    sample_pos = current - direction * total
                    spawn_pos = sample_pos - direction * offset
                    if special is None:
                        hue_shift = hue_offsets[self.trail_phase % len(hue_offsets)]
                        self.trail_phase += 1
                        trail_color = _shift_hue(player.color, hue_shift)
                        self.add(
                            "trail",
                            spawn_pos,
                            trail_color,
                            life=TRAIL_LIFETIME,
                            size=circle_radius,
                        )
                    else:
                        self._spawn_bubble(
                            special, spawn_pos, direction, player, circle_radius
                        )

                accumulator = total

            self.trails[name] = (current.copy(), accumulator)

    def update(self, dt):
        dt = max(0.0, dt)
        self.time += dt
        alive = []

        for effect in self.items:
            active_dt = dt

            if effect.delay > 0:
                effect.delay -= dt

                if effect.delay > 0:
                    alive.append(effect)
                    continue

                active_dt = -effect.delay
                effect.delay = 0.0

            effect.age += active_dt

            if effect.age >= effect.life:
                continue

            effect.pos += effect.velocity * active_dt

            if effect.kind == "drop":
                effect.velocity *= math.exp(-5 * active_dt)
            elif effect.kind == "shard":
                effect.velocity *= math.exp(-4 * active_dt)
            elif effect.kind == "puff":
                effect.velocity *= math.exp(-2.5 * active_dt)
            elif effect.kind == "bubble_fast":
                effect.velocity *= math.exp(-4 * active_dt)

            alive.append(effect)

        self.items = alive
        trails = bubbles = 0
        for effect in alive:
            if effect.kind == "trail":
                trails += 1
            elif effect.kind.startswith("bubble_"):
                bubbles += 1
        self._trail_count = trails
        self._bubble_count = bubbles

    def draw_player(self, target, player):
        sprite = self._swinging_sprite(player)
        lift = 0.0

        if getattr(player, "jumping", False):
            progress = min(1.0, max(0.0, getattr(player, "jump_progress", 0.0)))
            lift = math.sin(math.pi * progress) * jump_visual_height

        if getattr(player, "squashing", False):
            duration = max(0.001, getattr(player, "squash_duration", 0.32))
            progress = min(1.0, max(0.0, getattr(player, "squash_elapsed", 0.0) / duration))
            envelope = math.sin(math.pi * progress)
            strength = getattr(player, "squash_strength", 1.0) * envelope
            if strength > 0.001:
                width = max(1, round(sprite.get_width() * (1.0 + 0.24 * strength)))
                height = max(1, round(sprite.get_height() * (1.0 - 0.2 * strength)))
                sprite = p.transform.smoothscale(sprite, (width, height))

        rect = sprite.get_rect(center=(round(player.x), round(player.y - lift)))
        target.blit(sprite, rect)

        if getattr(player, "broken_visual", False):
            self._draw_broken_stars(target, player, lift)

        self._draw_direction_marker(target, player, lift)

    def _swinging_sprite(self, player):
        icon = player.icon
        angle = self.swings.get(player.name, {}).get("angle", 0.0)
        if abs(angle) < 0.5:
            return icon
        upper_angle = round(angle * swing_upper_factor)
        lower_angle = round(angle)
        key = (player.name, id(icon), icon.get_size(), upper_angle, lower_angle)
        sprite = self.swing_cache.get(key)
        if sprite is None:
            upper, lower, pivot = swing_layers(icon)
            canvas_size = (icon.get_width() + 60, icon.get_height() + 60)
            offset_x = (canvas_size[0] - icon.get_width()) // 2
            offset_y = (canvas_size[1] - icon.get_height()) // 2
            pivot_final = (offset_x + pivot[0], offset_y + pivot[1])
            upper_rotated = self._rotate_layer(
                upper, upper_angle, pivot, canvas_size, pivot_final
            )
            lower_rotated = self._rotate_layer(
                lower, lower_angle, pivot, canvas_size, pivot_final
            )
            sprite = p.Surface(canvas_size, p.SRCALPHA)
            sprite.blit(upper_rotated, (0, 0))
            sprite.blit(lower_rotated, (0, 0))
            self.swing_cache[key] = sprite
        return sprite

    @staticmethod
    def _rotate_layer(layer, angle, pivot, canvas_size, pivot_final):
        temp = p.Surface(canvas_size, p.SRCALPHA)
        temp.blit(
            layer,
            (
                canvas_size[0] // 2 - pivot[0],
                canvas_size[1] // 2 - pivot[1],
            ),
        )
        rotated = p.transform.rotozoom(temp, angle, 1.0)
        result = p.Surface(canvas_size, p.SRCALPHA)
        result.blit(rotated, rotated.get_rect(center=pivot_final))
        return result

    def _draw_broken_stars(self, target, player, lift=0.0):
        center_x = player.x
        center_y = player.y - lift
        half = max(player.icon.get_width(), player.icon.get_height()) * 0.5
        orbit = half + 10 * self.scale
        count = 5
        old_clip = target.get_clip()
        target.set_clip(old_clip.clip(self.bounds))
        try:
            for index in range(count):
                angle = self.time * 2.6 + index * math.tau / count
                wobble = math.sin(self.time * 5.0 + index * 1.7) * 3.0 * self.scale
                star_x = center_x + math.cos(angle) * (orbit + wobble)
                star_y = center_y + math.sin(angle) * (orbit + wobble * 0.6)
                radius = (
                    5.5 + 1.5 * math.sin(self.time * 7.0 + index * 2.1)
                ) * self.scale
                points = []
                for point_index in range(16):
                    point_angle = point_index * math.pi / 8
                    length = radius if point_index % 2 == 0 else radius * 0.42
                    points.append(
                        (
                            star_x + math.cos(point_angle) * length,
                            star_y + math.sin(point_angle) * length,
                        )
                    )
                p.draw.polygon(target, (196, 138, 26), points)
        finally:
            target.set_clip(old_clip)

    def _draw_direction_marker(self, target, player, lift=0.0):
        if getattr(player, "mode", (0, 0))[1] <= 0:
            return
        if getattr(player, "jumping_to_wall", False):
            return

        direction = math.radians(player.angle)
        ux, uy = math.cos(direction), math.sin(direction)
        px, py = -uy, ux
        base_y = player.y - lift
        extent = max(
            player.radius,
            player.icon.get_width() / 2,
            player.icon.get_height() / 2,
        )
        origin = (
            player.x + ux * (extent + 0.5 * self.scale),
            base_y + uy * (extent + 0.5 * self.scale),
        )

        length = 16 * self.scale
        head_length = 7.5 * self.scale
        head_half = 7.5 * self.scale
        shaft_half = 4.5 * self.scale
        shaft_end = length - head_length

        def to_world(local_x, local_y):
            return (
                origin[0] + ux * local_x + px * local_y,
                origin[1] + uy * local_x + py * local_y,
            )

        body = (
            to_world(0, -shaft_half),
            to_world(shaft_end, -shaft_half),
            to_world(shaft_end, -head_half),
            to_world(length, 0),
            to_world(shaft_end, head_half),
            to_world(shaft_end, shaft_half),
            to_world(0, shaft_half),
        )

        pulse = 0.5 + 0.5 * math.sin(self.time * 6.5)
        light = 0.2 + 0.8 * pulse
        gold = tuple(
            round(low + (high - low) * light)
            for low, high in zip((176, 122, 26), (255, 224, 118))
        )

        old_clip = target.get_clip()
        target.set_clip(old_clip.clip(self.bounds))
        try:
            p.draw.polygon(target, gold, body)
            p.draw.polygon(
                target, (12, 12, 14), body, max(2, round(1.8 * self.scale))
            )
        finally:
            target.set_clip(old_clip)

    def draw_labels(self, target):
        old_clip = target.get_clip()
        target.set_clip(old_clip.clip(self.bounds))
        try:
            for effect in self.items:
                if effect.kind != "label" or effect.delay > 0:
                    continue

                progress = effect.age / effect.life
                fade = 1.0 - max(0.0, (progress - 0.45) / 0.55)
                alpha = max(0, min(255, round(255 * fade)))
                if alpha <= 0:
                    continue

                font_size = effect.size
                body = self._text_surface(effect.text, effect.color, font_size)
                shadow = self._text_surface(effect.text, (16, 21, 33), font_size)
                body.set_alpha(alpha)
                shadow.set_alpha(min(alpha, 190))

                center = (round(effect.pos.x), round(effect.pos.y))
                body_rect = body.get_rect(center=center)
                target.blit(shadow, body_rect.move(2, 2))
                target.blit(body, body_rect)
        finally:
            target.set_clip(old_clip)

    def draw(self, target, players=()):
        self.layer.fill((0, 0, 0, 0), self.bounds)
        self.layer.set_clip(self.bounds)

        for effect in self.items:
            if effect.delay > 0 or effect.kind == "label":
                continue

            progress = effect.age / effect.life
            alpha = round(220 * (1.0 - progress))
            color = (*effect.color, alpha)
            center = (round(effect.pos.x), round(effect.pos.y))

            if effect.kind == "drop":
                radius = max(1, round(effect.size * (1 - progress * 0.6)))
                p.draw.circle(self.layer, color, center, radius)

            elif effect.kind == "trail":
                remaining = max(0.0, 1.0 - progress)
                eased_scale = remaining ** 0.85
                radius = round(effect.size * eased_scale)
                if radius < 1:
                    continue
                trail_alpha = max(0, min(230, round(230 * (remaining ** 0.7))))
                r, g, b = effect.color
                shifted = _shift_hue((r, g, b), progress * 38.0)
                sr, sg, sb = shifted
                glow_radius = radius + max(1, round(2.5 * self.scale))
                glow_color = (
                    sr,
                    sg,
                    sb,
                    max(0, round(trail_alpha * 0.28)),
                )
                body_color = (
                    min(255, sr + round((255 - sr) * 0.22)),
                    min(255, sg + round((255 - sg) * 0.22)),
                    min(255, sb + round((255 - sb) * 0.22)),
                    trail_alpha,
                )
                core_color = (
                    min(255, sr + round((255 - sr) * 0.72)),
                    min(255, sg + round((255 - sg) * 0.72)),
                    min(255, sb + round((255 - sb) * 0.72)),
                    min(245, round(trail_alpha * 0.95)),
                )
                ring_color = (
                    max(0, round(r * 0.45)),
                    max(0, round(g * 0.45)),
                    max(0, round(b * 0.45)),
                    min(240, round(trail_alpha * 0.85)),
                )
                p.draw.circle(self.layer, glow_color, center, glow_radius)
                p.draw.circle(self.layer, body_color, center, radius)
                if radius >= 3:
                    p.draw.circle(
                        self.layer,
                        core_color,
                        (center[0] - max(1, radius // 4), center[1] - max(1, radius // 4)),
                        max(1, round(radius * 0.45)),
                    )
                if radius >= 2:
                    p.draw.circle(self.layer, ring_color, center, radius, max(1, round(1.5 * self.scale)))

            elif effect.kind.startswith("bubble_"):
                self._draw_bubble(effect, progress, center)

            elif effect.kind == "ring":
                eased = 1 - (1 - progress) ** 3
                radius = max(1, round(effect.size * eased))
                width = min(radius, max(1, round(3 * self.scale)))
                p.draw.circle(self.layer, color, center, radius, width)

            elif effect.kind == "pixel_ring":
                eased = 1 - (1 - progress) ** 3
                radius = max(1, round(effect.size * eased))
                width = min(radius, max(1, round(3 * self.scale)))
                points = (
                    (center[0], center[1] - radius),
                    (center[0] + radius, center[1]),
                    (center[0], center[1] + radius),
                    (center[0] - radius, center[1]),
                )
                p.draw.polygon(self.layer, color, points, width)

            elif effect.kind == "flash":
                size = max(1, round(effect.size * (1.0 - progress * 0.3)))
                thickness = max(1, round(max(2, effect.size * 0.35)))
                p.draw.rect(
                    self.layer,
                    (80, 40, 12, alpha),
                    (center[0] - size - 2, center[1] - thickness - 2,
                     size * 2 + 4, thickness * 2 + 4),
                )
                p.draw.rect(
                    self.layer,
                    (80, 40, 12, alpha),
                    (center[0] - thickness - 2, center[1] - size - 2,
                     thickness * 2 + 4, size * 2 + 4),
                )
                p.draw.rect(
                    self.layer,
                    color,
                    (center[0] - size, center[1] - thickness, size * 2, thickness * 2),
                )
                p.draw.rect(
                    self.layer,
                    color,
                    (center[0] - thickness, center[1] - size, thickness * 2, size * 2),
                )
                core = max(1, round(max(2, effect.size * 0.22)))
                p.draw.rect(
                    self.layer,
                    (255, 255, 235, alpha),
                    (center[0] - core, center[1] - core, core * 2, core * 2),
                )

            elif effect.kind == "shard":
                size = max(1, round(effect.size * (1.0 - progress * 0.55)))
                rect = p.Rect(0, 0, size * 2, size * 2)
                rect.center = center
                p.draw.rect(self.layer, color, rect)
                if size >= 2:
                    p.draw.rect(
                        self.layer,
                        (70, 36, 12, alpha),
                        rect,
                        max(1, round(self.scale)),
                    )

            elif effect.kind == "puff":
                radius = max(1, round(effect.size * (0.45 + progress * 1.1)))
                points = (
                    (center[0], center[1] - radius),
                    (center[0] + radius, center[1]),
                    (center[0], center[1] + radius),
                    (center[0] - radius, center[1]),
                )
                p.draw.polygon(self.layer, (80, 40, 12, alpha), points)
                if radius > 2:
                    inner = max(1, round(radius * 0.7))
                    inner_points = (
                        (center[0], center[1] - inner),
                        (center[0] + inner, center[1]),
                        (center[0], center[1] + inner),
                        (center[0] - inner, center[1]),
                    )
                    p.draw.polygon(self.layer, color, inner_points)
                    core = max(1, round(radius * 0.3))
                    p.draw.rect(
                        self.layer,
                        (255, 190, 60, alpha),
                        (center[0] - core, center[1] - core, core * 2, core * 2),
                    )

            elif effect.kind == "burst_star":
                radius = effect.size * (0.75 + progress * 0.6)
                points = []
                for index in range(8):
                    angle = index * math.pi / 4 + progress * 0.3
                    length = radius if index % 2 == 0 else radius * 0.32
                    points.append(
                        (
                            center[0] + math.cos(angle) * length,
                            center[1] + math.sin(angle) * length,
                        )
                    )
                p.draw.polygon(self.layer, (80, 40, 12, alpha), points)
                inner = []
                for index in range(8):
                    angle = index * math.pi / 4 + progress * 0.3
                    length = (
                        radius * 0.72 if index % 2 == 0 else radius * 0.22
                    )
                    inner.append(
                        (
                            center[0] + math.cos(angle) * length,
                            center[1] + math.sin(angle) * length,
                        )
                    )
                p.draw.polygon(self.layer, color, inner)
                core = max(1, round(radius * 0.28))
                p.draw.rect(
                    self.layer,
                    (255, 255, 235, alpha),
                    (center[0] - core, center[1] - core, core * 2, core * 2),
                )

            elif effect.kind == "star":
                radius = effect.size * (0.65 + progress * 0.35)
                points = []

                for index in range(16):
                    angle = index * math.pi / 8
                    length = radius if index % 2 == 0 else radius * 0.4
                    points.append(
                        (
                            center[0] + math.cos(angle) * length,
                            center[1] + math.sin(angle) * length,
                        )
                    )

                p.draw.polygon(self.layer, color, points)

        for player in players:
            self._draw_player_shadow(player)

        for player in players:
            if getattr(player, "bandi", False):
                self._draw_bandi(player)

        self.layer.set_clip(None)
        target.blit(self.layer, self.bounds.topleft, self.bounds)

    def _draw_player_shadow(self, player):
        sprite = player.icon

        if getattr(player, "jumping", False):
            progress = min(1.0, max(0.0, getattr(player, "jump_progress", 0.0)))
            lift = math.sin(math.pi * progress)
            offset = jump_shadow_offset
            width_factor = 0.85 - 0.34 * lift
            alpha = round(135 - 60 * lift)
        else:
            offset = idle_shadow_offset
            width_factor = 0.85
            alpha = 135

        width = max(12, round(sprite.get_width() * width_factor))
        height = max(6, round(width * 0.6))
        center = (
            round(player.x),
            round(player.y + sprite.get_height() * offset),
        )

        outer = p.Rect(0, 0, width, height)
        outer.center = center
        p.draw.ellipse(
            self.layer,
            (8, 12, 20, max(0, alpha // 3)),
            outer.inflate(12, 6),
        )
        p.draw.ellipse(self.layer, (8, 12, 20, max(0, alpha)), outer)

    def _draw_bubble(self, effect, progress, center):
        remaining = max(0.0, 1.0 - progress)
        if remaining <= 0.0:
            return

        mode = effect.kind[len("bubble_"):]
        r, g, b = effect.color
        alpha = max(0, min(235, round(235 * (remaining ** 0.7))))

        if mode == "fast":
            speed = math.hypot(effect.velocity.x, effect.velocity.y)
            if speed > 0.001:
                ux, uy = effect.velocity.x / speed, effect.velocity.y / speed
            else:
                ux, uy = 1.0, 0.0

            px, py = -uy, ux
            length = effect.size * (1.1 + 1.4 * remaining)
            width = effect.size * (0.35 + 0.25 * remaining)
            tip = (center[0] + ux * length, center[1] + uy * length)
            tail = (center[0] - ux * length * 0.7, center[1] - uy * length * 0.7)
            left = (center[0] + px * width, center[1] + py * width)
            right = (center[0] - px * width, center[1] - py * width)
            streak = (
                min(255, r + round((255 - r) * 0.35)),
                min(255, g + round((255 - g) * 0.35)),
                min(255, b + round((255 - b) * 0.35)),
                alpha,
            )
            p.draw.polygon(self.layer, streak, (tip, left, tail, right))
            p.draw.line(
                self.layer,
                (255, 255, 255, min(255, alpha)),
                tail,
                tip,
                max(1, round(1.2 * self.scale)),
            )

        elif mode == "fat":
            radius = max(2, round(effect.size * (0.28 + 0.72 * progress)))
            border = max(1, round(1.4 * self.scale))
            thickness = max(2, round(radius * 0.38))
            p.draw.circle(
                self.layer,
                (112, 62, 6, alpha),
                center,
                radius + border,
                thickness + 2 * border,
            )
            p.draw.circle(self.layer, (255, 196, 40, alpha), center, radius, thickness)
            shine = max(1, round(thickness * 0.32))
            if thickness >= 4:
                p.draw.circle(
                    self.layer,
                    (255, 246, 168, round(alpha * 0.9)),
                    center,
                    max(1, radius - thickness // 2),
                    shine,
                )

    def _draw_bandi(self, player):
        pulse = (math.sin(self.time * 9) + 1) * 0.5
        remaining = getattr(player, "bandi_time_left", None)
        expiring = remaining is not None and 0.0 < remaining <= 2.5
        urgency = 0.0 if not expiring else 1.0 - remaining / 2.5
        boost = pulse * (4 + 7 * urgency)
        extent = max(
            player.radius,
            player.icon.get_width() / 2,
            player.icon.get_height() / 2,
        )
        radius = round(extent + (5 + boost) * self.scale)
        center = (round(player.x), round(player.y))

        ring_alpha = round(130 + pulse * 90)
        if expiring:
            ring_alpha = min(255, ring_alpha + round(45 * urgency))

        p.draw.circle(
            self.layer,
            (*tuple(player.color)[:3], ring_alpha),
            center,
            radius,
            max(1, round((3 + urgency) * self.scale)),
        )
