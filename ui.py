"""
ui.py
-----
Reusable UI drawing helpers: text with outline/shadow, rounded panels,
buttons, icons and medals.

Keeping these widgets here is another example of decomposition: the game
state code describes *what* to show, while this module decides *how*.
"""

from __future__ import annotations

import math

import pygame

from settings import (
    ACCENT,
    ACCENT_DARK,
    ACCENT_LIGHT,
    BRONZE,
    CREAM,
    GOLD,
    INK,
    MEDAL_COLOURS,
    MEDAL_NAMES,
    PLATINUM,
    ROOKIE,
    SILVER,
    WHITE,
)
from utils import clamp, lerp_color


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color,
    center=None,
    topleft=None,
    outline: int = 0,
    outline_color=INK,
    shadow: bool = False,
    alpha: int = 255,
) -> pygame.Rect:
    """Render text with an optional outline, drop shadow and overall alpha."""
    base = font.render(text, True, color)
    rect = base.get_rect()
    if center is not None:
        rect.center = (int(center[0]), int(center[1]))
    elif topleft is not None:
        rect.topleft = (int(topleft[0]), int(topleft[1]))

    if outline <= 0 and not shadow and alpha >= 255:
        surface.blit(base, rect)
        return rect

    pad = max(1, outline) + (3 if shadow else 0)
    temp = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)

    if shadow:
        shadow_surf = font.render(text, True, (0, 0, 0))
        shadow_surf.set_alpha(80)
        temp.blit(shadow_surf, (pad, pad + 2))

    if outline > 0:
        outline_surf = font.render(text, True, outline_color)
        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                if dx == 0 and dy == 0:
                    continue
                temp.blit(outline_surf, (pad + dx, pad + dy))

    temp.blit(base, (pad, pad))
    if alpha < 255:
        temp.set_alpha(max(0, min(255, alpha)))
    surface.blit(temp, (rect.x - pad, rect.y - pad))
    return rect


# ---------------------------------------------------------------------------
# Panels
# ---------------------------------------------------------------------------
def draw_panel(
    surface: pygame.Surface,
    rect,
    fill,
    radius: int = 16,
    shadow: bool = True,
    border=None,
    border_width: int = 2,
    alpha: int = 255,
) -> pygame.Rect:
    """Draw a rounded rectangle with a soft shadow (and optional border)."""
    rect = pygame.Rect(rect)
    pad = 14
    temp = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
    local = pygame.Rect(pad, pad, rect.w, rect.h)

    if shadow:
        shade = pygame.Rect(local.x + 2, local.y + 5, local.w, local.h)
        pygame.draw.rect(temp, (12, 26, 36, 70), shade, border_radius=radius)

    body = (*fill, alpha) if len(fill) == 3 else (*fill[:3], min(alpha, fill[3]))
    pygame.draw.rect(temp, body, local, border_radius=radius)

    if border is not None:
        edge = (*border, min(alpha, 255)) if len(border) == 3 else border
        pygame.draw.rect(
            temp, edge, local, width=border_width, border_radius=max(0, radius - 1)
        )

    # Subtle top highlight for a glossy feel.
    if radius >= 8 and alpha > 180:
        highlight = pygame.Rect(local.x + 8, local.y + 2, local.w - 16, 2)
        pygame.draw.rect(temp, (255, 255, 255, 45), highlight, border_radius=1)

    surface.blit(temp, (rect.x - pad, rect.y - pad))
    return rect


