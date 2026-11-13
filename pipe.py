"""
pipe.py
-------
A single pair of pipes (top + bottom) with a gap between them.

Collision geometry:
    The bird is a circle (x, y, r).
    Each pipe half is an axis-aligned rectangle.
    The shortest distance from the circle centre to the rectangle is
        dx = max(rect.left - x, 0, x - rect.right)
        dy = max(rect.top  - y, 0, y - rect.bottom)
        hit if dx^2 + dy^2 < r^2
    This is the point-to-rectangle form of the Euclidean distance formula
    used in slide 9 of the presentation.
"""

from __future__ import annotations

from settings import GROUND_Y, PIPE_CAP_PAD, PIPE_W


class Pipe:
    def __init__(self, x: float, gap_center: float, gap_size: float, assets) -> None:
        self.x = float(x)
        self.gap_center = float(gap_center)
        self.gap_size = float(gap_size)
        self.width = PIPE_W
        self.gap_top = max(1.0, self.gap_center - self.gap_size / 2.0)
        self.gap_bottom = min(GROUND_Y - 1.0, self.gap_center + self.gap_size / 2.0)
        self.scored = False

        self.top_surface = assets.pipe_surface(max(1, int(self.gap_top)), top=True)
        self.bottom_surface = assets.pipe_surface(
            max(1, int(GROUND_Y - self.gap_bottom)), top=False
        )

    @property
    def right(self) -> float:
        return self.x + self.width

    def update(self, dt: float, speed: float) -> None:
        # d = v * t  ->  x_new = x_old - v * dt
        self.x -= speed * dt

    def rects(self):
        """Collision rectangles: (x, y, width, height)."""
        return [
            (self.x, 0.0, self.width, self.gap_top),
            (self.x, self.gap_bottom, self.width, GROUND_Y - self.gap_bottom),
        ]

    def is_off_screen(self) -> bool:
        return self.right < -20.0

    def draw(self, surface) -> None:
        surface.blit(self.top_surface, (int(self.x) - PIPE_CAP_PAD, 0))
        surface.blit(
            self.bottom_surface,
            (int(self.x) - PIPE_CAP_PAD, int(self.gap_bottom)),
        )
