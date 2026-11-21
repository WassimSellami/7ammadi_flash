import math
import pygame as p
import data.sound as sound
from data.settings import *
from random import randint, choice
from data.image import Image
from data.color import Color


PRIZE_LABELS = {
    "speed": "SPEED UP",
    "fat": "FAT BOOST",
    "rain": "COLOR RAIN",
    "boom": "BOOM!",
    "bandi": "BANDI!",
    "follow_me": "FOLLOW ME",
}

# Only these prizes change the player's movement mode. Utility prizes such as
# rain/boom/follow_me must leave an active speed, fat, or bandi mode untouched.
MODE_PRIZES = frozenset(("speed", "fat", "bandi"))

GLOW = tuple(prize_glow_color)[:3]
GLOW_DARK = tuple(max(0, round(channel * 0.42)) for channel in GLOW)
GLOW_LIGHT = tuple(
    min(255, round(channel + (255 - channel) * 0.66)) for channel in GLOW
)
ICON_TINT = (255, 205, 94)


class Prize:
    x = None
    y = None
    rectangle = None
    radius = p_radius
    chosen_prize = None
    rain_list = None
    is_allowed = False
    icon = None
    sound = False

    def __init__(self):
        self.chosen_prizes = {}
        self.age_ms = 0.0
        self.lifetime_ms = prize_time * 1000
        self.halo_angle = 0.0
        self.icon_cache = {}
        self.outline_cache = {}
        self.halo_cache = {}
        self.rain_pending = []
        self.rain_accum = 0.0
        self.rain_color = Color.white
        self.rain_screen = None

    def update(self, dt):
        dt = max(0.0, dt)
        if self.is_allowed:
            self.age_ms += dt * 1000.0
            self.halo_angle = (self.halo_angle + dt * 120.0) % 360.0
        self._update_rain(dt)

    def _update_rain(self, dt):
        if not self.rain_pending:
            return
        self.rain_accum += dt
        while self.rain_pending and self.rain_accum >= rain_delay:
            self.rain_accum -= rain_delay
            self._paint_rain_drop()

    def _paint_rain_drop(self):
        if not self.rain_pending:
            return
        if self.rain_screen is None:
            self.rain_pending.clear()
            return

        x, y = self.rain_pending.pop()
        background = self.rain_screen.background
        background.set_clip(playfield_rect)
        p.draw.circle(background, self.rain_color, (x, y), normal_radius)
        background.set_clip(None)

    def clear_rain(self):
        self.rain_pending.clear()
        self.rain_accum = 0.0
        self.rain_screen = None

    def is_expired(self):
        return self.age_ms >= self.lifetime_ms

    def is_expiring(self):
        return self.lifetime_ms - self.age_ms <= 2600

    def show_prize(self, screen):
        if self.icon is None or self.rectangle is None:
            return

        age = self.age_ms / 1000.0
        progress = min(1.0, age / 0.35)
        c1 = 1.70158
        c3 = c1 + 1.0
        pop = 1.0 + c3 * (progress - 1.0) ** 3 + c1 * (progress - 1.0) ** 2
        scale = 0.35 + 0.65 * pop

        expiring = self.is_expiring()
        if expiring:
            pulse = 0.5 + 0.5 * math.sin(age * 10.0)
            scale += 0.07 * pulse

        width = max(1, round(self.icon.get_width() * scale))
        height = max(1, round(self.icon.get_height() * scale))
        size_key = (width, height)
        icon = self.icon_cache.get(size_key)
        if icon is None:
            icon = p.transform.smoothscale(self.icon, size_key)
            if len(self.icon_cache) >= 96:
                self.icon_cache.clear()
                self.outline_cache.clear()
            self.icon_cache[size_key] = icon
        outline = self.outline_cache.get(size_key)
        if outline is None:
            outline = p.transform.smoothscale(self.icon, size_key)
            outline.fill((0, 0, 0), special_flags=p.BLEND_RGB_MULT)
            self.outline_cache[size_key] = outline
        center = (round(self.x), round(self.y))

        self._draw_spawn_burst(screen, center, age)
        self._draw_halo(screen, center, scale, expiring, age)
        border = max(2, round(max(width, height) * 0.05))
        for dx, dy in (
            (border, 0),
            (-border, 0),
            (0, border),
            (0, -border),
            (border, border),
            (border, -border),
            (-border, border),
            (-border, -border),
        ):
            screen.window.blit(
                outline, outline.get_rect(center=(center[0] + dx, center[1] + dy))
            )
        screen.window.blit(icon, icon.get_rect(center=center))

    def _draw_spawn_burst(self, screen, center, age):
        duration = 1.25
        if age >= duration:
            return

        progress = min(1.0, age / duration)
        fade = min(1.0, (1.0 - progress) / 0.3)
        base = max(self.icon.get_width(), self.icon.get_height())
        max_radius = max(16, round(base * 0.72))
        pad = max_radius + 34

        layer = p.Surface((pad * 2, pad * 2), p.SRCALPHA)
        cx = cy = pad
        ease = 1.0 - (1.0 - progress) ** 3
        radius = round(max_radius * (0.18 + 0.82 * ease))
        thickness = max(2, round(base * 0.14 * (1.0 - 0.45 * progress)))

        diamond = (
            (cx, cy - radius),
            (cx + radius, cy),
            (cx, cy + radius),
            (cx - radius, cy),
        )
        p.draw.polygon(
            layer,
            (*GLOW_DARK, max(0, round(235 * fade))),
            diamond,
            thickness + 3,
        )
        p.draw.polygon(
            layer,
            (*GLOW, max(0, round(250 * fade))),
            diamond,
            thickness,
        )

        if radius > 8:
            inner = max(2, radius // 3)
            inner_points = (
                (cx, cy - inner),
                (cx + inner, cy),
                (cx, cy + inner),
                (cx - inner, cy),
            )
            p.draw.polygon(
                layer,
                (*GLOW_LIGHT, max(0, round(230 * fade))),
                inner_points,
                max(1, thickness // 2),
            )

        spark_alpha = max(0, round(245 * fade))
        if spark_alpha > 0:
            for index in range(8):
                angle = math.radians(self.halo_angle * 3.0 + index * 45)
                distance = radius + base * (
                    0.08 + 0.1 * abs(math.sin(age * 7 + index))
                )
                spark_x = cx + math.cos(angle) * distance
                spark_y = cy + math.sin(angle) * distance
                spark_size = max(1.5, base * 0.07 * (0.55 + 0.45 * fade))
                self._draw_sparkle(
                    layer,
                    spark_x,
                    spark_y,
                    spark_size,
                    GLOW_LIGHT,
                    spark_alpha,
                )

        if progress < 0.3:
            flash = 1.0 - progress / 0.3
            flash_size = max(1, round(base * 0.28 * (0.4 + 0.6 * flash)))
            flash_thickness = max(1, round(flash_size * 0.35))
            flash_alpha = max(0, round(220 * flash))
            p.draw.rect(
                layer,
                (*GLOW_LIGHT, flash_alpha),
                (cx - flash_size, cy - flash_thickness,
                 flash_size * 2, flash_thickness * 2),
            )
            p.draw.rect(
                layer,
                (*GLOW_LIGHT, flash_alpha),
                (cx - flash_thickness, cy - flash_size,
                 flash_thickness * 2, flash_size * 2),
            )

        screen.window.blit(layer, (center[0] - cx, center[1] - cy))

    @staticmethod
    def _draw_sparkle(layer, x, y, size, color, alpha):
        size = max(1, round(size))
        bar = max(1, size // 3)
        p.draw.rect(
            layer,
            (*color, alpha),
            (x - size, y - bar, size * 2, bar * 2),
        )
        p.draw.rect(
            layer,
            (*color, alpha),
            (x - bar, y - size, bar * 2, size * 2),
        )
        p.draw.rect(
            layer,
            (*color, min(255, alpha + 10)),
            (x - bar, y - bar, bar * 2, bar * 2),
        )

    def _draw_halo(self, screen, center, scale, expiring, age):
        base = max(self.icon.get_width(), self.icon.get_height())
        radius = round(base * 0.66 * scale)
        if radius < 6:
            return

        pulse = 0.5 + 0.5 * math.sin(age * 7.5)
        alpha = round(150 + 55 * pulse)
        if expiring:
            alpha = min(255, alpha + 55)

        width = max(2, round(3.2 * scale))
        margin = max(8, width * 4)
        angle_bucket = round((self.halo_angle % 360.0) / 7.5) % 48
        cache_key = (radius, angle_bucket, width)
        halo = self.halo_cache.get(cache_key)

        if halo is None:
            halo = p.Surface(
                (radius * 2 + margin * 2, radius * 2 + margin * 2),
                p.SRCALPHA,
            )
            cx = cy = radius + margin
            angle = math.radians(angle_bucket * 7.5)
            points = []
            for index in range(8):
                point_angle = angle + index * math.pi / 4
                length = radius if index % 2 == 0 else radius * 0.48
                points.append(
                    (
                        cx + math.cos(point_angle) * length,
                        cy + math.sin(point_angle) * length,
                    )
                )
            p.draw.polygon(halo, (*GLOW_DARK, 210), points, width * 4)
            p.draw.polygon(halo, (*GLOW, 90), points, width * 2)
            p.draw.polygon(halo, (*GLOW, 255), points, width)
            pip = max(1, round(2.5 * scale))
            for index in range(4):
                point_angle = angle + index * math.pi / 2
                px = cx + math.cos(point_angle) * radius
                py = cy + math.sin(point_angle) * radius
                p.draw.rect(
                    halo,
                    (*GLOW_LIGHT, 230),
                    (px - pip, py - pip, pip * 2, pip * 2),
                )

            if len(self.halo_cache) >= 256:
                self.halo_cache.clear()
            self.halo_cache[cache_key] = halo

        halo.set_alpha(alpha)
        screen.window.blit(halo, (center[0] - radius - margin, center[1] - radius - margin))

    def gen_pos(self, p1, p2):
        min_distance_sq = prize_dis ** 2
        best_position = (d_width // 2, (playfield_top + playfield_bottom) // 2)
        best_distance_sq = -1
        for _ in range(80):
            x = randint(50, d_width - 50)
            y = randint(playfield_top + 50, playfield_bottom - 50)
            p1_distance_sq = (p1.y - y) ** 2 + (p1.x - x) ** 2
            p2_distance_sq = (p2.y - y) ** 2 + (p2.x - x) ** 2
            closest_sq = min(p1_distance_sq, p2_distance_sq)
            if closest_sq >= min_distance_sq:
                self.x, self.y = x, y
                return
            if closest_sq > best_distance_sq:
                best_distance_sq = closest_sq
                best_position = (x, y)
        self.x, self.y = best_position

    def gen_prize(self):
        eligible = [
            kind for kind in prize_kinds
            if self.chosen_prizes.get(kind, 0) < prizes_per_kind
        ]

        if not eligible:
            self.is_allowed = False
            return

        self.chosen_prize = choice(eligible)
        self.chosen_prizes[self.chosen_prize] = (
            self.chosen_prizes.get(self.chosen_prize, 0) + 1
        )
        self.age_ms = 0.0
        self.halo_angle = 0.0
        self.icon_cache.clear()
        self.outline_cache.clear()
        self.halo_cache.clear()
        self.icon = Image(self.chosen_prize).transform()
        self.icon.fill(ICON_TINT, special_flags=p.BLEND_RGB_MAX)
        self.rectangle = self.icon.get_rect(center=(self.x, self.y))
        margin_x = self.rectangle.width // 2
        margin_y = self.rectangle.height // 2
        center_x = max(margin_x, min(d_width - margin_x, self.x))
        center_y = max(
            playfield_top + margin_y,
            min(playfield_bottom - margin_y, self.y),
        )
        self.x = center_x
        self.y = center_y
        self.rectangle = self.icon.get_rect(center=(center_x, center_y))

    def gen_rain(self):
        self.rain_list = []
        for i in range(rain_drops):
            x_R = randint(20, d_width - 20)
            y_R = randint(playfield_top + 20, playfield_bottom - 20)
            self.rain_list.append((x_R, y_R))

    def reward(self, winner, loser, screen, game):
        screen.effects.pickup(
            (self.x, self.y),
            winner.color,
        )

        if self.chosen_prize in MODE_PRIZES:
            winner.clear_powerup()

        if self.chosen_prize == 'speed':  # player's mode changes to fast mode
            winner.mode = fast_mode
            winner.radius = normal_radius
            winner.broken_visual = False
            winner.icon = Image.normal(winner.name)
            winner.powerup = 'speed'
        elif self.chosen_prize == 'fat':  # player's radius changes to big radius
            winner.mode = normal_mode
            winner.broken_visual = False
            winner.icon = Image.normal(winner.name)
            winner.radius = big_radius
            winner.powerup = 'fat'
        elif self.chosen_prize == 'rain':  # many player's color-circles are drawn
            self.rain(winner.color, screen)
        elif self.chosen_prize == 'boom':  # A big player-color circle is drawn
            self.boom(winner.color, winner.x, winner.y, screen)
        elif self.chosen_prize == 'bandi':  # winner's radius changes to big radius, mode changes to fast mode
            # the winner can punch others.
            winner.bandi = True
            winner.bandi_time_left = bandi_time
            winner.broken_visual = False
            winner.icon = Image.normal(winner.name)
            winner.mode = fast_mode
            winner.radius = big_radius
            winner.powerup = 'bandi'
        elif self.chosen_prize == 'follow_me':
            sound.evil.play()
            winner.color = loser.color = Color.true_color(winner.name)
            if getattr(winner, "powerup", None) is None and not getattr(winner, "bandi", False):
                winner.powerup = 'follow_me'

        screen.effects.label(
            (self.x, self.y),
            winner.color,
            PRIZE_LABELS.get(self.chosen_prize, "POWER UP!"),
        )
        winner.clamp_to_playfield()

    def rain(self, color, screen):
        self.gen_rain()
        rain_duration = rain_delay * max(1, len(self.rain_list))
        sound.play_rain(rain_duration)
        self.rain_color = tuple(color)[:3]
        self.rain_screen = screen
        self.rain_pending = list(self.rain_list)
        self.rain_accum = 0.0
        self._paint_rain_drop()
        screen.effects.rain(
            self.rain_list,
            color,
            radius=normal_radius,
        )

    @staticmethod
    def boom(color, x, y, screen):
        sound.bomb.play()
        screen.background.set_clip(playfield_rect)
        p.draw.circle(screen.background, color, (x, y), 200)
        screen.background.set_clip(None)
        screen.effects.boom(
            (x, y),
            color,
            radius=200,
        )
