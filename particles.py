"""
particles.py
------------
A lightweight particle system for game feel: flap puffs, score sparkles and
feathers on impact.  No image assets are required.
"""

from __future__ import annotations

import math
import random

import pygame

from utils import clamp, lerp_color


class Particle:
    __slots__ = (
        "x",
        "y",
        "px",
        "py",
        "vx",
        "vy",
        "life",
        "max_life",
        "size",
        "colour",
        "gravity",
        "drag",
        "kind",
    )

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        life: float,
        size: float,
        colour,
        gravity: float,
        drag: float,
        kind: str,
    ) -> None:
        self.x = x
        self.y = y
        self.px = x
        self.py = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.colour = colour
        self.gravity = gravity
        self.drag = drag
        self.kind = kind

    def update(self, dt: float) -> None:
        self.px, self.py = self.x, self.y
        self.vy += self.gravity * dt
        self.vx *= max(0.0, 1.0 - self.drag * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface: pygame.Surface) -> None:
        t = clamp(self.life / max(self.max_life, 0.001), 0.0, 1.0)
        if self.kind == "spark":
            colour = lerp_color(self.colour, (255, 255, 255), 0.35 * t)
            end = (int(self.x - self.vx * 0.018), int(self.y - self.vy * 0.018))
            pygame.draw.line(surface, colour, (int(self.x), int(self.y)), end, max(1, int(2 * t)))
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), max(1, int(1.5 * t)))
        elif self.kind == "feather":
            colour = lerp_color(self.colour, (210, 230, 235), 0.25 * (1.0 - t))
            radius = max(1, int(self.size * t))
            pygame.draw.ellipse(
                surface,
                colour,
                (int(self.x) - radius, int(self.y) - radius // 2, radius * 2, max(2, radius)),
            )
        else:
            colour = lerp_color(self.colour, (235, 250, 250), 0.2 * (1.0 - t))
            radius = max(1, int(self.size * (0.35 + 0.65 * t)))
            pygame.draw.circle(surface, colour, (int(self.x), int(self.y)), radius)


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def clear(self) -> None:
        self.particles.clear()

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)
        self.particles = [p for p in self.particles if p.life > 0.0]

    def draw(self, surface: pygame.Surface) -> None:
        for particle in self.particles:
            particle.draw(surface)

    # ------------------------------------------------------------------
    # Emitters
    # ------------------------------------------------------------------
    def flap(self, x: float, y: float) -> None:
        for _ in range(6):
            self.particles.append(
                Particle(
                    x + random.uniform(-8, 2),
                    y + random.uniform(-4, 10),
                    random.uniform(-120, -40),
                    random.uniform(20, 110),
                    random.uniform(0.25, 0.5),
                    random.uniform(1.5, 3.2),
                    random.choice([(255, 255, 255), (208, 239, 247), (255, 236, 170)]),
                    gravity=180.0,
                    drag=1.8,
                    kind="circle",
                )
            )

    def score(self, x: float, y: float) -> None:
        for _ in range(12):
            angle = random.uniform(-math.pi, 0.0)
            speed = random.uniform(50, 170)
            self.particles.append(
                Particle(
                    x + random.uniform(-4, 4),
                    y + random.uniform(-4, 4),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(0.35, 0.65),
                    random.uniform(1.5, 3.0),
                    random.choice([(255, 236, 120), (255, 255, 255), (255, 190, 80)]),
                    gravity=360.0,
                    drag=0.5,
                    kind="spark",
                )
            )

    def hit(self, x: float, y: float) -> None:
        for _ in range(20):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(60, 280)
            self.particles.append(
                Particle(
                    x + random.uniform(-8, 8),
                    y + random.uniform(-8, 8),
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    random.uniform(0.45, 0.9),
                    random.uniform(2.5, 5.5),
                    random.choice([(255, 214, 64), (255, 244, 190), (240, 150, 60), (255, 255, 255)]),
                    gravity=760.0,
                    drag=0.9,
                    kind="feather",
                )
            )
