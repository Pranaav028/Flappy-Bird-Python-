"""
assets.py
---------
Visual and sound assets.

The project ships with a hand-drawn sprite set (background, bird frames, pipe
and ground) in the `Flappy bird img` folder.  If those files are missing, every
asset is generated procedurally instead, so the game still runs from a single
folder with no external images.

Why keep procedural fallbacks?  They make the mathematics visible: pipes are
rectangles, the bird is a circle for collision, and the ground is a horizontal
boundary.  The same collision model is used for both the image and fallback
versions.
"""

from __future__ import annotations

import io
import math
import os
import random
import wave
from array import array

import pygame

from settings import (
    ASSET_DIR,
    UI_ASSET_DIR,
    CLOUD,
    GROUND_DIRT,
    GROUND_DIRT_DARK,
    GROUND_GRASS,
    GROUND_GRASS_DARK,
    GROUND_H,
    GROUND_Y,
    HILL_FAR,
    HILL_NEAR,
    PIPE_CAP_PAD,
    PIPE_DARK,
    PIPE_EDGE,
    PIPE_GREEN,
    PIPE_LIGHT,
    PIPE_W,
    SKY_BOTTOM,
    SKY_TOP,
    SUN,
    VIRTUAL_H,
    VIRTUAL_W,
)
from utils import clamp, lerp, lerp_color


# ---------------------------------------------------------------------------
# Basic shapes
# ---------------------------------------------------------------------------
def make_sky() -> pygame.Surface:
    sky = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    for y in range(VIRTUAL_H):
        t = y / max(1, VIRTUAL_H - 1)
        pygame.draw.line(sky, lerp_color(SKY_TOP, SKY_BOTTOM, t), (0, y), (VIRTUAL_W, y))

    # Sun with a soft glow.
    sun_x, sun_y = int(VIRTUAL_W * 0.79), 108
    glow = pygame.Surface((240, 240), pygame.SRCALPHA)
    for radius in range(104, 0, -2):
        alpha = int(5 * (1.0 - radius / 104.0)) + 1
        pygame.draw.circle(glow, (255, 247, 200, alpha), (120, 120), radius)
    sky.blit(glow, (sun_x - 120, sun_y - 120))
    pygame.draw.circle(sky, SUN, (sun_x, sun_y), 27)
    pygame.draw.circle(sky, (255, 255, 230), (sun_x - 7, sun_y - 7), 10)

    # A few distant birds (small "v" shapes).
    for x, y, size in ((242, 150, 6), (267, 136, 4), (287, 158, 5)):
        pygame.draw.lines(
            sky,
            (66, 132, 154),
            False,
            [(x - size, y), (x, y - size * 0.55), (x + size, y)],
            2,
        )
    return sky


def make_cloud_layer() -> pygame.Surface:
    width, height = 720, 260
    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    rng = random.Random(11)
    for i in range(6):
        x = 40 + i * 118 + rng.randint(-15, 15)
        y = 30 + rng.randint(0, 110)
        scale = rng.uniform(0.65, 1.15)
        _cloud(layer, x, y, scale)
    return layer


def _cloud(surface, x, y, scale) -> None:
    shadow = (150, 206, 222, 70)
    white = (255, 255, 255, 225)
    parts = (
        (-22, 8, 34, 20),
        (-4, -2, 38, 28),
        (18, 4, 36, 22),
        (34, 10, 30, 18),
        (-34, 13, 26, 15),
    )
    for dx, dy, w, h in parts:
        pygame.draw.ellipse(
            surface,
            shadow,
            (
                int(x + dx * scale),
                int(y + (dy + 6) * scale),
                int(w * scale),
                int(h * scale),
            ),
        )
    for dx, dy, w, h in parts:
        pygame.draw.ellipse(
            surface,
            white,
            (
                int(x + dx * scale),
                int(y + dy * scale),
                int(w * scale),
                int(h * scale),
            ),
        )