# ---------------------------------------------------------------------------
# Icons
# ---------------------------------------------------------------------------
def draw_icon(surface: pygame.Surface, name: str, center, color, size: int = 16) -> None:
    """Small vector icons, so the project needs no image files."""
    cx, cy = center
    s = float(size)
    if name == "play":
        pygame.draw.polygon(
            surface,
            color,
            [(cx - s * 0.34, cy - s * 0.5), (cx - s * 0.34, cy + s * 0.5), (cx + s * 0.52, cy)],
        )
    elif name == "pause":
        bar_w = max(3, int(s * 0.22))
        bar_h = max(8, int(s * 0.9))
        pygame.draw.rect(
            surface, color, (cx - s * 0.28 - bar_w / 2, cy - bar_h / 2, bar_w, bar_h), border_radius=2
        )
        pygame.draw.rect(
            surface, color, (cx + s * 0.28 - bar_w / 2, cy - bar_h / 2, bar_w, bar_h), border_radius=2
        )
    elif name == "sound":
        _speaker(surface, cx, cy, s, color)
        for radius in (s * 0.3, s * 0.5):
            rect = pygame.Rect(cx - radius * 0.55, cy - radius, radius * 1.7, radius * 2)
            pygame.draw.arc(surface, color, rect, -0.95, 0.95, 2)
    elif name == "mute":
        _speaker(surface, cx, cy, s, color)
        pygame.draw.line(
            surface, color, (cx + s * 0.28, cy - s * 0.3), (cx + s * 0.62, cy + s * 0.3), 3
        )
        pygame.draw.line(
            surface, color, (cx + s * 0.62, cy - s * 0.3), (cx + s * 0.28, cy + s * 0.3), 3
        )
    elif name == "home":
        pygame.draw.polygon(
            surface,
            color,
            [
                (cx, cy - s * 0.48),
                (cx + s * 0.52, cy - s * 0.02),
                (cx + s * 0.38, cy - s * 0.02),
                (cx + s * 0.38, cy + s * 0.46),
                (cx - s * 0.38, cy + s * 0.46),
                (cx - s * 0.38, cy - s * 0.02),
                (cx - s * 0.52, cy - s * 0.02),
            ],
        )
    elif name == "restart":
        rect = pygame.Rect(cx - s * 0.46, cy - s * 0.46, s * 0.92, s * 0.92)
        pygame.draw.arc(surface, color, rect, 0.25, 4.8, 2)
        pygame.draw.polygon(
            surface,
            color,
            [
                (cx + s * 0.3, cy - s * 0.56),
                (cx + s * 0.62, cy - s * 0.32),
                (cx + s * 0.2, cy - s * 0.2),
            ],
        )
    elif name == "trophy":
        pygame.draw.rect(surface, color, (cx - s * 0.28, cy + s * 0.2, s * 0.56, s * 0.22), border_radius=2)
        pygame.draw.rect(surface, color, (cx - s * 0.08, cy - s * 0.05, s * 0.16, s * 0.3))
        pygame.draw.polygon(
            surface,
            color,
            [
                (cx - s * 0.38, cy - s * 0.45),
                (cx + s * 0.38, cy - s * 0.45),
                (cx + s * 0.25, cy + s * 0.05),
                (cx, cy + s * 0.18),
                (cx - s * 0.25, cy + s * 0.05),
            ],
        )
        for side in (-1, 1):
            rect = pygame.Rect(cx + side * s * 0.52 - s * 0.2, cy - s * 0.36, s * 0.4, s * 0.4)
            pygame.draw.arc(surface, color, rect, -1.3 if side < 0 else 1.9, 1.3 if side < 0 else 4.4, 2)
    elif name == "close":
        pygame.draw.line(surface, color, (cx - s * 0.4, cy - s * 0.4), (cx + s * 0.4, cy + s * 0.4), 3)
        pygame.draw.line(surface, color, (cx + s * 0.4, cy - s * 0.4), (cx - s * 0.4, cy + s * 0.4), 3)


