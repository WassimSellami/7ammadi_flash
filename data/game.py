import pygame as p
import data.sound as sound
import data.image as image
from data.settings import *
from data.color import Color
from data.image import Image



class Game:
    game = True
    collision = False  # True  If both players are in a collision.
    col_start = False  # If True you can start the col timer.
    beaten_start = False  # If True you can start the beaten timer.

    @staticmethod
    def quit_test():
        """when user wanna exit the game"""
        for event in p.event.get():
            if event.type == p.KEYDOWN:
                if event.key == p.K_ESCAPE:
                    quit()

    def game_test(self):
        """when user wants to end the game and show final scores """
        keys = p.key.get_pressed()
        if keys[p.K_RETURN]:
            self.game = False

    @staticmethod
    def tangent(o1, o2):
        """returns True if the distance between o1, o2 is less than col_distance """
        current_distance = (abs(o1.y - o2.y)) ** 2 + (abs(o1.x - o2.x)) ** 2
        col_distance = (o1.radius + o2.radius) ** 2
        if current_distance <= col_distance:
            return True
        else:
            return False

    @staticmethod
    def bandi_reward(p1, p2, screen):
        p1.color = Color.true_color(p1.name)
        p2.color = Color.true_color(p2.name)
        p2.icon = Image.normal(p2.name)
        p2.beaten = False
        p2.broken_visual = False
        if p2.bandi or getattr(p2, "powerup", None) in ("speed", "fat"):
            p2.clear_powerup()
        else:
            p2.mode = normal_mode
        screen.effects.punch(
            (
                (p1.x + p2.x) / 2,
                (p1.y + p2.y) / 2,
            ),
            Color.true_color(p1.name),
        )
        screen.jump_to_wall(p2)

    @staticmethod
    def set_to_normal(player):
        player.radius = normal_radius
        player.color = Color.true_color(player.name)
        player.mode = normal_mode
        player.bandi = False
        player.bandi_time_left = 0.0
        player.powerup = None
        player.broken_visual = False
        player.clamp_to_playfield()

    @staticmethod
    def round_setup(screen, prize, p1, p2):
        screen.update_background()
        prize.chosen_prizes.clear()
        prize.is_allowed = False
        prize.icon = None
        prize.rectangle = None
        p1.setup(color=Color.color_A, angle=in_angle_A, icon=image.normal_icon_A, pos=1)
        p2.setup(color=Color.color_B, angle=in_angle_B, icon=image.normal_icon_B, pos=2)
        p1.mode = normal_mode
        p2.mode = normal_mode
        screen.start(p1, p2)

    @staticmethod
    def update_players(screen, p1, p2, elapsed_ms=0):
        """Update pos and paint players"""
        keys = p.key.get_pressed()
        p1.update_squash(elapsed_ms)
        p2.update_squash(elapsed_ms)
        p1.update_powerup(elapsed_ms)
        p2.update_powerup(elapsed_ms)
        p1.update_jump_anim(elapsed_ms)
        p2.update_jump_anim(elapsed_ms)
        if not getattr(p1, "jumping_to_wall", False):
            p1.change_angle(p.K_d, p.K_a, elapsed_ms, keys)
        if not getattr(p2, "jumping_to_wall", False):
            p2.change_angle(p.K_RIGHT, p.K_LEFT, elapsed_ms, keys)
        p1.change_coor(elapsed_ms)
        p2.change_coor(elapsed_ms)
        screen.paint_players(p1, p2, draw_players=False)

    def prize_check(self, prize, p1, p2, screen):
        """Checks if one of the players has got the prize and rewards him"""
        if self.tangent(prize, p1):
            prize.is_allowed = False
            prize.reward(p1, p2, screen, self)
        elif self.tangent(prize, p2):
            prize.is_allowed = False
            prize.reward(p2, p1, screen, self)

    def _start_normal_collision(self, p1, p2):
        if p1.jumping:
            return
        # Bandi-vs-bandi cancels out: both lose bandi and react like a normal hit.
        self.col_start = True
        self.collision = True
        p1.jumping = True
        p2.jumping = True
        self.set_to_normal(p1)
        self.set_to_normal(p2)
        p1.jump()
        p2.jump()
        p1.begin_squash(1.0)
        p2.begin_squash(1.0)
        sound.smash.play()

    def collision_check(self, p1, p2, screen):
        """Changes game parameters according to current_distance between players and modes..."""
        # If players are close enough: 2 cases:
        if self.tangent(p1, p2):
            if p1.bandi and p2.bandi:
                # Both bandi cancel each other with a regular collision.
                self._start_normal_collision(p1, p2)
            elif p1.bandi or p2.bandi:
                # Case 1: If one of the players has bandi mode:
                if p1.bandi:
                    victim = p2
                else:
                    victim = p1
                if not victim.jumping_to_wall and not getattr(victim, "punch_contacted", False):
                    victim.punch_contacted = True
                    sound.punch.play()
                    if p1.bandi:
                        self.bandi_reward(p1, p2, screen)
                    else:
                        self.bandi_reward(p2, p1, screen)
            else:
                # Case 2: If both players are not jumping(new collision):
                self._start_normal_collision(p1, p2)
        else:
            p1.punch_contacted = False
            p2.punch_contacted = False