def make_hills(colour, baseline: float, amplitude: float, period: float, phase: float) -> pygame.Surface:
    width = 720
    layer = pygame.Surface((width, VIRTUAL_H), pygame.SRCALPHA)
    points = []
    for x in range(0, width + 4, 4):
        wave = math.sin(math.tau * x / period + phase)
        wave2 = math.sin(math.tau * x / (period / 2.0) + phase * 1.7)
        y = baseline - amplitude * wave - amplitude * 0.35 * wave2
        points.append((x, y))
    polygon = points + [(width, VIRTUAL_H), (0, VIRTUAL_H)]
    pygame.draw.polygon(layer, colour, polygon)

    # A lighter ridge line gives the hills some depth.
    ridge = lerp_color(colour, (255, 255, 255), 0.22)
    pygame.draw.lines(layer, ridge, False, points, 3)

    # Simple bushes sitting on the ridge.
    rng = random.Random(int(period) + int(baseline))
    for i in range(7):
        bx = 40 + i * 100 + rng.randint(-18, 18)
        wave = math.sin(math.tau * bx / period + phase)
        wave2 = math.sin(math.tau * bx / (period / 2.0) + phase * 1.7)
        by = baseline - amplitude * wave - amplitude * 0.35 * wave2
        radius = rng.randint(6, 11)
        pygame.draw.circle(layer, lerp_color(colour, (0, 0, 0), 0.06), (bx, int(by + 2)), radius)
    return layer


def make_ground() -> pygame.Surface:
    tile_w = 48
    ground = pygame.Surface((tile_w, GROUND_H))
    for y in range(GROUND_H):
        t = y / max(1, GROUND_H - 1)
        pygame.draw.line(ground, lerp_color(GROUND_DIRT, GROUND_DIRT_DARK, t), (0, y), (tile_w, y))

    # Grass band.
    pygame.draw.rect(ground, GROUND_GRASS, (0, 0, tile_w, 13))
    pygame.draw.rect(ground, GROUND_GRASS_DARK, (0, 9, tile_w, 4))
    pygame.draw.line(ground, (170, 232, 122), (0, 1), (tile_w, 1), 2)

    # Little grass blades / notches.
    for x in range(0, tile_w, 8):
        pygame.draw.polygon(
            ground,
            (146, 220, 102),
            [(x + 2, 0), (x + 5, -4), (x + 8, 0)],
        )

    # Diagonal dirt stripes.
    for x in range(-GROUND_H, tile_w + GROUND_H, 18):
        pygame.draw.line(
            ground,
            (206, 166, 104),
            (x, GROUND_H),
            (x + GROUND_H, 14),
            3,
        )

    # Pebbles.
    rng = random.Random(4)
    for _ in range(5):
        px = rng.randint(3, tile_w - 4)
        py = rng.randint(24, GROUND_H - 5)
        pygame.draw.circle(ground, (184, 143, 88), (px, py), rng.randint(1, 2))
    return ground


# ---------------------------------------------------------------------------
# Bird
# ---------------------------------------------------------------------------
def make_bird_frame(wing_offset: int) -> pygame.Surface:
    """Draw the bird at 4x then downsample for smooth edges."""
    scale = 4
    w, h = 48, 40
    surf = pygame.Surface((w * scale, h * scale), pygame.SRCALPHA)

    def rect(x, y, rw, rh):
        return pygame.Rect(int(x * scale), int(y * scale), int(rw * scale), int(rh * scale))

    ink = (54, 46, 40)
    body = (255, 212, 64)
    body_light = (255, 234, 128)
    belly = (255, 244, 195)
    wing = (242, 178, 42)
    beak = (250, 150, 54)
    beak_dark = (212, 108, 34)

    # Tail.
    pygame.draw.polygon(
        surf,
        ink,
        [(8 * scale, 18 * scale), (0, 12 * scale), (2 * scale, 28 * scale), (9 * scale, 25 * scale)],
    )
    pygame.draw.polygon(
        surf,
        wing,
        [(8 * scale, 19 * scale), (2 * scale, 14 * scale), (4 * scale, 25 * scale), (9 * scale, 24 * scale)],
    )

    # Body outline + fill.
    pygame.draw.ellipse(surf, ink, rect(5, 5, 36, 30))
    pygame.draw.ellipse(surf, body, rect(7, 7, 32, 26))
    pygame.draw.ellipse(surf, body_light, rect(10, 8, 22, 13))

    # Belly.
    pygame.draw.ellipse(surf, ink, rect(12, 18, 23, 14))
    pygame.draw.ellipse(surf, belly, rect(13, 19, 21, 12))

    # Wing.
    wing_y = 17 + wing_offset * 4
    pygame.draw.ellipse(surf, ink, rect(9, wing_y - 1, 17, 12))
    pygame.draw.ellipse(surf, wing, rect(10, wing_y, 15, 10))
    pygame.draw.ellipse(surf, body_light, rect(13, wing_y + 1, 8, 4))

    # Eye.
    pygame.draw.ellipse(surf, ink, rect(28, 11, 10, 12))
    pygame.draw.ellipse(surf, (255, 255, 255), rect(29, 12, 8, 10))
    pygame.draw.ellipse(surf, (36, 38, 42), rect(32, 14, 5, 7))
    pygame.draw.circle(surf, (255, 255, 255), (33 * scale, 15 * scale), max(1, int(1.2 * scale)))

    # Beak.
    pygame.draw.polygon(
        surf,
        ink,
        [(35 * scale, 18 * scale), (47 * scale, 22 * scale), (35 * scale, 28 * scale)],
    )
    pygame.draw.polygon(
        surf,
        beak,
        [(36 * scale, 19 * scale), (45 * scale, 22 * scale), (36 * scale, 26 * scale)],
    )
    pygame.draw.line(
        surf,
        beak_dark,
        (37 * scale, 23 * scale),
        (44 * scale, 23 * scale),
        max(1, scale),
    )

    return pygame.transform.smoothscale(surf, (w, h))


