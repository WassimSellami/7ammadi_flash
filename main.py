"""7ammadi Flash V 4.6
This is a Painting Game.
"""
import pygame as p

p.init()

from data.settings import *

_logical_window = p.display.set_mode(
    (d_width, d_height),
    p.FULLSCREEN | p.SCALED,
)

from data.color import Color
from data.screen import Screen
from data.player import Player
from data.game import Game
from data.timer import Timer
from data.prize import Prize
from data.effects import EffectsManager
import data.sound as sound
import data.image as image

p.display.set_icon(image.load_window_icon())


def palette_index(color):
    for index, (_, rgb) in enumerate(Color.paint_palette):
        if rgb == color:
            return index
    return 0


paint_choices = [
    palette_index(Color.color_A),
    palette_index(Color.color_B),
]


def apply_paint_colors():
    Color.color_A = Color.paint_palette[paint_choices[0]][1]
    Color.color_B = Color.paint_palette[paint_choices[1]][1]
    image.prepare_icons()


def select_paint_color(player_index, color_index):
    other = 1 - player_index
    if color_index == paint_choices[other]:
        return
    paint_choices[player_index] = color_index
    apply_paint_colors()


def cycle_paint_color(player_index, direction):
    other = 1 - player_index
    choice = paint_choices[player_index]
    for _ in range(len(Color.paint_palette)):
        choice = (choice + direction) % len(Color.paint_palette)
        if choice != paint_choices[other]:
            break
    select_paint_color(player_index, choice)


apply_paint_colors()


