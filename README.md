# Flappy Bird — Computational Thinking × Mathematics

A complete Flappy Bird game written in **Python with Pygame**.
The game bundles your supplied bird, pipe, ground, background and title images
in `game_assets/` and `ui_assets/`. If an asset is missing, it automatically
falls back to procedural graphics and synthesised sound. It runs from a
single folder.

This game is the implementation of slide 11 of the team presentation:
> *“Coding: Start and complete the basic Flappy Bird game using Python.”*

The ZIP includes standalone UI assets and a regression test suite.
See `PATCH_NOTES.md` for the new layout and `EASY_MODE_NOTES.md` for the score 0–10 beginner difficulty tuning.

---

## 1. Quick start

### Option A — one click (Windows)

Double-click **`run_game.bat`**.

### Option B — command line

```bat
cd FlappyBird
python -m pip install -r requirements.txt
python main.py
```

### First-time setup (only if `.venv` is missing)

```bat
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> Python 3.11–3.13 with a compatible Pygame installation is recommended.

### Verify the build (optional)

```bat
.venv\Scripts\python.exe tests.py
.venv\Scripts\python.exe smoke_test.py
```

`tests.py` runs twenty-three independent checks of the physics, collisions, scoring,
difficulty scaling, persistence, letterbox mapping and sprite loading. It prints
`RESULT: 23/23 checks passed` when everything is correct and exits with a non-zero
status otherwise. Run the tests on your own machine after installing Pygame.

`smoke_test.py` runs completely headless (dummy video/audio drivers), drives the game
through menu → ready → playing → paused → maths mode → game over → restart, and writes
one PNG per state to `screenshots\_smoke\`. If the last line says `SMOKE TEST OK`, every
state transition and the renderer are working.

---

## 2. Controls

| Action | Key / Mouse |
|---|---|
| Flap | `Space`, `↑`, `W`, or left click |
| Start / retry | `Space` or click |
| Pause / resume | `P` or `Esc` |
| Restart instantly | `R` |
| Mute | `M` or the speaker button |
| **Maths mode** (live physics overlay) | `F1` |
| Save a PNG screenshot | `F12` |
| Toggle fullscreen | `F11` |
| Quit | `Esc` on the title screen, or close the window |

---

## 3. Project structure

```
FlappyBird/
├── main.py          window, letterbox scaling, global event loop
├── game.py          state machine + gameplay + all screens
├── bird.py          bird physics, impulse and rotation
├── pipe.py          pipe pair, scrolling and collision rectangles
├── particles.py     flap / score / impact particle system
├── assets.py        optional world sprites, standalone UI art, fonts, sounds
├── ui_assets/       replaceable PNG artwork for buttons and HUD
├── ui.py            text, panels, buttons, icons, medals
├── storage.py       high-score + mute persistence (JSON, atomic write)
├── settings.py      every tunable constant and the colour palette
├── utils.py         clamp / lerp / easing helpers
├── tests.py         20 automated checks of the mathematical model
├── requirements.txt
├── run_game.bat
├── smoke_test.py    headless test: drives every state, saves screenshots
├── screenshots/     press F12 in game to add images for the report
└── report_assets/   figure generator and report builder
    ├── make_figures.py    draws every report diagram from the game constants
    └── build_report.py    builds the DOCX from Project_Report_Template.docx
```

The split is deliberate **decomposition**: each module has one job, and `game.py`
only coordinates them.

---

## 4. The mathematics inside the game

### 4.1 Coordinate system

The logical canvas is **360 × 640 px**. The origin `(0, 0)` is the **top-left** corner,
`+x` points right and **`+y` points down**. Gravity is therefore **positive**.
Pipes use the same convention, so every value in the debug overlay is directly
checkable on screen.

### 4.2 Gravity and velocity (slides 7–8)

Each fixed physics step (`Δt = 1/120 s`) applies:

```
v_y  ←  v_y + g · Δt          (a = (0, g),  g starts at 560 px/s² and only increases after score 10)
y    ←  y  + v_y · Δt
```

Velocity is updated **before** position — this is **semi-implicit Euler**, which is
more stable than explicit Euler for gravity.

### 4.3 The flap is an impulse (projectile motion)

A flap sets `v_y = −445 px/s` instantly (negative because up is −y). Between flaps the
bird follows the parabola

```
y(t) = y₀ − v₀t + ½ g t²
```

The maximum height gained from one flap is

```
h = v₀² / (2g) = 445² / (2 × 760) ≈ 130.3 px at the opening gravity
```

Falling speed is clamped to `760 px/s` (terminal velocity), which keeps the simulation
stable and the game fair.

### 4.4 Horizontal motion (slides 9–10)

Pipes move left at constant speed `v`, so distance is simply

```
d = v · t        x_new = x_old − v · Δt
```

Speed starts at `102 px/s`, remains there through score 4, then grows by `1.1 px/s` per point, capped at `188 px/s`.
The gap starts at `200 px`, remains there through score 4, then shrinks by `0.8 px` per point, floored at `132 px`.
Gravity starts at `760 px/s²`, then increases by `4.5 px/s²` per point after score 4, capped at `1350 px/s²`.

### 4.5 Collision = Euclidean distance to a rectangle (slide 9)

The bird is treated as a **circle** of radius `r = 9.5 px`; each pipe half is an
axis-aligned rectangle. The closest point on the rectangle is

```
nearest_x = clamp(x, left, right)
nearest_y = clamp(y, top, bottom)
dx = x − nearest_x
dy = y − nearest_y
```

The circle and rectangle overlap when

```
dx² + dy² < r²
```

which is the squared form of

```
d = √[(x₂ − x₁)² + (y₂ − y₁)²]
```

`F1` draws the hitbox circle and every collision rectangle, so the viva demo can
show the geometry live.

### 4.6 Randomness and probability (conclusion slide)

The first gap centre is uniformly random in `[low, high]`, where
`low = margin + gap/2` and `high = ground − margin − gap/2`. Later gaps are

```
c_new = clamp(c_prev + U(−112, +112), low, high)
```

`U(a, b)` is a uniform random variable, so each new gap is a random variable whose
value is constrained to a fair playable band. The clamp guarantees that two adjacent
pipes can never require an impossible vertical jump.

### 4.7 Fixed timestep

Rendering runs at 60 FPS, but physics always advances in steps of `1/120 s`:

```
accumulator += frame_dt
while accumulator ≥ Δt:
    step_physics(Δt)
    accumulator −= Δt