# ---------------------------------------------------------------------------
# Pipes
# ---------------------------------------------------------------------------
def make_pipe_surface(height: int, top: bool) -> pygame.Surface:
    """Render one pipe half.  `top=True` means the cap is at the bottom."""
    height = max(24, int(height))
    scale = 3
    pad = PIPE_CAP_PAD
    out_w = PIPE_W + pad * 2
    surf = pygame.Surface((out_w * scale, height * scale), pygame.SRCALPHA)

    body_x = pad * scale
    body_w = PIPE_W * scale
    body_h = height * scale

    # Horizontal gradient: light on the left, dark on the right.
    for x in range(body_w):
        t = x / max(1, body_w - 1)
        if t < 0.20:
            colour = lerp_color(PIPE_LIGHT, PIPE_GREEN, t / 0.20)
        elif t > 0.80:
            colour = lerp_color(PIPE_GREEN, PIPE_DARK, (t - 0.80) / 0.20)
        else:
            colour = PIPE_GREEN
        pygame.draw.line(surf, colour, (body_x + x, 0), (body_x + x, body_h))

    # Vertical highlight and shadow.
    pygame.draw.rect(
        surf,
        (*PIPE_LIGHT, 150),
        (body_x + 8 * scale, 0, 5 * scale, body_h),
    )
    pygame.draw.rect(
        surf,
        (*PIPE_EDGE, 70),
        (body_x + body_w - 9 * scale, 0, 5 * scale, body_h),
    )
    pygame.draw.rect(surf, PIPE_EDGE, (body_x, 0, body_w, body_h), width=3 * scale)

    # Cap at the gap end.
    cap_h = 22 * scale
    cap_y = body_h - cap_h if top else 0
    cap_rect = pygame.Rect(2 * scale, cap_y, (out_w - 4) * scale, cap_h)
    pygame.draw.rect(surf, PIPE_EDGE, cap_rect, border_radius=6 * scale)
    inner = cap_rect.inflate(-3 * scale, -3 * scale)
    pygame.draw.rect(surf, PIPE_GREEN, inner, border_radius=5 * scale)
    pygame.draw.rect(
        surf,
        PIPE_LIGHT,
        (inner.x + 4 * scale, inner.y + 2 * scale, inner.w - 8 * scale, 4 * scale),
        border_radius=2 * scale,
    )
    pygame.draw.rect(
        surf,
        PIPE_DARK,
        (inner.x + 4 * scale, inner.bottom - 6 * scale, inner.w - 8 * scale, 4 * scale),
        border_radius=2 * scale,
    )

    # Rivets.
    for rx in (inner.x + 8 * scale, inner.right - 10 * scale):
        pygame.draw.circle(surf, PIPE_DARK, (rx, inner.centery), max(1, 2 * scale))
        pygame.draw.circle(surf, PIPE_LIGHT, (rx - scale, inner.centery - scale), max(1, scale))

    return pygame.transform.smoothscale(surf, (out_w, height))


