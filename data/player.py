from data.settings import *
import pygame as p
from math import cos, sin, radians
from random import randrange
from data.image import Image


# noinspection PyUnresolvedReferences
class Player:
    jumping = False
    beaten = False
    broken_visual = False
    y = d_height // 2
    radius = normal_radius
    step = in_step
    bandi = False
    mode = wait_mode
    score = 0

    def __init__(self, x, angle, color, icon, name):
        self.x = x
        self.angle = angle
        self.color = color
        self.icon = icon
        self.name = name
        self.squashing = False
        self.squash_elapsed = 0.0
        self.squash_duration = 0.32
        self.squash_strength = 1.0
        self.wall_event = None
        self.wall_cooldown = 0.0
        self.move_accum_x = 0.0
        self.move_accum_y = 0.0
        self.powerup = None
        self.bandi_time_left = 0.0
        self.jump_progress = 0.0
        self.broken_visual = False

    def begin_squash(self, strength=1.0, duration=0.32):
        self.squashing = True
        self.squash_elapsed = 0.0
        self.squash_duration = max(0.01, duration)
        self.squash_strength = strength

    def update_squash(self, elapsed_ms):
        if not getattr(self, "squashing", False):
            return
        self.squash_elapsed += max(0.0, elapsed_ms) / 1000.0
        if self.squash_elapsed >= self.squash_duration:
            self.squashing = False
            self.squash_elapsed = self.squash_duration

    def update_powerup(self, elapsed_ms):
        if not getattr(self, "bandi", False):
            return
        self.bandi_time_left = max(
            0.0,
            getattr(self, "bandi_time_left", bandi_time)
            - max(0.0, elapsed_ms) / 1000.0,
        )
        if self.bandi_time_left <= 0:
            self.bandi_to_normal()

    def update_jump_anim(self, elapsed_ms):
        if not getattr(self, "jumping", False):
            self.jump_progress = 0.0
            return
        self.jump_progress = min(
            1.0,
            getattr(self, "jump_progress", 0.0)
            + max(0.0, elapsed_ms) / max(0.001, jumping_time * 1000.0),
        )

    def clear_powerup(self):
        self.bandi = False
        self.bandi_time_left = 0.0
        self.radius = normal_radius
        self.mode = normal_mode
        self.broken_visual = False
        self.icon = Image.normal(self.name)
        self.powerup = None

    def restore_powerup_mode(self):
        if self.bandi or getattr(self, "powerup", None) == "speed":
            self.mode = fast_mode
        elif getattr(self, "powerup", None) == "fat":
            self.mode = normal_mode

    def apply_stagger_mode(self, fallback_mode):
        if self.bandi or getattr(self, "powerup", None) in ("speed", "fat"):
            self.restore_powerup_mode()
        else:
            self.mode = fallback_mode

    def setup(self, color, angle, icon, pos):
        self.color = color
        self.angle = angle
        self.radius = normal_radius
        self.bandi = False
        self.beaten = False
        self.jumping = False
        self.clear_knockback()
        self.punch_contacted = False
        self.x = pos * d_width // 3
        self.y = d_height // 2
        self.icon = icon
        self.mode = wait_mode
        self.squashing = False
        self.squash_elapsed = 0.0
        self.squash_strength = 1.0
        self.wall_event = None
        self.wall_cooldown = 0.0
        self.move_accum_x = 0.0
        self.move_accum_y = 0.0
        self.powerup = None
        self.bandi_time_left = 0.0
        self.jump_progress = 0.0
        self.broken_visual = False
        self.clamp_to_playfield()

    def clear_knockback(self):
        self.jumping_to_wall = False
        self.knockback_elapsed = 0.0
        self.knockback_duration = knockback_time
        self.knockback_direction = 0
        self.knockback_start_y = float(self.y) if hasattr(self, "y") else float(d_height // 2)
        self.knockback_target_y = float(self.y) if hasattr(self, "y") else float(d_height // 2)
        self.knockback_paused = False
        self.wall_event = None
        self.wall_cooldown = 0.0

    def start_knockback(self):
        if getattr(self, "jumping_to_wall", False):
            return
        self.clamp_to_playfield()
        playfield_midpoint = (playfield_top + playfield_bottom) / 2
        if self.y < playfield_midpoint:
            direction = -1
        else:
            direction = 1
        sprite_height = getattr(self.icon, "get_height", lambda: 0)()
        margin_y = max(self.radius, sprite_height // 2)
        target_y = (
            playfield_top + margin_y
            if direction < 0
            else playfield_bottom - margin_y
        )

        self.jumping_to_wall = True
        self.knockback_direction = direction
        self.knockback_start_y = float(self.y)
        self.knockback_target_y = float(target_y)
        self.knockback_elapsed = 0.0
        self.knockback_duration = knockback_time
        self.knockback_paused = False

    def pause_knockback(self):
        if getattr(self, "jumping_to_wall", False):
            self.knockback_paused = True

    def resume_knockback(self):
        if getattr(self, "jumping_to_wall", False):
            self.knockback_paused = False

    def clamp_to_playfield(self):
        sprite_width = getattr(self.icon, "get_width", lambda: 0)()
        sprite_height = getattr(self.icon, "get_height", lambda: 0)()
        margin_x = max(self.radius, sprite_width // 2)
        margin_y = max(self.radius, sprite_height // 2)
        self.x = max(margin_x, min(d_width - margin_x, int(self.x)))
        self.y = max(
            playfield_top + margin_y,
            min(playfield_bottom - margin_y, int(self.y)),
        )

    def paint_alone(self, screen):
        r = p.Rect(self.x - 3 * self.radius // 2, self.y - 3 * self.radius // 2, 3 * self.radius, 3 * self.radius)
        r_icon = self.icon.get_rect(center=(self.x, self.y))
        if not self.beaten:      # ne7iha? ?? 5ater dima beaten
            screen.background.set_clip(playfield_rect)
            p.draw.circle(screen.background, self.color, (self.x, self.y), self.radius)
            screen.background.set_clip(None)
        screen.window.blit(screen.background, (0, 0))
        screen.window.blit(self.icon, r_icon)
        p.display.update([r])

    @staticmethod
    def paint_both(screen, p1, p2, draw_players=True):
        if not p1.jumping:
            screen.background.set_clip(playfield_rect)
            p.draw.circle(screen.background, p1.color, (p1.x, p1.y), p1.radius)
            p.draw.circle(screen.background, p2.color, (p2.x, p2.y), p2.radius)
            screen.background.set_clip(None)
        screen.window.blit(screen.background, (0, 0))
        if draw_players:
            screen.effects.draw_player(screen.window, p1)
            screen.effects.draw_player(screen.window, p2)

    def change_angle(self, key1, key2, elapsed_ms=0, keys=None):
        if keys is None:
            keys = p.key.get_pressed()
        factor = max(0.0, elapsed_ms) / speed
        if keys[key1]:
            self.angle += self.mode[0] * factor
        elif keys[key2]:
            self.angle -= self.mode[0] * factor

    def change_coor(self, elapsed_ms=0):
        self.wall_cooldown = max(
            0.0, getattr(self, "wall_cooldown", 0.0) - max(0, elapsed_ms) / 1000.0
        )
        if getattr(self, "jumping_to_wall", False):
            if getattr(self, "knockback_paused", False):
                return
            duration_ms = max(0.001, getattr(self, "knockback_duration", knockback_time)) * 1000
            self.knockback_elapsed = min(
                duration_ms,
                getattr(self, "knockback_elapsed", 0.0) + max(0, elapsed_ms)
            )
            progress = self.knockback_elapsed / duration_ms
            start_y = getattr(self, "knockback_start_y", float(self.y))
            target_y = getattr(self, "knockback_target_y", float(self.y))
            self.y = start_y + (target_y - start_y) * progress
            if progress >= 1.0:
                self.y = float(target_y)
                self.jumping_to_wall = False
                self.knockback_elapsed = duration_ms
                self.wall_event = (
                    self.x,
                    0 if getattr(self, "knockback_direction", 1) < 0 else playfield_bottom,
                )
                self.knockback_direction = 0
                self.beaten = False
                if self.bandi or getattr(self, "powerup", None) in ("speed", "fat"):
                    self.restore_powerup_mode()
                else:
                    self.mode = normal_mode
                self.move_accum_x = 0.0
                self.move_accum_y = 0.0
            self.clamp_to_playfield()
            return
        px = cos(radians(self.angle))
        py = sin(radians(self.angle))
        sprite_width = getattr(self.icon, "get_width", lambda: 0)()
        sprite_height = getattr(self.icon, "get_height", lambda: 0)()
        margin_x = max(self.radius, sprite_width // 2)
        margin_y = max(self.radius, sprite_height // 2)
        hit_side = None
        if (self.y <= playfield_top + margin_y) and (py < 0):
            py = 0
            hit_side = "top"
        elif (self.y >= playfield_bottom - margin_y) and (py > 0):
            py = 0
            hit_side = "bottom"
        if (self.x <= margin_x) and (px < 0):
            px = 0
            hit_side = "left"
        elif (self.x >= d_width - margin_x) and (px > 0):
            px = 0
            hit_side = "right"
        factor = max(0.0, elapsed_ms) / speed
        if getattr(self, "jumping", False):
            factor *= jump_move_factor
        self.move_accum_x += px * self.mode[1] * factor
        self.move_accum_y += py * self.mode[1] * factor
        dx = int(self.move_accum_x)
        dy = int(self.move_accum_y)
        self.move_accum_x -= dx
        self.move_accum_y -= dy
        self.x += dx
        self.y += dy
        self.clamp_to_playfield()
        if hit_side is not None and self.wall_cooldown <= 0:
            if hit_side == "top":
                self.wall_event = (self.x, playfield_top)
            elif hit_side == "bottom":
                self.wall_event = (self.x, playfield_bottom)
            elif hit_side == "left":
                self.wall_event = (0, self.y)
            else:
                self.wall_event = (d_width, self.y)
            self.wall_cooldown = 0.5
        if hit_side is not None and (
            self.bandi or getattr(self, "powerup", None) in ("speed", "fat")
        ):
            self.restore_powerup_mode()

    def jump(self):
        self.angle = 0
        self.jump_progress = 0.0
        w12 = d_width // 5   # screen 1        3
        w34 = 4 * w12               # 2        4
        play_height = playfield_bottom - playfield_top
        h13 = playfield_top + play_height // 5
        h24 = playfield_bottom - play_height // 5
        # self.jumping = True
        if (0 <= self.x < w12) and (playfield_top <= self.y < h13):
            # while not(abs(angle_A - angle_B) in range(50, 90)):
            self.angle = randrange(-20, 110)
        elif (w34 <= self.x < d_width) and (playfield_top <= self.y < h13):
            # while not(abs(angle_A - angle_B) in range(50, 90)):
            self.angle = randrange(70, 200)
        elif (w34 <= self.x < d_width) and (h24 <= self.y < d_height):
            # while not(abs(angle_A - angle_B) in range(50, 90)):
            self.angle = randrange(160, 290)
        elif (0 <= self.x < w12) and (h24 <= self.y < d_height):
            # while not(abs(angle_A - angle_B) in range(50, 90)):
            self.angle = randrange(250, 380)
        else:
            # while not(abs(angle_A - angle_B) in range(60, 120)):
            self.angle = randrange(0, 360)

    def bandi_to_normal(self):
        self.bandi = False
        self.bandi_time_left = 0.0
        self.mode = normal_mode
        self.radius = normal_radius
        if getattr(self, "powerup", None) == "bandi":
            self.powerup = None

    def beaten_to_normal(self):
        self.beaten = False
        self.mode = normal_mode
        self.broken_visual = False
        self.icon = Image.normal(self.name)