Game1 = Game()
Screen1 = Screen()
Screen1.effects = EffectsManager(
    Screen1.window.get_size(),
    p.Rect(0, playfield_top, d_width, playfield_bottom - playfield_top),
)
Prize1 = Prize()
Player_A = Player(x=d_width // 3, angle=in_angle_A, color=Color.color_A, icon=image.normal_icon_A, name='Player_A')
Player_B = Player(x=2 * d_width // 3, angle=in_angle_B, color=Color.color_B, icon=image.normal_icon_B, name='Player_B')


round_timer = Timer(round_time)
jump_timer = Timer(jumping_time)
broken_timer = Timer(broken_time)
beaten_timer = Timer(beaten_time)
prize_timer = Timer(prize_time)
countdown_timer = Timer(symbol_time)

clock = p.time.Clock()
state = "main_menu"
previous_state = "gameplay"
menu_selected = 0
countdown_step = 0
countdown_labels = ("3", "2", "1", "Go!")
countdown_sounds = (sound.s_3, sound.s_2, sound.s_1, sound.s_go)
match_scored = False
round_elapsed_ms = 0
next_prize_index = 1
match_result = ""
pause_enter_pressed = False
synced_music_state = None
synced_music_enabled = sound.music_enabled


def sync_game_music():
    global synced_music_state, synced_music_enabled
    preference_changed = synced_music_enabled != sound.music_enabled
    state_changed = synced_music_state != state
    if not preference_changed and not state_changed:
        return

    if state == "gameplay":
        if sound.music_enabled:
            if preference_changed and sound.is_game_music_playing():
                sound.resume_game_music()
            elif sound.is_game_music_paused():
                sound.resume_game_music()
            else:
                sound.play_m1(force_restart=state_changed)
        else:
            sound.stop_game_music()
    elif state == "pause_menu":
        sound.pause_game_music()
    else:
        sound.stop_game_music()

    synced_music_state = state
    synced_music_enabled = sound.music_enabled


def reset_match():
    global state, menu_selected, countdown_step, match_scored, round_elapsed_ms, next_prize_index
    global pause_enter_pressed
    apply_paint_colors()
    Screen1.effects.clear()
    Screen1.reset_scoreboard_animation()
    Game1.game = True
    Game1.collision = False
    Game1.col_start = False
    Game1.beaten_start = False
    Player_A.score = 0
    Player_B.score = 0
    Player_A.setup(Color.color_A, in_angle_A, image.normal_icon_A, 1)
    Player_B.setup(Color.color_B, in_angle_B, image.normal_icon_B, 2)
    Prize1.chosen_prizes.clear()
    Prize1.is_allowed = False
    Prize1.icon = None
    Prize1.rectangle = None
    Prize1.clear_rain()
    Game1.round_setup(Screen1, Prize1, Player_A, Player_B)
    for timer in (round_timer, jump_timer, broken_timer, beaten_timer, prize_timer, countdown_timer):
        timer.done = False
        timer.paused = False
    countdown_step = 0
    match_scored = False
    round_elapsed_ms = 0
    next_prize_index = 1
    menu_selected = 0
    pause_enter_pressed = False
    countdown_timer.start()
    countdown_sounds[0].play()
    sound.stop_game_music()
    state = "countdown"


def pause_all_timers():
    for timer in (round_timer, jump_timer, broken_timer, beaten_timer, prize_timer, countdown_timer):
        if not timer.done:
            timer.pause()
    Player_A.pause_knockback()
    Player_B.pause_knockback()


def resume_all_timers():
    for timer in (round_timer, jump_timer, broken_timer, beaten_timer, prize_timer, countdown_timer):
        if timer.paused:
            timer.resume()
    Player_A.resume_knockback()
    Player_B.resume_knockback()

def continue_from_pause():
    global state, previous_state
    resume_all_timers()
    state = "gameplay" if previous_state == "gameplay" else "countdown"


def open_pause_menu():
    global state, previous_state, menu_selected, pause_enter_pressed
    previous_state = state
    pause_all_timers()
    sound.pause_game_music()
    menu_selected = 0
    pause_enter_pressed = False
    state = "pause_menu"


def collision():
    Game1.collision_check(Player_A, Player_B, Screen1)
    if Game1.col_start:
        jump_timer.start()
        broken_timer.start()
        Game1.col_start = False
    if not broken_timer.done:
        broken_timer.check()
    if Player_A.jumping or Player_B.jumping:
        jump_timer.check()
    if jump_timer.done and (Player_A.jumping or Player_B.jumping):
        Player_A.jumping = False
        Player_B.jumping = False
        Player_A.broken_visual = True
        Player_B.broken_visual = True
        Player_A.apply_stagger_mode(slow_mode)
        Player_B.apply_stagger_mode(slow_mode)
    if broken_timer.done and Game1.collision:
        Game1.collision = False
        Player_A.jumping = False
        Player_B.jumping = False
        Player_A.broken_visual = False
        Player_B.broken_visual = False
        Player_A.apply_stagger_mode(normal_mode)
        Player_B.apply_stagger_mode(normal_mode)


def prize(dt):
    Prize1.update(dt)
    if Prize1.is_allowed:
        if Prize1.is_expired():
            Prize1.is_allowed = False
            Prize1.icon = None
            Prize1.rectangle = None
        else:
            if not Prize1.sound:
                Prize1.sound = True
                sound.plop.play()
            Game1.prize_check(Prize1, Player_A, Player_B, Screen1)


def return_to_main_menu():
    global state, menu_selected, pause_enter_pressed
    menu_selected = 0
    pause_enter_pressed = False
    state = "main_menu"


def menu_options():
    if state == "main_menu":
        return (
            "Start",
            "Player A Color",
            "Player B Color",
            "Exit Game",
        )
    return (
        "Continue",
        "Play Again",
        "Exit Game",
    )


def adjust_menu_value(direction):
    action = menu_options()[menu_selected]
    if action.startswith("Player A Color"):
        cycle_paint_color(0, direction)
    elif action.startswith("Player B Color"):
        cycle_paint_color(1, direction)


def activate_menu_action(options):
    global state, previous_state, menu_selected, running
    action = options[menu_selected]
    if action == "Start":
        reset_match()
    elif action.startswith("Player A Color"):
        cycle_paint_color(0, 1)
    elif action.startswith("Player B Color"):
        cycle_paint_color(1, 1)
    elif action == "Continue":
        continue_from_pause()
    elif action == "Play Again":
        reset_match()
    elif action == "Exit Game":
        running = False


running = True
while running:
    dt = clock.tick(60) / 1000.0
    frame_elapsed_ms = dt * 1000.0
    event_batch_locked = False
    for event in p.event.get():
        if event.type == p.QUIT:
            running = False
        elif event_batch_locked:
            continue
        elif event.type == getattr(p, "WINDOWFOCUSLOST", -1):
            if state in ("gameplay", "countdown"):
                open_pause_menu()
                event_batch_locked = True
        elif event.type == p.KEYUP:
            if event.key == p.K_RETURN and pause_enter_pressed:
                pause_enter_pressed = False
        elif event.type == p.KEYDOWN:
            if state in ("main_menu", "pause_menu"):
                options = menu_options()
                if event.key in (p.K_DOWN, p.K_s):
                    menu_selected = (menu_selected + 1) % len(options)
                    sound.plop.play()
                elif event.key in (p.K_UP, p.K_w):
                    menu_selected = (menu_selected - 1) % len(options)
                    sound.plop.play()
                elif event.key in (p.K_LEFT, p.K_a):
                    adjust_menu_value(-1)
                    sound.plop.play()
                elif event.key in (p.K_RIGHT, p.K_d):
                    adjust_menu_value(1)
                    sound.plop.play()
                elif event.key == p.K_RETURN:
                    if state == "pause_menu":
                        pause_enter_pressed = True
                    activate_menu_action(options)
                    event_batch_locked = True
                elif event.key == p.K_ESCAPE and state == "pause_menu":
                    continue_from_pause()
                    event_batch_locked = True
            elif state == "score":
                if event.key == p.K_RETURN:
                    return_to_main_menu()
                    event_batch_locked = True
            elif event.key == p.K_ESCAPE and state in ("gameplay", "countdown"):
                open_pause_menu()
                event_batch_locked = True
        elif event.type == p.MOUSEBUTTONDOWN and event.button == 1:
            if state in ("main_menu", "pause_menu"):
                options = menu_options()
                if state == "main_menu":
                    for player_index, color_index, rect in Screen1.menu_color_rects:
                        if rect.collidepoint(event.pos):
                            label = (
                                "Player A Color"
                                if player_index == 0
                                else "Player B Color"
                            )
                            if label in options:
                                menu_selected = options.index(label)
                            select_paint_color(player_index, color_index)
                            event_batch_locked = True
                            break
                if not event_batch_locked:
                    for index, rect in enumerate(Screen1.menu_button_rects):
                        if rect.collidepoint(event.pos):
                            menu_selected = index
                            activate_menu_action(options)
                            event_batch_locked = True
                            break
            elif state == "gameplay":
                if (
                    Screen1.music_toggle_rect
                    and Screen1.music_toggle_rect.collidepoint(event.pos)
                ):
                    sound.toggle_music()
                    event_batch_locked = True
                elif (
                    Screen1.sound_toggle_rect
                    and Screen1.sound_toggle_rect.collidepoint(event.pos)
                ):
                    sound.toggle_effects()
                    event_batch_locked = True
            elif state == "score":
                if Screen1.continue_button_rect and Screen1.continue_button_rect.collidepoint(event.pos):
                    return_to_main_menu()
                    event_batch_locked = True

    sync_game_music()

    if state == "main_menu":
        Screen1.show_menu(
            "7ammadi Flash",
            menu_options(),
            menu_selected,
            paint_choices,
        )

    elif state == "pause_menu":
        Screen1.show_menu(
            "Paused",
            menu_options(),
            menu_selected
        )

    elif state == "countdown":
        countdown_timer.check()
        Player_A.change_angle(p.K_d, p.K_a, frame_elapsed_ms)
        Player_B.change_angle(p.K_RIGHT, p.K_LEFT, frame_elapsed_ms)
        Screen1.paint_players(Player_A, Player_B)
        Screen1.render_blit(countdown_labels[countdown_step], Screen1.very_large_text,
                            (d_width // 2, d_height // 2), Color.black)
        p.display.flip()
        if countdown_timer.done:
            countdown_step += 1
            if countdown_step < len(countdown_labels):
                countdown_timer.start()
                countdown_sounds[countdown_step].play()
            else:
                round_timer.start()
                prize_timer.start()
                jump_timer.done = True
                broken_timer.done = True
                beaten_timer.done = True
                state = "gameplay"

    elif state == "gameplay":
        Screen1.effects.update(dt)
        Game1.update_players(Screen1, Player_A, Player_B, frame_elapsed_ms)
        Screen1.effects.observe_players((Player_A, Player_B), dt)
        collision()
        round_timer.check()
        round_elapsed_ms = min(round_time * 1000, round_timer.passed_time)
        spawn_ms = next_prize_index * prize_time * 1000
        if spawn_ms < round_time * 1000 and spawn_ms <= round_elapsed_ms:
            next_prize_index += 1
            Prize1.sound = False
            Prize1.is_allowed = True
            Prize1.gen_pos(Player_A, Player_B)
            Prize1.gen_prize()
        prize(dt)
        Screen1.effects.draw(
            Screen1.window,
            (Player_A, Player_B),
        )

        # Redraw important objects above the decorative effects.
        Screen1.effects.draw_player(Screen1.window, Player_A)
        Screen1.effects.draw_player(Screen1.window, Player_B)

        if Prize1.is_allowed:
            Prize1.show_prize(Screen1)

        Screen1.effects.draw_labels(Screen1.window)
        Screen1.draw_round_timeline(round_elapsed_ms)
        p.display.flip()
        if round_timer.done:
            if not match_scored:
                match_scored = True
                Screen1.score(Player_A)
                Screen1.score(Player_B)
                _, match_result, _ = Screen1.who_won(Player_A, Player_B)
                Screen1.draw_scoreboard(
                    Player_A, Player_B,
                    title="Results",
                    result=match_result,
                    button_text="Continue to Main Menu"
                )
                state = "score"

    elif state == "score":
        Screen1.draw_scoreboard(
            Player_A, Player_B,
            title="Results",
            result=match_result,
            button_text="Continue to Main Menu"
        )

sound.shutdown_audio()
p.quit()