# ---------------------------------------------------------------------------
# Sheet-style icons
# ---------------------------------------------------------------------------
def make_sheet_icon(kind: str, scale: int = 2) -> pygame.Surface:
    """Build a sound/mute icon in the sprite sheet's red-square style.

    The uploaded sheet has play and pause icons but no speaker icon, so this
    re-creates the same 13x14 framed button and swaps the glyph.
    """
    w, h = 13, 14
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    dark = (82, 49, 3)
    white = (253, 254, 253)
    red = (224, 97, 25)

    pygame.draw.rect(surf, dark, (0, 0, w, h))
    pygame.draw.rect(surf, white, (1, 1, w - 2, h - 2))
    pygame.draw.rect(surf, red, (2, 2, w - 4, h - 4))

    # Speaker body + cone (white, like the play/pause glyphs).
    pygame.draw.rect(surf, white, (3, 6, 2, 3))
    pygame.draw.polygon(surf, white, [(5, 6), (8, 3), (8, 11), (5, 8)])

    if kind == "sound":
        pygame.draw.arc(surf, white, pygame.Rect(8, 4, 4, 6), -1.0, 1.0, 1)
        pygame.draw.arc(surf, white, pygame.Rect(8, 2, 7, 10), -1.0, 1.0, 1)
    else:
        pygame.draw.line(surf, white, (9, 5), (12, 9), 1)
        pygame.draw.line(surf, white, (12, 5), (9, 9), 1)

    return pygame.transform.scale(surf, (w * scale, h * scale))


# ---------------------------------------------------------------------------
# Fonts and sound
# ---------------------------------------------------------------------------
class SoundBank:
    """Small synthesised sound effects (no external WAV files)."""

    def __init__(self) -> None:
        self.enabled = True
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if not pygame.mixer.get_init():
            return
        try:
            self.sounds["flap"] = self._tone(430, 800, 0.085, 0.35, decay=2.0, noise=0.04)
            self.sounds["score"] = self._tone(880, 1174, 0.15, 0.30, decay=1.2)
            self.sounds["hit"] = self._tone(170, 64, 0.26, 0.42, decay=1.3, noise=0.18, harmonics=0.5)
            self.sounds["click"] = self._tone(760, 980, 0.045, 0.22, decay=2.2)
        except (pygame.error, ValueError, OSError):
            self.sounds.clear()
        for sound in self.sounds.values():
            sound.set_volume(0.45)

    @staticmethod
    def _samples_to_sound(samples) -> pygame.mixer.Sound:
        pcm = array("h", (int(clamp(s, -1.0, 1.0) * 32767) for s in samples)).tobytes()
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(pcm)
        buffer.seek(0)
        return pygame.mixer.Sound(file=buffer)

    @classmethod
    def _tone(cls, f0, f1, duration, volume, decay=1.5, noise=0.0, harmonics=0.25):
        rate = 44100
        count = max(1, int(rate * duration))
        out = []
        phase = 0.0
        for i in range(count):
            t = i / count
            freq = lerp(f0, f1, t)
            phase += math.tau * freq / rate
            envelope = (1.0 - t) ** decay
            value = math.sin(phase) + harmonics * math.sin(phase * 2.0)
            if noise:
                value += random.uniform(-1.0, 1.0) * noise
            out.append(volume * envelope * value)
        return cls._samples_to_sound(out)

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled


