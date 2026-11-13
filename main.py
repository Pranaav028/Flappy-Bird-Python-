"""
main.py
-------
Entry point for the Flappy Bird project.

Responsibilities kept intentionally small (single responsibility principle):
    * create the OS window (resizable, letterboxed)
    * own the global event loop
    * forward events and the frame delta to the Game class

Everything about gameplay, drawing and mathematics lives in game.py and the
supporting modules.

Run with:
    .venv\\Scripts\\python.exe main.py
"""

from __future__ import annotations

import sys

import pygame

from game import Game
from settings import FPS, VIRTUAL_H, VIRTUAL_W

WINDOW_TITLE = "Flappy Bird  ·  Computational Thinking x Mathematics"

# Start at a comfortable size that fits a 1080p screen with room to spare.
DEFAULT_SCALE = 1.4


def create_window(fullscreen: bool = False) -> pygame.Surface:
    """Create the display surface, either windowed or borderless fullscreen."""
    if fullscreen:
        info = pygame.display.Info()
        size = (info.current_w, info.current_h)
        flags = pygame.FULLSCREEN | pygame.SCALED
    else:
        size = (int(VIRTUAL_W * DEFAULT_SCALE), int(VIRTUAL_H * DEFAULT_SCALE))
        flags = pygame.RESIZABLE
    return pygame.display.set_mode(size, flags)


def main() -> int:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    try:
        window = create_window(fullscreen=False)
    except pygame.error:
        # Some headless environments have no usable display driver.
        pygame.quit()
        print("Could not create a display window. Is a desktop session available?")
        return 1

    clock = pygame.time.Clock()
    game = Game()
    fullscreen = False
    running = True

    while running:
        # Keep the virtual/window coordinate mapping current before input.
        game.set_viewport(*game.viewport_for(window.get_size()))

        # --- events -------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = not fullscreen
                window = create_window(fullscreen=fullscreen)
            else:
                game.handle_event(event)

        if game.quit_requested:
            running = False
            break

        # --- update -------------------------------------------------------
        dt = clock.tick(FPS) / 1000.0
        game.update(dt)

        # --- draw ---------------------------------------------------------
        game.draw(window)
        pygame.display.flip()

    game.save()
    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
