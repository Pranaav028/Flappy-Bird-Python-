"""
bird.py
-------
The player-controlled bird.

Mathematical model used here (also in the report):

    v_y <- min(v_y + g * dt, v_terminal)      (velocity update)
    y   <- y + v_y * dt                        (position update)

This is *semi-implicit Euler*: velocity is updated first, then position is
advanced using the NEW velocity.  It is more stable than explicit Euler for
gravity-driven motion.

A flap is an impulse: it instantly sets v_y to FLAP_VELOCITY (a negative
number because +y points down).  The resulting path is a parabola.
"""

from __future__ import annotations

import math

import pygame

from settings import (
    BIRD_RADIUS,
    BIRD_START_Y,
    BIRD_X,
    FLAP_VELOCITY,
    GRAVITY_START,
    MAX_FALL_SPEED,
)
from utils import clamp


class Bird:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.x = BIRD_X
        self.y = BIRD_START_Y
        self.vy = 0.0
        self.angle = 0.0
        self.wing_phase = 0.0
        self.alive = True
        # The game updates this as the score rises.  Keeping it on the bird
        # means step_physics() can still be called on its own (e.g. in tests).
        self.gravity = GRAVITY_START

    def flap(self) -> None:
        """Apply the jump impulse (v_y becomes negative)."""
        self.vy = FLAP_VELOCITY
        self.wing_phase = 0.0

    def step_physics(self, dt: float, gravity: float | None = None) -> None:
        # v_new = v_old + a * dt, with a = (0, g).  `gravity` lets the game
        # pass the current score-dependent value; otherwise the bird's own
        # value (set on reset) is used.
        g = self.gravity if gravity is None else gravity
        self.vy = min(self.vy + g * dt, MAX_FALL_SPEED)
        # p_new = p_old + v_new * dt
        self.y += self.vy * dt

        # The top of the screen is a soft boundary; the bird cannot fly out.
        if self.y < BIRD_RADIUS:
            self.y = BIRD_RADIUS
            self.vy = max(0.0, self.vy)

        # Rotation is a visual function of vertical velocity.
        target = clamp(-25.0 + (self.vy / MAX_FALL_SPEED) * 115.0, -25.0, 90.0)
        self.angle += (target - self.angle) * min(1.0, 14.0 * dt)

    def update_visual(self, dt: float) -> None:
        speed = 28.0 if self.vy < 0 else 9.0
        self.wing_phase += dt * speed

    def draw(self, surface: pygame.Surface, assets) -> None:
        draw_bird_sprite(
            surface,
            assets,
            self.x,
            self.y,
            self.angle,
            scale=1.0,
            wing_phase=self.wing_phase,
            vy=self.vy,
        )


def draw_bird_sprite(
    surface: pygame.Surface,
    assets,
    x: float,
    y: float,
    angle: float,
    scale: float = 1.0,
    wing_phase: float = 0.0,
    vy: float = 0.0,
) -> None:
    """Draw the bird at any position (also used for the menu mascot)."""
    if vy < -40:
        # Fast wing beat while rising.
        index = int((math.sin(wing_phase) + 1.0) * 1.5) % 3
    elif vy > 260:
        # Glide with wings mostly level while falling quickly.
        index = 1
    else:
        index = int((math.sin(wing_phase) + 1.0) * 1.5) % 3

    frame = assets.bird_frames[index]
    if scale != 1.0:
        frame = pygame.transform.rotozoom(frame, 0.0, scale)
    rotated = pygame.transform.rotozoom(frame, -angle, 1.0)
    surface.blit(rotated, rotated.get_rect(center=(int(x), int(y))))
