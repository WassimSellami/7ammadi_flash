"""Decorative, distance-spaced shrinking circles. No territory changes."""
from collections import deque
from math import hypot
import pygame as p


class CircleTrail:
    def __init__(self, lifetime=0.4, limit=240):
        self.lifetime = lifetime
        self.circles = deque(maxlen=limit)
        self.anchors = {}
        self.stamps = {}

    def clear(self):
        self.circles.clear()
        self.anchors.clear()

    def update(self, dt, players, before, bounds):
        dt = max(0.0, min(dt, 0.1))
        self.circles = deque(
            ((x, y, r, color, age + dt) for x, y, r, color, age in self.circles
             if age + dt < self.lifetime), maxlen=self.circles.maxlen)
        shared_jump = any(getattr(player, 'jumping', False) for player in players)
        for player, start in zip(players, before):
            key = id(player)
            end = (float(player.x), float(player.y))
            dx, dy = end[0] - start[0], end[1] - start[1]
            distance = hypot(dx, dy)
            blocked = shared_jump or getattr(player, 'beaten', False) or getattr(player, 'jumping_to_wall', False)
            if blocked or distance > max(bounds.size) * 0.08:
                self.anchors.pop(key, None)
                continue
            if distance < 0.01:
                continue
            ux, uy = dx / distance, dy / distance
            radius = max(3.0, player.radius * 0.25)
            spacing = max(5.0, radius * 1.6)
            anchor = self.anchors.get(key, start)
            ax, ay = anchor
            length = hypot(end[0] - ax, end[1] - ay)
            if length > max(bounds.size) * 0.08:
                ax, ay = start
                length = distance
            if length > 0:
                vx, vy = (end[0] - ax) / length, (end[1] - ay) / length
                count = min(32, int(length / spacing))
                for index in range(1, count + 1):
                    sx, sy = ax + vx * spacing * index, ay + vy * spacing * index
                    offset = player.radius * 1.15
                    self.circles.append((sx - ux * offset, sy - uy * offset,
                                         radius, tuple(player.color)[:3], 0.0))
                self.anchors[key] = (ax + vx * spacing * count, ay + vy * spacing * count)

    def draw(self, surface, bounds):
        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(bounds))
        try:
            for x, y, initial, color, age in self.circles:
                progress = max(0.0, 1.0 - age / self.lifetime)
                radius = int(initial * progress)
                if radius < 1:
                    continue
                alpha = max(0, min(210, int(210 * progress)))
                alpha = (alpha // 24) * 24
                cache_key = (radius, color, alpha)
                stamp = self.stamps.get(cache_key)
                if stamp is None:
                    if len(self.stamps) >= 512:
                        self.stamps.clear()
                    stamp = p.Surface((radius * 2 + 2, radius * 2 + 2), p.SRCALPHA)
                    r, g, b = color
                    core = (
                        min(255, r + round((255 - r) * 0.25)),
                        min(255, g + round((255 - g) * 0.25)),
                        min(255, b + round((255 - b) * 0.25)),
                        alpha,
                    )
                    ring = (
                        max(0, round(r * 0.65)),
                        max(0, round(g * 0.65)),
                        max(0, round(b * 0.65)),
                        min(235, round(alpha * 0.9)),
                    )
                    p.draw.circle(stamp, core, (radius + 1, radius + 1), radius)
                    if radius >= 2:
                        p.draw.circle(stamp, ring, (radius + 1, radius + 1), radius, 1)
                    self.stamps[cache_key] = stamp
                surface.blit(stamp, (round(x) - radius - 1, round(y) - radius - 1))
        finally:
            surface.set_clip(old_clip)
