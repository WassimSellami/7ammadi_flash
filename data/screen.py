import math
import pygame as p
from data.settings import *
from data.color import Color
from data.timer import Timer
from data.image import Image
import data.sound as sound

class Screen:
    very_large_text = p.font.SysFont('Comic Sans MS', min(d_width // 5, d_height // 3))
    large_text = p.font.SysFont('Comic Sans MS', min(d_width // 16, d_height // 9))
    small_text = p.font.SysFont('Comic Sans MS', min(d_width // 25, d_height // 14))
    button_text_font = p.font.SysFont('Comic Sans MS', max(24, d_height // 34))

    def __init__(self, collision=False, sound_off=True):
        # Creates a window and its  background with some default variables.
        self.d_width = d_width
        self.d_height = d_height
        self.collision = collision
        self.sound_off = sound_off
        self.window = p.display.get_surface()
        self.menu_button_rects = []
        self.menu_color_rects = []
        Image.prepare_icons()
        self.background = Image.background()
        self.continue_button_rect = None
        self.music_toggle_rect = None
        self.sound_toggle_rect = None
        self.music_icon_base = p.image.load("data/icons/music.png").convert_alpha()
        self.music_icon_cache = {}
        self.sound_icon_base = p.image.load("data/icons/volume.png").convert_alpha()
        self.sound_icon_cache = {}
        self.scoreboard_anim_key = None
        self.scoreboard_anim_start = None
        self.scoreboard_settled = False
        self._text_cache = {}
        p.display.set_caption('7ammadi Flash V 4.6')

    timer1 = Timer(symbol_time, 100)  # Creating a symbol_timer(sec) with 100_ms_delay

    def show_symbol(self, p1, p2, symbol, sound):
        self.paint_players(p1, p2)
        self.render_blit(symbol, self.very_large_text, (d_width // 2, d_height // 2), Color.black)
        p.display.flip()

    def start(self, p1, p2):
        pass

    def paint_boom(self, player, prize):
        prize.boom(player.color, player.x, player.y, self)

    def paint_rain(self, player, prize):
        prize.rain(player.color, self)

    def score(self, player):
        player.score = 0
        player_color = Color.true_color(player.name)
        play_height = playfield_bottom - playfield_top
        try:
            mask = p.mask.from_threshold(
                self.background.subsurface(playfield_rect), player_color, (1, 1, 1)
            )
            painted = mask.count()
        except (ValueError, p.error):
            painted = 0
            for j in range(playfield_top, playfield_bottom):
                for i in range(1, d_width):
                    if self.background.get_at((i, j)) == player_color:
                        painted += 1
        player.score = int(round(painted / (play_height * d_width) * 100))
        return player.score

    @staticmethod
    def who_won(p1, p2):
        """Determines the winner and prepares the result and the result color"""
        if p1.score > p2.score:
            winner = p1
        elif p1.score < p2.score:
            winner = p2
        else:
            winner = None
        if winner is not None:
            result = f'******{winner.name}  wins *******'
            result_color = Color.true_color(winner.name)
        else:
            result_color = Color.white
            result = '******Draw******'
        return winner, result, result_color

    def render_blit(self, text, size, center, color, return_rect=False):
        key = (text, id(size), tuple(color)[:3])
        surface = self._text_cache.get(key)
        if surface is None:
            surface = size.render(text, True, color)
            if len(self._text_cache) >= 256:
                self._text_cache.clear()
            self._text_cache[key] = surface
        rectangle = surface.get_rect(center=center)
        self.window.blit(surface, rectangle)
        if return_rect:
            return rectangle

    def update_background(self):
        self.background = Image.background()
        self.window.blit(self.background, (0, 0))
        p.display.flip()

    def paint_players(self, p1, p2, draw_players=True):
        p1.paint_both(self, p1, p2, draw_players=draw_players)

    def jump_to_wall(self, player):
        player.start_knockback()

    def show_menu(self, title, options, selected, paint_choices=None):
        self.window.fill(Color.black)
        self.menu_color_rects = []
        self.render_blit(title, self.large_text, (d_width // 2, d_height // 5), Color.white)
        self.menu_button_rects = []
        selected_color = (255, 205, 94)
        idle_color = (198, 210, 228)
        options_top = d_height * 3 // 8
        spacing = d_height // 10
        for index, option in enumerate(options):
            center_y = options_top + index * spacing
            is_color_row = paint_choices is not None and option.startswith("Player ")
            if is_color_row:
                player_index = 0 if option.startswith("Player A") else 1
                self._draw_inline_colors(
                    player_index,
                    paint_choices[player_index],
                    center_y,
                    index == selected,
                )
            else:
                color = selected_color if index == selected else idle_color
                prefix = "> " if index == selected else "  "
                self.render_blit(
                    prefix + option,
                    self.small_text,
                    (d_width // 2, center_y),
                    color,
                )
            row_width = d_width // 2 if is_color_row else d_width // 4
            self.menu_button_rects.append(p.Rect(
                d_width // 2 - row_width // 2,
                center_y - d_height // 40,
                row_width,
                d_height // 10,
            ))
        p.display.flip()

    def _draw_inline_colors(self, player_index, choice, center_y, active):
        label = "Player A Color" if player_index == 0 else "Player B Color"
        prefix = "> " if active else "  "
        color = (255, 205, 94) if active else (198, 210, 228)
        prefix_width = self.small_text.size(prefix)[0]
        label_width = self.small_text.size(label)[0]
        size = 48
        gap = 10
        swatch_total = len(Color.paint_palette) * size + (len(Color.paint_palette) - 1) * gap
        group_gap = 20
        group_width = prefix_width + label_width + group_gap + swatch_total
        left = d_width // 2 - group_width // 2
        self.render_blit(
            prefix,
            self.small_text,
            (left + prefix_width // 2, center_y),
            color,
        )
        label_left = left + prefix_width
        self.render_blit(
            label,
            self.small_text,
            (label_left + label_width // 2, center_y),
            color,
        )
        swatch_left = label_left + label_width + group_gap
        for index, (_, rgb) in enumerate(Color.paint_palette):
            rect = p.Rect(
                swatch_left + index * (size + gap),
                center_y - size // 2,
                size,
                size,
            )
            p.draw.rect(self.window, rgb, rect, border_radius=10)
            border = Color.white if index == choice else (62, 74, 96)
            border_width = 4 if index == choice else 2
            p.draw.rect(self.window, border, rect, width=border_width, border_radius=10)
            self.menu_color_rects.append((player_index, index, rect))

    @staticmethod
    def _toggle_icons(cache, base, size):
        icons = cache.get(size)
        if icons is None:
            scaled = p.transform.smoothscale(base, (size, size)).copy()
            icon_on = scaled.copy()
            icon_on.fill((255, 205, 94), special_flags=p.BLEND_RGB_MAX)
            icon_off = scaled.copy()
            icon_off.fill((118, 132, 156), special_flags=p.BLEND_RGB_MAX)
            margin = max(3, size // 8)
            thickness = max(2, round(size * 0.1))
            for start, end in (
                ((margin, margin), (size - margin, size - margin)),
                ((size - margin, margin), (margin, size - margin)),
            ):
                p.draw.line(icon_off, (52, 10, 10), start, end, thickness + 2)
            for start, end in (
                ((margin, margin), (size - margin, size - margin)),
                ((size - margin, margin), (margin, size - margin)),
            ):
                p.draw.line(icon_off, (232, 62, 52), start, end, thickness)
            icons = (icon_on, icon_off)
            cache[size] = icons
        return icons

    def draw_round_timeline(self, elapsed_ms):
        width, height = self.window.get_size()
        elapsed_ms = max(0, min(elapsed_ms, round_time * 1000))
        progress = elapsed_ms / (round_time * 1000)

        remaining = max(0.0, (round_time * 1000 - elapsed_ms) / 1000.0)
        warning = 0.0
        if elapsed_ms > 0 and remaining <= 10.0:
            warning = min(1.0, (10.0 - remaining) / 10.0)
        pulse = 0.5 + 0.5 * math.sin(elapsed_ms / 1000.0 * 6.0)

        def blend(base, warm, amount):
            amount = max(0.0, min(1.0, amount))
            return tuple(
                round(base[i] + (warm[i] - base[i]) * amount) for i in range(3)
            )

        panel_color = blend((16, 23, 38), (58, 29, 34), warning * (0.3 + 0.35 * pulse))
        track_color = blend((55, 68, 90), (116, 70, 62), warning * 0.55)
        fill_color = blend((77, 209, 188), (255, 116, 70), warning * (0.55 + 0.35 * pulse))

        panel = p.Rect(0, 0, width, hud_height)
        p.draw.rect(self.window, panel_color, panel)

        scale = min(width / d_width, height / d_height)
        icon_size = max(20, min(hud_height - 20, round(46 * scale)))
        music_icons = self._toggle_icons(
            self.music_icon_cache, self.music_icon_base, icon_size
        )
        sound_icons = self._toggle_icons(
            self.sound_icon_cache, self.sound_icon_base, icon_size
        )
        music_toggle = p.Rect(
            width - 22 - icon_size,
            panel.centery - icon_size // 2,
            icon_size,
            icon_size,
        )
        sound_toggle = p.Rect(
            music_toggle.left - 10 - icon_size,
            music_toggle.top,
            icon_size,
            icon_size,
        )
        self.music_toggle_rect = music_toggle
        self.sound_toggle_rect = sound_toggle

        track = p.Rect(28, panel.centery - 5, max(40, sound_toggle.left - 50), 10)
        p.draw.rect(self.window, track_color, track, border_radius=5)

        fill_width = round(track.width * progress)
        if fill_width:
            fill = p.Rect(track.x, track.y, fill_width, track.height)
            p.draw.rect(self.window, fill_color, fill, border_radius=5)

        for spawn_sec in range(prize_time, round_time, prize_time):
            x = track.x + round(track.width * spawn_sec / round_time)
            y = track.centery
            reached = elapsed_ms >= spawn_sec * 1000
            diamond = [(x, y - 10), (x + 10, y), (x, y + 10), (x - 10, y)]
            reached_color = blend((255, 205, 94), (255, 150, 90), warning * 0.6)
            p.draw.polygon(
                self.window, reached_color if reached else (28, 39, 58), diamond
            )
            p.draw.polygon(self.window, reached_color, diamond, width=2)

        enabled = sound.music_enabled
        self.window.blit(
            music_icons[0] if enabled else music_icons[1], music_toggle
        )
        effects_enabled = sound.effects_enabled
        self.window.blit(
            sound_icons[0] if effects_enabled else sound_icons[1], sound_toggle
        )

    def reset_scoreboard_animation(self):
        self.scoreboard_anim_key = None
        self.scoreboard_anim_start = None
        self.scoreboard_settled = False

    def draw_scoreboard(self, p1, p2, *, title, result, hint="", button_text=""):
        clean_result = str(result).replace("*", "").replace("_", " ").strip()
        anim_key = (title, clean_result)
        now = p.time.get_ticks()
        if self.scoreboard_anim_key != anim_key or self.scoreboard_anim_start is None:
            self.scoreboard_anim_key = anim_key
            self.scoreboard_anim_start = now
            self.scoreboard_settled = False
        elif self.scoreboard_settled:
            return

        width, height = self.window.get_size()
        self.window.fill((12, 18, 30))

        ink = (241, 245, 252)
        muted = (161, 176, 200)
        card = (25, 36, 55)
        accent = (255, 205, 94)

        elapsed = max(0, now - self.scoreboard_anim_start)

        count_span = 1100
        count_progress = min(1.0, elapsed / count_span)
        eased = 1.0 - (1.0 - count_progress) ** 3
        reveal_progress = 0.0
        if elapsed > count_span:
            reveal_progress = min(1.0, (elapsed - count_span) / 450.0)
        result_alpha = round(255 * reveal_progress)

        def text(value, font, color, center, alpha=255):
            surface = font.render(str(value), True, color)
            if alpha < 255:
                surface = surface.copy()
                surface.set_alpha(max(0, alpha))
            self.window.blit(surface, surface.get_rect(center=center))

        text(title, self.large_text, ink, (width // 2, height // 7))
        if result_alpha > 0:
            text(clean_result, self.small_text, accent, (width // 2, height // 4), result_alpha)

        card_width = width * 34 // 100
        card_height = height * 39 // 100
        card_top = height * 34 // 100

        for player, center_x in ((p1, width * 28 // 100), (p2, width * 72 // 100)):
            rect = p.Rect(0, card_top, card_width, card_height)
            rect.centerx = center_x
            color = Color.true_color(player.name)

            p.draw.rect(self.window, card, rect, border_radius=22)
            stripe = p.Rect(rect.left + 24, rect.top + 18, rect.width - 48, 6)
            p.draw.rect(self.window, color, stripe, border_radius=3)

            text(player.name.replace("_", " "), self.small_text, ink,
                 (center_x, rect.top + card_height // 5))

            target_value = player.score
            shown = round(target_value * eased)
            text(f"{shown}%", self.large_text, color, (center_x, rect.centery))

        if hint:
            text(hint, self.small_text, muted, (width // 2, height * 88 // 100))

        self.continue_button_rect = None
        if button_text:
            button_width = min(width * 46 // 100, 560)
            button_height = height * 7 // 100
            button_rect = p.Rect(0, 0, button_width, button_height)
            button_rect.centerx = width // 2
            button_rect.top = height * 82 // 100
            p.draw.rect(self.window, card, button_rect, border_radius=18)
            p.draw.rect(self.window, accent, button_rect, width=3, border_radius=18)
            text(button_text, self.button_text_font, ink, button_rect.center)
            self.continue_button_rect = button_rect
        if elapsed >= count_span + 450:
            self.scoreboard_settled = True
        p.display.flip()