```

This makes the trajectory identical on fast and slow machines (frame-rate
independence) and is a clean example of **algorithm design**.

---

## 5. Computational-thinking mapping

| Pillar | Where it appears |
|---|---|
| **Decomposition** | Bird, Pipe, Particles, Assets, UI, Storage modules |
| **Pattern recognition** | `input → update → collide → score → draw` loop every frame |
| **Abstraction** | `Bird.flap()` / `Bird.step_physics(dt)` hide sprite and maths details; `Pipe.rects()` hides rendering |
| **Algorithm design** | Explicit state machine, fixed timestep accumulator, broad-phase collision skip |

### State machine

```
MENU ──▶ READY ──▶ PLAYING ──▶ PAUSED
          ▲           │  ▲        │
          │           ▼  └────────┘
          └──── GAME_OVER ◀────────┘
```

Five states, each with its own update/draw/input rules. Adding a new screen
(e.g. a settings page) means adding one state, not rewriting the loop.

---

## 6. Feature checklist

- [x] Start screen with personal best and animated mascot
- [x] "Get ready" state before the first flap
- [x] Parabolic flapping, rotation based on `v_y`
- [x] Infinite random pipes with fair gap placement
- [x] Difficulty curve (speed up, gap shrink)
- [x] Score pop, particles, screen shake, medal tiers
- [x] Pause panel with resume / restart / menu
- [x] Game-over card with score, best and medal
- [x] High score + mute saved to `data.json`
- [x] Uploaded classic sprites with a procedural fallback
- [x] Live maths overlay (`F1`) with `y`–`t` graph
- [x] Screenshot key (`F12`) for collecting report evidence
- [x] Resizable letterboxed window and fullscreen (`F11`)
- [x] Gameplay independent of frame rate (fixed timestep)
- [x] 20 automated checks covering every equation in the report

---

## 7. Suggested viva demo flow

1. Open the game on the **menu** — explain the title, best score and controls.
2. Press `F1` and start a run. Point at the live `y`, `v_y`, `g`, `pipe v`, `gap`
   read-outs and the `y–t` graph; show the parabola after each flap.
3. Pause and point at the fixed-timestep explanation in this README.
4. Deliberately crash. Show the game-over card, medal and saved best score.
5. Mention the collision maths while the hitbox is visible (`F1`).
6. Close the game and reopen it to prove the high score persisted.

---

## 8. Tuning table (`settings.py`)

| Constant | Value | Meaning |
|---|---|---|
| `VIRTUAL_W`, `VIRTUAL_H` | 360 × 640 | logical canvas |
| `GRAVITY_START` | 560 px/s² | starting `g` for scores 0–10 |
| `FLAP_VELOCITY` | −445 px/s | impulse per flap |
| `MAX_FALL_SPEED` | 760 px/s | terminal velocity |
| `PHYSICS_DT` | 1/120 s | fixed step |
| `PIPE_GAP_START` | 200 px | starting gap |
| `PIPE_GAP_MIN` | 132 px | hardest gap |
| `PIPE_SPEED_START` | 102 px/s | starting scroll speed |
| `PIPE_SPEED_MAX` | 188 px/s | fastest scroll speed |
| `PIPE_MAX_SHIFT` | 112 px | max vertical jump between gaps |
| `BIRD_HITBOX_RADIUS` | 9.5 px | forgiving circle radius |

---

## 9. Report evidence

Press `F12` at any moment to save a screenshot into `screenshots/`. Useful captures:

- title screen,
- `F1` maths overlay mid-flight,
- a near-miss showing the hitbox,
- game-over card with medal and best score.

These images satisfy the “testing / output screenshots” section of the project report.

### Rebuilding the report

The report is generated from the official template, so every figure and table can be
reproduced from the finished program:

```bat
.venv\Scripts\python.exe report_assets\make_figures.py
.venv\Scripts\python.exe report_assets\build_report.py
```

`make_figures.py` draws the coordinate-system, trajectory, collision, random-gap,
architecture, state-machine, asset-sheet and difficulty diagrams using the constants
from `settings.py`. `build_report.py` copies the styles, page setup, footer and logo from
`..\Project_Report_Template.docx`, writes the full report body, and saves
`..\FLAPPY BIRD - PROJECT REPORT.docx`.

After building, open the DOCX in Word once (or update fields) so the table of contents
and page numbers are filled in.
