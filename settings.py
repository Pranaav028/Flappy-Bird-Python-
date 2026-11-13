"""
settings.py
-----------
All tunable constants for the Flappy Bird project.

This file is deliberately kept separate so that the mathematical model
(gravity, velocity, gap size, pipe speed) can be explained and adjusted
in one place.  The report can quote these constants directly.

Coordinate system (important for the report):
    Origin (0, 0) is at the TOP-LEFT of the window.
    +x points right, +y points DOWN.
    Gravity is therefore +y (positive).
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data.json")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Bundled user-supplied bird, pipe, ground, and background artwork.
# The game automatically falls back to procedural graphics if any asset is missing.
ASSET_DIR = os.path.join(BASE_DIR, "game_assets")
UI_ASSET_DIR = os.path.join(BASE_DIR, "ui_assets")

# ---------------------------------------------------------------------------
# Display / simulation
# ---------------------------------------------------------------------------
VIRTUAL_W = 360
VIRTUAL_H = 640                 # logical canvas; the window scales it
GROUND_H = 88
GROUND_Y = VIRTUAL_H - GROUND_H

FPS = 60
PHYSICS_DT = 1.0 / 120.0        # fixed physics step (s)
MAX_FRAME_DT = 0.10             # avoid huge catch-up after a window drag

# ---------------------------------------------------------------------------
# Bird physics  (units: pixels and seconds)
# ---------------------------------------------------------------------------
# Gravity is not constant during a run: it starts gentle and ramps up with the
# score.  A low starting gravity makes the opening pipes forgiving, while the
# higher cap keeps the late game challenging.
GRAVITY_START = 560.0            # relaxed gravity for scores 0-10 (px/s^2)
GRAVITY_MAX = 1250.0            # late-game cap (px/s^2)
GRAVITY_GAIN = 7.0              # gravity ramps up per point from score 11 onward
DIFFICULTY_GRACE_SCORE = 10     # scores 0-10 all use the same easy settings
GRAVITY = GRAVITY_START         # backwards-compatible report symbol
FLAP_VELOCITY = -310.0          # gentler flap to avoid overshooting large early gaps
MAX_FALL_SPEED = 760.0          # terminal velocity (px/s)
BIRD_X = 96.0
BIRD_START_Y = 280.0
BIRD_RADIUS = 12.0
BIRD_HITBOX_RADIUS = 9.5        # slightly forgiving circle for fair collisions

# ---------------------------------------------------------------------------
# Pipes / difficulty
# ---------------------------------------------------------------------------
PIPE_W = 58
PIPE_CAP_PAD = 6                # visual cap overhang on each side
PIPE_GAP_START = 250.0          # extra-wide opening gap at scores 0-10
PIPE_GAP_MIN = 140.0            # playable hard-mode gap floor
PIPE_GAP_SHRINK = 1.35          # shrink gradually only after score 10
PIPE_SPEED_START = 90.0         # slow pipes for scores 0-10
PIPE_SPEED_MAX = 190.0
PIPE_SPEED_GAIN = 1.45          # gradual acceleration after score 10
PIPE_SPACING = 210.0            # more time between pipes, even for new players
PIPE_MARGIN = 48.0              # generous vertical play area for wide gaps
PIPE_MAX_SHIFT = 112.0          # maximum vertical shift at higher scores
PIPE_FIRST_X = VIRTUAL_W + 48  # extra preparation time before first pipe

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
SKY_TOP = (67, 178, 226)
SKY_BOTTOM = (188, 241, 247)
SUN = (255, 247, 200)
CLOUD = (255, 255, 255)
HILL_FAR = (119, 208, 179)
HILL_NEAR = (73, 181, 142)
GROUND_GRASS = (118, 204, 82)
GROUND_GRASS_DARK = (86, 170, 60)
GROUND_DIRT = (224, 186, 121)
GROUND_DIRT_DARK = (198, 157, 96)
PIPE_GREEN = (104, 201, 62)
PIPE_DARK = (54, 143, 37)
PIPE_LIGHT = (174, 236, 116)
PIPE_EDGE = (42, 108, 31)

INK = (38, 48, 58)
INK_SOFT = (76, 92, 104)
WHITE = (255, 255, 255)
CREAM = (255, 251, 240)
ACCENT = (255, 150, 64)         # warm orange for primary buttons
ACCENT_DARK = (220, 112, 36)
ACCENT_LIGHT = (255, 182, 112)
SECONDARY = (74, 164, 196)
SECONDARY_DARK = (52, 130, 158)
DANGER = (228, 86, 76)
GOLD = (247, 196, 70)
SILVER = (196, 205, 214)
BRONZE = (205, 137, 82)
PLATINUM = (174, 235, 238)
ROOKIE = (176, 186, 194)

# ---------------------------------------------------------------------------
# UI sizes
# ---------------------------------------------------------------------------
TITLE = "FLAPPY BIRD"
SUBTITLE = "COMPUTATIONAL THINKING  x  MATHEMATICS"
FOOTER = "Amrita School of AI  ·  Semester 1"

# Medal thresholds (score -> tier index)
MEDAL_THRESHOLDS = (5, 15, 25, 40)
MEDAL_NAMES = ("ROOKIE", "BRONZE", "SILVER", "GOLD", "PLATINUM")
MEDAL_COLOURS = (ROOKIE, BRONZE, SILVER, GOLD, PLATINUM)