def _speaker(surface, cx, cy, s, color) -> None:
    pygame.draw.polygon(
        surface,
        color,
        [
            (cx - s * 0.46, cy - s * 0.18),
            (cx - s * 0.24, cy - s * 0.18),
            (cx - s * 0.02, cy - s * 0.45),
            (cx - s * 0.02, cy + s * 0.45),
            (cx - s * 0.24, cy + s * 0.18),
            (cx - s * 0.46, cy + s * 0.18),
        ],
    )


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------
class Button:
    """A rounded button with hover/pressed states and an optional icon."""

    def __init__(
        self,
        rect,
        label: str = "",
        color=ACCENT,
        text_color=WHITE,
        radius: int = 13,
        font_size: int = 18,
        icon: str | None = None,
        icon_color=None,
        border=None,
        shadow: bool = True,
        image: pygame.Surface | None = None,
        fit: bool = False,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.text_color = text_color
        self.radius = radius
        self.font_size = font_size
        self.icon = icon
        self.icon_color = icon_color or text_color
        self.border = border
        self.shadow = shadow
        self.image = image
        self.fit = fit
        self.hovered = False
        self.pressed = False

    def hit(self, pos) -> bool:
        return self.rect.collidepoint(pos)

    def update(self, mouse_pos, mouse_down: bool) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)
        self.pressed = self.hovered and mouse_down

    def draw(self, surface: pygame.Surface, assets) -> None:
        rect = self.rect.move(0, 2 if self.pressed else 0)

        # Image-backed buttons use the uploaded sheet artwork.  The procedural
        # panel below remains the fallback when the sheet is unavailable.
        if self.image is not None:
            image = self.image
            if self.fit and image.get_size() != rect.size:
                image = pygame.transform.smoothscale(image, rect.size)
            image_rect = image.get_rect(center=rect.center)
            surface.blit(image, image_rect)
            if self.pressed or self.hovered:
                tint = pygame.Surface(image_rect.size, pygame.SRCALPHA)
                tint.fill((0, 0, 0, 55) if self.pressed else (255, 255, 255, 35))
                surface.blit(tint, image_rect)
            return

        base = self.color
        if self.pressed:
            base = lerp_color(self.color, (0, 0, 0), 0.14)
        elif self.hovered:
            base = lerp_color(self.color, (255, 255, 255), 0.16)

        draw_panel(
            surface,
            rect,
            base,
            radius=self.radius,
            shadow=self.shadow and not self.pressed,
            border=self.border,
            border_width=2,
        )

        font = assets.font(self.font_size, bold=True)
        if self.icon and self.label:
            text_w = font.size(self.label)[0]
            gap = 10
            icon_x = rect.centerx - text_w / 2 - gap
            icon_size = max(10, int(rect.h * 0.42))
            draw_icon(surface, self.icon, (icon_x, rect.centery), self.icon_color, icon_size)
            draw_text(
                surface,
                self.label,
                font,
                self.text_color,
                center=(rect.centerx + gap * 0.7, rect.centery),
                shadow=True,
            )
        elif self.icon:
            icon_size = max(10, int(rect.h * 0.48))
            draw_icon(surface, self.icon, rect.center, self.icon_color, icon_size)
        elif self.label:
            draw_text(
                surface,
                self.label,
                font,
                self.text_color,
                center=rect.center,
                shadow=True,
            )


# ---------------------------------------------------------------------------
# Medal
# ---------------------------------------------------------------------------
def _star_points(cx: float, cy: float, outer: float, inner: float, points: int = 5):
    result = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / points
        result.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return result


def draw_medal(surface: pygame.Surface, center, radius: int, tier: int) -> None:
    tier = max(0, min(len(MEDAL_COLOURS) - 1, tier))
    colour = MEDAL_COLOURS[tier]
    cx, cy = center

    # Ribbon behind the medal.
    ribbon = lerp_color(colour, (0, 0, 0), 0.18)
    pygame.draw.polygon(
        surface,
        ribbon,
        [(cx - radius * 0.55, cy - radius * 0.95), (cx - radius * 0.12, cy - radius * 0.2), (cx - radius * 0.55, cy - radius * 0.05)],
    )
    pygame.draw.polygon(
        surface,
        ribbon,
        [(cx + radius * 0.55, cy - radius * 0.95), (cx + radius * 0.12, cy - radius * 0.2), (cx + radius * 0.55, cy - radius * 0.05)],
    )

    pygame.draw.circle(surface, lerp_color(colour, (0, 0, 0), 0.3), (int(cx), int(cy)), radius)
    pygame.draw.circle(surface, colour, (int(cx), int(cy)), max(1, radius - 2))
    pygame.draw.circle(
        surface,
        lerp_color(colour, (255, 255, 255), 0.35),
        (int(cx), int(cy)),
        max(1, radius - 7),
    )
    pygame.draw.circle(surface, lerp_color(colour, (0, 0, 0), 0.25), (int(cx), int(cy)), max(1, radius - 11), 2)

    pygame.draw.polygon(
        surface,
        lerp_color(colour, (0, 0, 0), 0.38),
        _star_points(cx, cy, radius * 0.55, radius * 0.24),
    )

    # Small shine.
    shine = (int(cx - radius * 0.35), int(cy - radius * 0.38))
    pygame.draw.circle(surface, (255, 255, 255), shine, max(1, int(radius * 0.1)))


def medal_name(tier: int) -> str:
    return MEDAL_NAMES[max(0, min(len(MEDAL_NAMES) - 1, tier))]
