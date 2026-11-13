"""Headless smoke test: drive the game through every state and save screenshots."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from game import Game  # noqa: E402
from settings import FPS, GROUND_Y, SCREENSHOT_DIR  # noqa: E402

OUT = os.path.join(SCREENSHOT_DIR, "_smoke")
os.makedirs(OUT, exist_ok=True)


def save(game: Game, name: str) -> None:
    game.draw_canvas()
    path = os.path.join(OUT, name + ".png")
    pygame.image.save(game.canvas, path)
    print("saved", path)


def autopilot(game: Game) -> None:
    """Aim for the next gap so screenshots show normal play, not a crash."""
    target = 320.0
    for pipe in game.pipes:
        if pipe.right > game.bird.x - 8:
            target = pipe.gap_center
            break
    if game.bird.y > target + 18 or game.bird.vy > 260:
        game.flap()


def main() -> None:
    pygame.init()
    pygame.display.set_mode((360, 640))
    game = Game()

    # Menu -------------------------------------------------------------
    for _ in range(30):
        game.update(1 / FPS)
    save(game, "01_menu")

    # Ready ------------------------------------------------------------
    game.start_ready()
    for _ in range(30):
        game.update(1 / FPS)
    save(game, "02_ready")

    # Playing ----------------------------------------------------------
    game.begin_play()
    for _ in range(95):
        autopilot(game)
        game.update(1 / FPS)
        if game.state != game.PLAYING:
            break
    assert game.state == game.PLAYING, game.state
    save(game, "03_playing")

    # Pause ------------------------------------------------------------
    game.pause()
    for _ in range(10):
        game.update(1 / FPS)
    assert game.state == game.PAUSED, game.state
    save(game, "04_paused")
    game.resume()

    # Debug / maths mode ----------------------------------------------
    game.debug = True
    for frame in range(170):
        autopilot(game)
        game.update(1 / FPS)
        if game.state != game.PLAYING:
            game.restart_now()
    assert game.state == game.PLAYING, game.state
    save(game, "05_debug")
    game.debug = False

    # Game over --------------------------------------------------------
    game.bird.y = GROUND_Y + 20
    game.update(1 / FPS)
    assert game.state == game.GAME_OVER, game.state
    for _ in range(60):
        game.update(1 / FPS)
    save(game, "06_game_over")

    # Restart path -----------------------------------------------------
    game.restart_now()
    for _ in range(30):
        autopilot(game)
        game.update(1 / FPS)
    assert game.state == game.PLAYING, game.state
    save(game, "07_restarted")

    pygame.quit()
    print("SMOKE TEST OK")


if __name__ == "__main__":
    main()
