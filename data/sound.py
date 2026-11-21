import array
import sys
import wave

import pygame as p

from data.settings import (
    music_enabled_default,
    music_volume,
    rain_delay,
    rain_drops,
    sound_enabled_default,
)

p.init()
p.mixer.init(44100, -16, 1, 512)


_rain_cache = {}


# Sound-effect functions.
effects_enabled = sound_enabled_default
_effect_sounds = []


def _register_effect(sound, volume):
    sound.set_volume(volume if effects_enabled else 0.0)
    _effect_sounds.append((sound, volume))
    return sound


def _apply_effects_volume():
    for sound, volume in _effect_sounds:
        sound.set_volume(volume if effects_enabled else 0.0)


def toggle_effects():
    global effects_enabled
    effects_enabled = not effects_enabled
    _apply_effects_volume()
    return effects_enabled


def set_effects_enabled(enabled):
    if bool(enabled) != effects_enabled:
        toggle_effects()
    return effects_enabled


def _slowed_wav(path, duration):
    with wave.open(path, 'rb') as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        source_rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())

    if width != 2 or channels < 1:
        return None

    samples = array.array('h')
    samples.frombytes(raw)
    if sys.byteorder == 'big':
        samples.byteswap()

    if channels > 1:
        mono = array.array('h')
        for index in range(0, len(samples) - channels + 1, channels):
            mono.append(sum(samples[index:index + channels]) // channels)
    else:
        mono = samples

    mixer_info = p.mixer.get_init()
    if mixer_info:
        mixer_rate, mixer_format, mixer_channels = mixer_info
    else:
        mixer_rate, mixer_format, mixer_channels = source_rate, -16, 1

    if mixer_format != -16 or mixer_channels not in (1, 2):
        return None

    target = max(1, int(round(duration * mixer_rate)))

    if len(mono) > 1 and target > 1:
        step = (len(mono) - 1) / (target - 1)
        resampled = array.array('h')
        for index in range(target):
            position = index * step
            low = int(position)
            high = min(len(mono) - 1, low + 1)
            fraction = position - low
            value = int(mono[low] * (1.0 - fraction) + mono[high] * fraction)
            resampled.append(max(-32768, min(32767, value)))
    else:
        resampled = mono

    if mixer_channels == 2:
        stereo = array.array('h')
        for sample in resampled:
            stereo.append(sample)
            stereo.append(sample)
        resampled = stereo

    if sys.byteorder == 'big':
        resampled.byteswap()
    return resampled.tobytes()


def _build_rain(duration):
    key = round(max(0.05, duration), 2)
    rain = _rain_cache.get(key)
    if rain is None:
        buffer = _slowed_wav('data/sounds/gun.wav', key)
        if buffer is None:
            rain = Sound('gun.wav').load()
        else:
            rain = p.mixer.Sound(buffer=buffer)
        rain.set_volume(0.2)
        _effect_sounds.append((rain, 0.2))
        _rain_cache[key] = rain
    return rain


def play_rain(duration):
    if not effects_enabled:
        return
    _build_rain(duration).play()


def preload_rain(duration):
    try:
        _build_rain(duration)
    except (p.error, OSError, wave.Error, ValueError):
        pass


class Sound:
    def __init__(self, label):
        self.label = label

    def load(self):
        return p.mixer.Sound(f'data/sounds/{self.label}')


# Music functions.
_game_music_started = False
_game_music_playing = False
_game_music_paused = False
music_enabled = music_enabled_default
_intended_music_volume = music_volume

def _apply_music_volume():
    p.mixer.music.set_volume(
        _intended_music_volume if music_enabled else 0
    )

def toggle_music():
    global music_enabled
    music_enabled = not music_enabled
    _apply_music_volume()
    if not music_enabled:
        stop_game_music()
    return music_enabled


def set_music_enabled(enabled):
    if bool(enabled) != music_enabled:
        toggle_music()
    return music_enabled

def music_option_label():
    return "Music: ON" if music_enabled else "Music: OFF"

def play_m1(force_restart=False):
    """Start or restart the looping soundtrack."""
    global _game_music_started, _game_music_playing, _game_music_paused
    if not music_enabled:
        stop_game_music()
        return
    if _game_music_playing and not force_restart:
        return
    _apply_music_volume()
    if not _game_music_started or force_restart:
        p.mixer.music.load("data/sounds/play_music.wav")
        _game_music_started = True
    _apply_music_volume()
    p.mixer.music.play(-1)
    _game_music_playing = True
    _game_music_paused = False

def pause_game_music():
    global _game_music_playing, _game_music_paused
    if _game_music_started and _game_music_playing and not _game_music_paused:
        p.mixer.music.pause()
        _game_music_paused = True

def resume_game_music():
    global _game_music_playing, _game_music_paused
    if music_enabled and _game_music_started and _game_music_playing and _game_music_paused:
        _apply_music_volume()
        p.mixer.music.unpause()
        _game_music_paused = False

def stop_game_music():
    global _game_music_playing, _game_music_paused
    p.mixer.music.stop()
    _game_music_playing = False
    _game_music_paused = False

def is_game_music_paused():
    return _game_music_paused

def is_game_music_playing():
    return _game_music_playing

def shutdown_audio():
    p.mixer.music.stop()
    p.mixer.quit()


# Effects.
smash = _register_effect(Sound('smash.wav').load(), 1)
punch = _register_effect(Sound('punch.wav').load(), 1)
gun = _register_effect(Sound('gun.wav').load(), 0.2)
bomb = _register_effect(Sound('bomb.wav').load(), 0.2)
plop = _register_effect(Sound('beep.wav').load(), 0.3)
evil = _register_effect(Sound('evil.wav').load(), 0.4)
######
s_go = _register_effect(Sound('s_go.wav').load(), 0.2)
s_3 = _register_effect(Sound('s_3.wav').load(), 0.1)
s_2 = _register_effect(Sound('s_2.wav').load(), 0.1)
s_1 = _register_effect(Sound('s_1.wav').load(), 0.1)

# Build the common rain effect at load time so the first COLOR RAIN prize is hitch-free.
preload_rain(rain_delay * rain_drops)



