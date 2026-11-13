"""
tests.py
--------
Reproducible checks for every mathematical and behavioural claim made in the
project report.  Run head-less:

    .venv\\Scripts\\python.exe tests.py

The script prints one line per test so its output can be pasted into the
"Results and Discussion" table of the report.
"""

from __future__ import annotations

import math
import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import storage  # noqa: E402
from game import Game, circle_rect_collision  # noqa: E402
from pipe import Pipe  # noqa: E402
from settings import (  # noqa: E402
    BIRD_HITBOX_RADIUS,
    DIFFICULTY_GRACE_SCORE,
    BIRD_START_Y,
    BIRD_X,
    FLAP_VELOCITY,
    GRAVITY_GAIN,
    GRAVITY_MAX,
    GRAVITY_START,
    GROUND_Y,
    MAX_FALL_SPEED,
    PHYSICS_DT,
    PIPE_GAP_MIN,
    PIPE_GAP_START,
    PIPE_MARGIN,
    PIPE_MAX_SHIFT,
    PIPE_SPEED_MAX,
    PIPE_SPEED_START,
    VIRTUAL_H,
    VIRTUAL_W,
)

RESULTS: list[tuple[str, str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    RESULTS.append((name, status, detail))
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol


def main() -> None:
    pygame.init()
    pygame.display.set_mode((VIRTUAL_W, VIRTUAL_H))
    game = Game()

    # 1. Initial state ------------------------------------------------------
    check("Initial state is MENU", game.state == game.MENU, game.STATE_NAMES[game.state])

    # 2. READY transition ---------------------------------------------------
    game.start_ready()
    check(
        "PLAY starts READY and resets the bird",
        game.state == game.READY
        and close(game.bird.y, BIRD_START_Y)
        and close(game.bird.vy, 0.0)
        and game.score == 0,
        f"y={game.bird.y:.1f}, vy={game.bird.vy:.1f}",
    )

    # 3. First flap ---------------------------------------------------------
    game.begin_play()
    check(
        f"First flap enters PLAYING with v_y = {FLAP_VELOCITY:g}",
        game.state == game.PLAYING and close(game.bird.vy, FLAP_VELOCITY),
        f"v_y={game.bird.vy:.1f}",
    )

    # 4 & 5. Semi-implicit Euler -------------------------------------------
    bird = game.bird
    bird.reset()
    vy_before = bird.vy
    y_before = bird.y
    bird.step_physics(PHYSICS_DT)
    expected_vy = min(vy_before + GRAVITY_START * PHYSICS_DT, MAX_FALL_SPEED)
    expected_y = y_before + expected_vy * PHYSICS_DT
    check(
        "Gravity: v_new = v_old + g*dt",
        close(bird.vy, expected_vy),
        f"{vy_before:.1f} -> {bird.vy:.1f}",
    )
    check(
        "Position: y_new = y_old + v_new*dt",
        close(bird.y, expected_y),
        f"{y_before:.1f} -> {bird.y:.3f}",
    )

    # 6. Flap impulse -------------------------------------------------------
    bird.flap()
    check(f"Flap impulse sets v_y = {FLAP_VELOCITY:g}", close(bird.vy, FLAP_VELOCITY), f"v_y={bird.vy:.1f}")

    # 7. Terminal velocity --------------------------------------------------
    bird.reset()
    bird.vy = 0.0
    for _ in range(600):
        bird.step_physics(PHYSICS_DT)
    check(
        "Terminal velocity is clamped at 760 px/s",
        bird.vy <= MAX_FALL_SPEED + 1e-9,
        f"v_y={bird.vy:.1f}",
    )

    # 8 & 9. Gap bounds and fairness shift ---------------------------------
    game.reset_round()
    game.state = game.PLAYING
    for _ in range(300):
        game.spawn_pipe()
    gaps_ok = all(
        p.gap_top >= PIPE_MARGIN - 1e-6 and p.gap_bottom <= GROUND_Y - PIPE_MARGIN + 1e-6
        for p in game.pipes
    )
    check("Random gap stays inside the fair-play band", gaps_ok, "300 pipes")

    shifts = [
        abs(b.gap_center - a.gap_center)
        for a, b in zip(game.pipes, game.pipes[1:])
    ]
    check(
        "Vertical shift between gaps <= 112 px",
        max(shifts) <= PIPE_MAX_SHIFT + 1e-6,
        f"max={max(shifts):.1f}",
    )

    # 10 & 11. Difficulty scaling ------------------------------------------
    game.score = 0
    start_speed, start_gap = game.pipe_speed(), game.current_gap()
    game.score = 100
    end_speed, end_gap = game.pipe_speed(), game.current_gap()
    check(
        f"Pipe speed scales {PIPE_SPEED_START:.0f} -> {PIPE_SPEED_MAX:.0f} px/s",
        close(start_speed, PIPE_SPEED_START) and close(end_speed, PIPE_SPEED_MAX),
        f"{start_speed:.0f} -> {end_speed:.0f}",
    )
    check(
        f"Gap shrinks {PIPE_GAP_START:.0f} -> {PIPE_GAP_MIN:.0f} px",
        close(start_gap, PIPE_GAP_START) and close(end_gap, PIPE_GAP_MIN),
        f"{start_gap:.0f} -> {end_gap:.0f}",
    )

    # Beginner 0-10: same low gravity, low speed and wide gap all the way.
    beginner_values = []
    for beginner_score in range(DIFFICULTY_GRACE_SCORE + 1):
        game.score = beginner_score
        beginner_values.append((game.current_gravity(), game.pipe_speed(), game.current_gap()))
    check(
        "Score 0-10 stays at beginner difficulty",
        DIFFICULTY_GRACE_SCORE == 10
        and all(values == beginner_values[0] for values in beginner_values)
        and close(beginner_values[0][0], GRAVITY_START)
        and close(beginner_values[0][1], PIPE_SPEED_START)
        and close(beginner_values[0][2], PIPE_GAP_START),
        f"g={beginner_values[0][0]:.0f}, speed={beginner_values[0][1]:.0f}, "
        f"gap={beginner_values[0][2]:.0f}",
    )

    game.score = 10
    g10, v10, gap10 = game.current_gravity(), game.pipe_speed(), game.current_gap()
    game.score = 11
    g11, v11, gap11 = game.current_gravity(), game.pipe_speed(), game.current_gap()
    check(
        "Difficulty starts increasing smoothly at score 11",
        close(g11 - g10, GRAVITY_GAIN)
        and g11 > g10 and v11 > v10 and gap11 < gap10
        and v11 < PIPE_SPEED_MAX and gap11 > PIPE_GAP_MIN,
        f"gravity +{g11-g10:.1f}, speed +{v11-v10:.2f}, gap {gap11-gap10:.2f}",
    )

    game.score = 0
    game.pipes.clear()
    game.spawn_pipe()
    check(
        "First pipe is positioned near the bird",
        abs(game.pipes[0].gap_center - BIRD_START_Y) <= 32.0 + 1e-6,
        f"center={game.pipes[0].gap_center:.1f}, bird={BIRD_START_Y:.1f}",
    )

    # 12. Circle-rectangle collision ---------------------------------------
    inside = circle_rect_collision(50, 50, 9.5, 40, 40, 30, 30)
    outside = circle_rect_collision(5, 5, 9.5, 40, 40, 30, 30)
    touching = circle_rect_collision(40 - 9.0, 55, 9.5, 40, 40, 30, 30)
    check(
        "Euclidean circle-rectangle test (inside/outside/touching)",
        inside and not outside and touching,
        f"inside={inside}, outside={outside}, touching={touching}",
    )

    # 13. Pipe collision ends the run --------------------------------------
    game.reset_round()
    game.state = game.PLAYING
    game.pipes = [Pipe(BIRD_X - 10, GROUND_Y - 100, 100, game.assets)]
    game.bird.y = 60.0
    game.step_physics(PHYSICS_DT)
    check(
        "Hitting a pipe triggers GAME OVER",
        game.state == game.GAME_OVER,
        game.STATE_NAMES[game.state],
    )

    # 14. Ground collision ends the run ------------------------------------
    game.reset_round()
    game.state = game.PLAYING
    game.bird.y = GROUND_Y - BIRD_HITBOX_RADIUS + 1.0
    game.step_physics(PHYSICS_DT)
    check(
        "Hitting the ground triggers GAME OVER",
        game.state == game.GAME_OVER,
        game.STATE_NAMES[game.state],
    )

    # 15. Scoring when a pipe is cleared -----------------------------------
    game.reset_round()
    game.state = game.PLAYING
    test_pipe = Pipe(BIRD_X - BIRD_HITBOX_RADIUS - 58 - 5, game.bird.y, 158, game.assets)
    game.pipes = [test_pipe]
    game.step_physics(PHYSICS_DT)
    check("Score increases after clearing a pipe", game.score == 1, f"score={game.score}")

    # 16. Pause / resume ----------------------------------------------------
    game.reset_round()
    game.state = game.PLAYING
    game.pause()
    paused_ok = game.state == game.PAUSED
    game.resume()
    check(
        "Pause and resume preserve the round",
        paused_ok and game.state == game.PLAYING,
        game.STATE_NAMES[game.state],
    )

    # 17. Persistence round-trip -------------------------------------------
    original_path = storage.DATA_PATH
    try:
        with tempfile.TemporaryDirectory() as folder:
            storage.DATA_PATH = os.path.join(folder, "data.json")
            storage.save_data({"high_score": 37, "muted": True})
            loaded = storage.load_data()
        persistence_ok = loaded == {"high_score": 37, "muted": True}
    finally:
        storage.DATA_PATH = original_path
    check("High score and mute persist as JSON", persistence_ok, str(loaded))

    # 18. Letterbox mapping -------------------------------------------------
    ox, oy, scale = game.viewport_for((720, 1280))
    game.set_viewport(ox, oy, scale)
    vx, vy = game.to_virtual((ox + 96 * scale, oy + 280 * scale))
    check(
        "Letterbox scaling maps window pixels back to the 360x640 canvas",
        close(scale, 2.0) and close(vx, 96.0, 1e-6) and close(vy, 280.0, 1e-6),
        f"scale={scale:.2f}, virtual=({vx:.1f}, {vy:.1f})",
    )

    # 19. Frame-rate independence ------------------------------------------
    def simulate(frame_dt: float, frames: int) -> float:
        g = Game()
        g.start_ready()
        g.begin_play()
        g.pipes.clear()
        g.particles.clear()
        g.bird.y = 100.0
        g.bird.vy = 0.0
        for _ in range(frames):
            # Avoid spawning pipes so only bird physics is compared.
            g.state = g.PLAYING
            g.update(frame_dt)
            g.pipes.clear()
        return g.bird.y

    y60 = simulate(1 / 60, 30)
    y120 = simulate(1 / 120, 60)
    check(
        "Fixed timestep gives frame-rate independent motion",
        abs(y60 - y120) < 0.05,
        f"60 fps y={y60:.3f}, 120 fps y={y120:.3f}",
    )

    # 20. Bundled UI and fallback sprites (standalone, no external art) -----
    assets = game.assets
    check(
        "Graphics and custom UI icons load without external sprite sheets",
        (assets.background is not None or assets.sky is not None)
        and len(assets.bird_frames) == 3
        and assets.pipe_surface(80, True).get_width() > 0
        and assets.ground.get_width() > 0
        and all(name in assets.ui for name in (
            "play_button", "play_again_button", "menu_button",
            "pause_icon", "sound_icon", "mute_icon",
            "score_label", "best_label")),
        f"birds={len(assets.bird_frames)}, ui={len(assets.ui)}, "
        f"ground={assets.ground.get_size()}",
    )

    pygame.quit()

    passed = sum(1 for _, status, _ in RESULTS if status == "PASS")
    print("-" * 72)
    print(f"RESULT: {passed}/{len(RESULTS)} checks passed")
    if passed != len(RESULTS):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