class Assets:
    def __init__(self) -> None:
        # Optional hand-drawn sprites (bg.png, base.png, bird1-3.png, pipe.png).
        self.background = self._load_image("bg.png")
        self.pipe_image = self._load_image("pipe.png")

        if self.background is not None:
            self.background = pygame.transform.scale(
                self.background, (VIRTUAL_W, VIRTUAL_H)
            )
            # The image already contains the sky, clouds and hills.
            self.sky = None
            self.clouds = None
            self.hills_far = None
            self.hills_near = None
        else:
            self.sky = make_sky()
            self.clouds = make_cloud_layer()
            self.hills_far = make_hills(
                HILL_FAR, baseline=432, amplitude=30, period=240, phase=0.4
            )
            self.hills_near = make_hills(
                HILL_NEAR, baseline=496, amplitude=38, period=180, phase=2.1
            )

        base = self._load_image("base.png")
        if base is not None:
            ground_w = max(1, round(base.get_width() * GROUND_H / base.get_height()))
            self.ground = pygame.transform.scale(base, (ground_w, GROUND_H))
        else:
            self.ground = make_ground()

        bird_images = [self._load_image(f"bird{index}.png") for index in (1, 2, 3)]
        if all(image is not None for image in bird_images):
            # Original sprites are 34x24; the 360x640 canvas is 1.25x the
            # classic 288x512 playfield, so a small upscale keeps proportions.
            self.bird_frames = [
                pygame.transform.scale(image, (43, 30)) for image in bird_images
            ]
        else:
            self.bird_frames = [make_bird_frame(i) for i in (-1, 0, 1)]

        # Dedicated UI PNGs avoid misaligned sprite-sheet crops.
        self.ui = self._load_ui()

        self._pipe_cache: dict[tuple[int, bool], pygame.Surface] = {}
        self._fonts: dict[tuple[int, bool, bool], pygame.font.Font] = {}
        self.sounds = SoundBank()

    @staticmethod
    def _load_image(name: str):
        """Load a PNG from ASSET_DIR, returning None when it is unavailable."""
        path = os.path.join(ASSET_DIR, name)
        if not os.path.isfile(path):
            return None
        try:
            image = pygame.image.load(path)
            try:
                return image.convert_alpha()
            except pygame.error:
                return image
        except pygame.error:
            return None

    # ------------------------------------------------------------------
    # UI sprite sheet
    # ------------------------------------------------------------------
    def _load_ui(self) -> dict[str, pygame.Surface]:
        """Load *individual* optional UI PNGs from ui_assets/.

        Never slice the old all-in-one sprite sheet: its crop coordinates did
        not match the supplied artwork and displayed unrelated sprites over
        the game-over panel. Each element now has its own dedicated PNG.
        Missing or invalid images fall back to Pygame-drawn UI controls.
        """
        filenames = {
            "play_button": "play_button.png",
            "play_again_button": "play_again_button.png",
            "menu_button": "menu_button.png",
            "resume_button": "resume_button.png",
            "restart_button": "restart_button.png",
            "pause_icon": "pause_icon.png",
            "sound_icon": "sound_icon.png",
            "mute_icon": "mute_icon.png",
            "score_label": "score_label.png",
            "best_label": "best_label.png",
            "title_logo": "title_logo.png",
        }
        ui: dict[str, pygame.Surface] = {}
        for key, filename in filenames.items():
            image_path = os.path.join(UI_ASSET_DIR, filename)
            if not os.path.isfile(image_path):
                continue
            try:
                image = pygame.image.load(image_path)
                try:
                    image = image.convert_alpha()
                except pygame.error:
                    pass
                ui[key] = image
            except (OSError, pygame.error):
                continue
        return ui

    def font(self, size: int, bold: bool = False, mono: bool = False) -> pygame.font.Font:
        key = (size, bold, mono)
        if key not in self._fonts:
            if mono:
                name = "consolas,courier new,monospace"
                self._fonts[key] = pygame.font.SysFont(name, size)
            else:
                name = "segoeuiblack,segoeui,arial"
                self._fonts[key] = pygame.font.SysFont(name, size, bold=bold)
        return self._fonts[key]

    def _image_pipe(self, height: int) -> pygame.Surface:
        """Build one pipe half from the classic sprite (cap at the top)."""
        out_w = PIPE_W + PIPE_CAP_PAD * 2
        image = self.pipe_image
        image_w, image_h = image.get_size()
        cap_src_h = 24

        cap = image.subsurface((0, 0, image_w, cap_src_h))
        body = image.subsurface((2, cap_src_h, image_w - 4, image_h - cap_src_h))

        cap_h = max(1, round(cap_src_h * out_w / image_w))
        height = max(height, cap_h + 2)
        surface = pygame.Surface((out_w, height), pygame.SRCALPHA)
        surface.blit(
            pygame.transform.scale(cap, (out_w, cap_h)), (0, 0)
        )
        body_h = height - cap_h
        if body_h > 0:
            surface.blit(
                pygame.transform.scale(body, (PIPE_W, body_h)),
                (PIPE_CAP_PAD, cap_h),
            )
        return surface

    def pipe_surface(self, height: int, top: bool) -> pygame.Surface:
        key = (max(24, int(height)), bool(top))
        if key not in self._pipe_cache:
            if self.pipe_image is not None:
                surface = self._image_pipe(key[0])
                if key[1]:
                    # A top pipe is the same sprite flipped upside down.
                    surface = pygame.transform.flip(surface, False, True)
            else:
                surface = make_pipe_surface(key[0], key[1])
            self._pipe_cache[key] = surface
        return self._pipe_cache[key]
