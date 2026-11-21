import pygame as _p

d_width = 1920
d_height = 1080
# Visual accent shared by the prize spawn portal and its rotating halo.
prize_glow_color = (140, 72, 18)
# Music defaults.
music_enabled_default = False
sound_enabled_default = True
music_volume = 0.2
# Time parameters.
# ms:
speed = 35  # Delay
# Seconds:
broken_time = 5  # Time in slow mode after collision
jumping_time = 1.4
jump_visual_height = 110  # Pixels the player icon lifts during a collision jump
jump_move_factor = 0.8  # Fraction of normal movement while colliding in the air
swing_angle = 20.0
swing_speed = 11.0
swing_upper_factor = 0.5
jump_shadow_offset = 0.47  # Shadow sits just under the icon, in icon heights
idle_shadow_offset = 0.47  # Resting shadow matches the landing jump shadow
bandi_time = 10  # Time in bandi mode
beaten_time = 5  # Time in slow mode after being beaten
knockback_time = 0.2  # Seconds for a bandi punch knockback
prize_time = 12  # Time between 2 prizes
round_time = 84  # round play time
prize_kinds = ("rain", "follow_me", "bandi", "fat", "boom", "speed")
rain_drops = 30  # Number of rain drops per rain prize
rain_delay = 0.05  # Seconds between individual rain drops

# Prize budget for one round, derived from the timing and kinds above.
prize_kind_count = max(1, len(set(prize_kinds)))
prizes_per_round = max(0, int((round_time - 1e-9) // max(1e-9, prize_time)))
prizes_per_kind = max(1, (prizes_per_round + prize_kind_count - 1) // prize_kind_count)
total_prize_slots = prizes_per_kind * prize_kind_count

symbol_time = 0.1  # Time of symbol show

# battle_mode_time = round_time * 0.9

# Player parameters.
prize_dis = d_height // 2

p_radius = 41
normal_radius = 36
in_angle_A = 180
in_angle_B = 0
in_step = 8
slow_mode = (6, 5)  # mode = (angle, step)
normal_mode = (6, 9)
fast_mode = (6, 13)
wait_mode = (0, 0)
# Other parameters.
# start_list = [1, 2, 3, 'GO!']
big_radius = 45
bandi_start_ticks = 0

# Logical top-HUD layout.
hud_height = 74
playfield_top = hud_height
playfield_bottom = d_height
playfield_rect = _p.Rect(0, playfield_top, d_width, playfield_bottom - playfield_top)
