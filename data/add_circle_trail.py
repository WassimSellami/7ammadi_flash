"""Run from the project root to install the trail. Edits files only; launches no game/tests."""
from pathlib import Path
import shutil

root = Path.cwd()
main = root / 'main.py'
source = main.read_text(encoding='utf-8')
if 'from data.circle_trail import CircleTrail' in source:
    raise SystemExit('Trail integration already exists; no files changed.')
replacements = [
    ('clock = p.time.Clock()', 'from data.circle_trail import CircleTrail\n\ncircle_trail = CircleTrail()\nclock = p.time.Clock()'),
    ('def reset_match():', 'def reset_match():'),
    ('    Game1.game = True', '    circle_trail.clear()\n    Game1.game = True'),
    ('while running:\n', 'while running:\n    trail_frame_state = state\n'),
    ('    elif state == "gameplay":\n        Game1.update_players(Screen1, Player_A, Player_B)',
     '    elif state == "gameplay":\n        trail_before = [(player.x, player.y) for player in (Player_A, Player_B)]\n        Game1.update_players(Screen1, Player_A, Player_B)'),
    ('        Screen1.draw_round_timeline(round_elapsed_ms)',
     '        trail_bounds = p.Rect(0, 0, d_width, playfield_bottom)\n        trail_dt = clock.get_time() / 1000.0 if trail_frame_state == "gameplay" else 0.0\n        circle_trail.update(trail_dt, (Player_A, Player_B), trail_before, trail_bounds)\n        circle_trail.draw(Screen1.window, trail_bounds)\n        for player in (Player_A, Player_B):\n            Screen1.window.blit(player.icon, player.icon.get_rect(center=(player.x, player.y)))\n        if Prize1.is_allowed and Prize1.icon is not None:\n            Prize1.show_prize(Screen1)\n        Screen1.draw_round_timeline(round_elapsed_ms)')
]
for old, new in replacements:
    if source.count(old) != 1:
        raise SystemExit('Cannot safely match integration anchor: ' + repr(old) + '. No files changed.')
    source = source.replace(old, new, 1)
module_source = Path(__file__).with_name('circle_trail.py')
backup = main.with_name('main.before_circle_trail.py')
if backup.exists():
    raise SystemExit('Backup already exists. No files changed.')
shutil.copy2(main, backup)
(root / 'data').mkdir(exist_ok=True)
shutil.copy2(module_source, root / 'data' / 'circle_trail.py')
main.write_text(source, encoding='utf-8')
print('Trail installed. Original main.py backed up. No game or tests launched.')
