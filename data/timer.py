import pygame as p


class Timer:
    """to call this class:
    timer1 = Timer(seconds, speed or delay)"""


    def __init__(self, sec,  delay=0):
        self.done = False
        self.start_ticks = 0
        self.passed_time = 0
        self.millis = 1000 * sec
        self.duration = self.millis
        self.delay = delay
        self.paused = False
        self.remaining = self.millis
        self.elapsed = 0
        self.elapsed_before_pause = 0

    def start(self):
        self.millis = self.duration
        self.start_ticks = p.time.get_ticks()
        self.done = False
        self.passed_time = 0
        self.paused = False
        self.remaining = self.millis
        self.elapsed = 0
        self.elapsed_before_pause = 0


    def check(self):
        if self.paused:
            return
        now_elapsed = self.elapsed_before_pause + (p.time.get_ticks() - self.start_ticks)
        self.elapsed = min(self.duration, max(0, now_elapsed))
        self.passed_time = self.elapsed
        self.remaining = max(0, self.duration - self.elapsed)
        if self.elapsed >= self.duration:
            self.done = True

    def pause(self):
        if not self.paused:
            elapsed = self.elapsed_before_pause + (p.time.get_ticks() - self.start_ticks)
            self.elapsed = min(self.duration, max(0, elapsed))
            self.elapsed_before_pause = self.elapsed
            self.remaining = max(0, self.duration - self.elapsed)
            self.paused = True

    def resume(self):
        if self.paused:
            self.start_ticks = p.time.get_ticks()
            self.done = self.elapsed >= self.duration
            self.paused = False




