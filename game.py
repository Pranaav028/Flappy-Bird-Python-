"""
game.py
-------
The Flappy Bird state machine and gameplay.

States
------
    MENU      title screen
    READY     bird hovering, waiting for the first flap
    PLAYING   fixed-timestep physics, pipes, scoring, collisions
    PAUSED    frozen gameplay with a translucent panel
    GAME_OVER score card, medal and restart options

Computational-thinking mapping
------------------------------
    Decomposition      -> Bird, Pipe, ParticleSystem, UI and storage modules
    Pattern recognition-> the same update -> collide -> draw loop every frame
    Abstraction        -> Bird exposes flap()/step_physics(); Game does not
                          need to know how the sprite is drawn
    Algorithm design   -> fixed timestep + explicit state machine
"""

from __future__ import annotations

import math
import os
import random
import time

import pygame

from assets import Assets
from bird import Bird, draw_bird_sprite
from particles import ParticleSystem
from pipe import Pipe
from settings import (
    ACCENT,
    BIRD_HITBOX_RADIUS,
    BIRD_START_Y,
    FPS,
    DIFFICULTY_GRACE_SCORE,
    FOOTER,
    GRAVITY_GAIN,
    GRAVITY_MAX,
    GRAVITY_START,
    GROUND_Y,
    INK,
    MAX_FALL_SPEED,
    MAX_FRAME_DT,
    MEDAL_THRESHOLDS,
    PHYSICS_DT,
    PIPE_FIRST_X,
    PIPE_GAP_MIN,
    PIPE_GAP_SHRINK,
    PIPE_GAP_START,
    PIPE_MARGIN,
    PIPE_MAX_SHIFT,
    PIPE_SPACING,
    PIPE_SPEED_GAIN,
    PIPE_SPEED_MAX,
    PIPE_SPEED_START,
    SCREENSHOT_DIR,
    SECONDARY,
    SECONDARY_DARK,
    SUBTITLE,
    VIRTUAL_H,
    VIRTUAL_W,
    WHITE,
)
from storage import load_data, save_data
from ui import Button, draw_medal, draw_panel, draw_text, medal_name
from utils import clamp, ease_out_back, lerp, lerp_color


def circle_rect_collision(cx, cy, radius, rx, ry, rw, rh) -> bool:
    """Shortest-distance test between a circle and an axis-aligned rectangle."""
    nearest_x = clamp(cx, rx, rx + rw)
    nearest_y = clamp(cy, ry, ry + rh)
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy < radius * radius


class Game:
    MENU, READY, PLAYING, PAUSED, GAME_OVER = range(5)
    STATE_NAMES = {
        MENU: "MENU",
        READY: "READY",
        PLAYING: "PLAYING",
        PAUSED: "PAUSED",
        GAME_OVER: "GAME OVER",
    }

    def __init__(self) -> None:
        try:
            self.canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert()
        except pygame.error:
            self.canvas = pygame.Surface((VIRTUAL_W, VIRTUAL_H))

        self.assets = Assets()
        data = load_data()
        self.best = int(data["high_score"])
        self.muted = bool(data["muted"])
        self.assets.sounds.set_enabled(not self.muted)

        self.bird = Bird()
        self.pipes: list[Pipe] = []
        self.particles = ParticleSystem()

        self.state = self.MENU
        self.score = 0
        self.new_best = False
        self.medal_tier = 0
        self.time = 0.0
        self.ready_time = 0.0
        self.game_over_timer = 0.0
        self.acc = 0.0
        self.score_pop = 0.0
        self.shake = 0.0
        self.bg_offset = 0.0
        self.ground_offset = 0.0
        self.fps_smooth = float(FPS)
        self.debug = False
        self.trail: list[float] = []
        self.toast = ""
        self.toast_timer = 0.0
        self.quit_requested = False

        self.mouse = (0.0, 0.0)
        self.mouse_down = False
        self.viewport = (0.0, 0.0, 1.0)

        # Individual UI PNGs (in ui_assets/) replace the badly cropped sheet.
        # Missing PNGs fall back to clean Pygame-drawn widgets.
        sheet = self.assets.ui
        self.btn_play = Button(
            (82, 420, 196, 54), "PLAY", color=ACCENT, icon="play",
            font_size=22, radius=15, image=sheet.get("play_button"), fit=True,
        )
        self.btn_pause = Button(
            (VIRTUAL_W - 42, 10, 30, 30), "", color=SECONDARY_DARK,
            icon="pause", radius=9, shadow=False,
            image=sheet.get("pause_icon"), fit=True,
        )
        self.btn_mute = Button(
            (VIRTUAL_W - 78, 10, 30, 30), "", color=SECONDARY_DARK,
            icon="sound", radius=9, shadow=False,
            image=sheet.get("sound_icon"), fit=True,
        )
        self.btn_resume = Button(
            (90, 306, 180, 46), "RESUME", color=ACCENT,
            font_size=18, radius=12, image=sheet.get("resume_button"), fit=True,
        )
        self.btn_restart_pause = Button(
            (90, 360, 180, 46), "RESTART", color=SECONDARY,
            font_size=18, radius=12, image=sheet.get("restart_button"), fit=True,
        )
        self.btn_menu_pause = Button(
            (90, 414, 180, 46), "MENU", color=(109, 125, 144),
            font_size=18, radius=12, image=sheet.get("menu_button"), fit=True,
        )
        self.btn_again = Button(
            (69, 428, 222, 52), "PLAY AGAIN", color=ACCENT,
            icon="restart", font_size=19, radius=14,
            image=sheet.get("play_again_button"), fit=True,
        )
        self.btn_menu_over = Button(
            (69, 491, 222, 52), "MENU", color=(109, 125, 144),
            icon="home", font_size=19, radius=14,
            image=sheet.get("menu_button"), fit=True,
        )

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def reset_round(self) -> None:
        self.bird.reset()
        self.pipes.clear()
        self.particles.clear()
        self.trail.clear()
        self.score = 0
        self.acc = 0.0
        self.score_pop = 0.0
        self.shake = 0.0
        self.game_over_timer = 0.0
        self.ready_time = 0.0
        self.new_best = False
        self.medal_tier = 0
        self.toast_timer = 0.0

    def start_ready(self) -> None:
        self.reset_round()
        self.state = self.READY
        self.bird.y = BIRD_START_Y
        self.bird.angle = 0.0
        self.bird.vy = 0.0

    def begin_play(self) -> None:
        if self.state != self.READY:
            return
        self.state = self.PLAYING
        self.bird.flap()
        self.particles.flap(self.bird.x - 8, self.bird.y + 6)
        self.assets.sounds.play("flap")
        self.spawn_pipe()

    def restart_now(self) -> None:
        self.start_ready()
        self.begin_play()

    def to_menu(self) -> None:
        self.reset_round()
        self.state = self.MENU
        self.bird.y = BIRD_START_Y

    def pause(self) -> None:
        if self.state == self.PLAYING:
            self.state = self.PAUSED
            self.acc = 0.0
            self.assets.sounds.play("click")

    def resume(self) -> None:
        if self.state == self.PAUSED:
            self.state = self.PLAYING
            self.acc = 0.0
            self.assets.sounds.play("click")

    def game_over(self) -> None:
        if self.state != self.PLAYING:
            return
        self.state = self.GAME_OVER
        self.bird.alive = False
        self.shake = 9.0
        self.particles.hit(self.bird.x, self.bird.y)
        self.assets.sounds.play("hit")
        self.game_over_timer = 0.0
        self.new_best = self.score > self.best
        if self.new_best:
            self.best = self.score
            self.save()
        self.medal_tier = self.medal_for_score(self.score)

    def save(self) -> None:
        save_data({"high_score": self.best, "muted": self.muted})

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        self.assets.sounds.set_enabled(not self.muted)
        if not self.muted:
            self.assets.sounds.play("click")
        self.save()

    def screenshot(self) -> None:
        try:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
            filename = time.strftime("flappy_%Y%m%d_%H%M%S.png")
            pygame.image.save(self.canvas, os.path.join(SCREENSHOT_DIR, filename))
            self.toast = "Screenshot saved!"
            self.toast_timer = 1.8
        except (OSError, pygame.error):
            self.toast = "Screenshot failed"
            self.toast_timer = 1.8

    # ------------------------------------------------------------------
    # Gameplay maths
    # ------------------------------------------------------------------
    def difficulty_points(self) -> int:
        """Hold beginner settings for scores 0-10; ramp smoothly from 11."""
        return max(0, self.score - DIFFICULTY_GRACE_SCORE)

    def pipe_speed(self) -> float:
        return min(PIPE_SPEED_MAX, PIPE_SPEED_START + self.difficulty_points() * PIPE_SPEED_GAIN)

    def current_gap(self) -> float:
        return max(PIPE_GAP_MIN, PIPE_GAP_START - self.difficulty_points() * PIPE_GAP_SHRINK)

    def current_gravity(self) -> float:
        """Forgiving opening; gravity increases gradually after the warm-up."""
        return min(GRAVITY_MAX, GRAVITY_START + self.difficulty_points() * GRAVITY_GAIN)

    def spawn_pipe(self) -> None:
        gap = self.current_gap()
        half = gap * 0.5
        low = PIPE_MARGIN + half
        high = GROUND_Y - PIPE_MARGIN - half

        if self.pipes:
            previous = self.pipes[-1].gap_center
            # Early pipes vary less vertically, giving beginners time to learn.
            shift = min(PIPE_MAX_SHIFT, 38.0 + self.difficulty_points() * 0.85)
            center = clamp(previous + random.uniform(-shift, shift), low, high)
            x = self.pipes[-1].x + PIPE_SPACING
        else:
            # Start near the bird to avoid an unfair first obstacle.
            center = clamp(BIRD_START_Y + random.uniform(-32.0, 32.0), low, high)
            x = PIPE_FIRST_X

        self.pipes.append(Pipe(x, center, gap, self.assets))

    def medal_for_score(self, score: int) -> int:
        tier = 0
        for index, threshold in enumerate(MEDAL_THRESHOLDS):
            if score >= threshold:
                tier = index + 1
        return tier

    def check_pipe_collision(self) -> bool:
        for pipe in self.pipes:
            # Broad phase: skip pipes far away from the bird.
            if pipe.right < self.bird.x - 30 or pipe.x > self.bird.x + 30:
                continue
            for rect in pipe.rects():
                if circle_rect_collision(
                    self.bird.x,
                    self.bird.y,
                    BIRD_HITBOX_RADIUS,
                    *rect,
                ):
                    return True
        return False

    def step_physics(self, dt: float) -> None:
        self.bird.step_physics(dt, self.current_gravity())

        for pipe in self.pipes:
            pipe.update(dt, self.pipe_speed())

        if not self.pipes or self.pipes[-1].x <= VIRTUAL_W - PIPE_SPACING:
            self.spawn_pipe()

        self.pipes = [pipe for pipe in self.pipes if not pipe.is_off_screen()]

        # Score when the bird's leading edge passes the pipe's trailing edge.
        for pipe in self.pipes:
            if not pipe.scored and self.bird.x - BIRD_HITBOX_RADIUS > pipe.right:
                pipe.scored = True
                self.score += 1
                self.score_pop = 0.25
                self.particles.score(self.bird.x + 8, self.bird.y)
                self.assets.sounds.play("score")

        if self.debug:
            self.trail.append(self.bird.y)
            if len(self.trail) > 160:
                self.trail.pop(0)

        # Ground collision ends the run.
        if self.bird.y + BIRD_HITBOX_RADIUS >= GROUND_Y:
            self.bird.y = GROUND_Y - BIRD_HITBOX_RADIUS
            self.game_over()
            return

        if self.check_pipe_collision():
            self.game_over()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        dt = clamp(dt, 0.0, MAX_FRAME_DT)
        self.time += dt
        if dt > 0:
            self.fps_smooth = lerp(self.fps_smooth, 1.0 / dt, 0.08)
        self.score_pop = max(0.0, self.score_pop - dt)
        self.shake = max(0.0, self.shake - dt * 30.0)
        self.toast_timer = max(0.0, self.toast_timer - dt)
        if self.state != self.PAUSED:
            self.particles.update(dt)

        if self.state == self.PLAYING:
            scroll_speed = self.pipe_speed()
        elif self.state == self.MENU:
            scroll_speed = 26.0
        elif self.state == self.READY:
            scroll_speed = 42.0
        else:
            scroll_speed = 0.0

        self.bg_offset += scroll_speed * dt
        self.ground_offset += scroll_speed * dt

        if self.state == self.READY:
            self.ready_time += dt
            self.bird.y = BIRD_START_Y + math.sin(self.time * 3.0) * 6.0
            self.bird.angle = math.sin(self.time * 3.0) * 4.0
            self.bird.wing_phase += dt * 11.0
        elif self.state == self.PLAYING:
            self.acc += dt
            steps = 0
            while self.acc >= PHYSICS_DT and steps < 10:
                self.step_physics(PHYSICS_DT)
                self.acc -= PHYSICS_DT
                steps += 1
                if self.state != self.PLAYING:
                    self.acc = 0.0
                    break
            if steps >= 10:
                self.acc = 0.0
            self.bird.update_visual(dt)
        elif self.state == self.GAME_OVER:
            self.game_over_timer += dt
            # Let the bird fall to the ground after the hit.
            if self.bird.y < GROUND_Y - BIRD_HITBOX_RADIUS:
                self.bird.vy = min(self.bird.vy + self.current_gravity() * dt, MAX_FALL_SPEED)
                self.bird.y += self.bird.vy * dt
                self.bird.angle = min(90.0, self.bird.angle + 190.0 * dt)
                if self.bird.y > GROUND_Y - BIRD_HITBOX_RADIUS:
                    self.bird.y = GROUND_Y - BIRD_HITBOX_RADIUS
            self.bird.update_visual(dt)
        elif self.state == self.PAUSED:
            pass

        self.update_buttons()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def set_viewport(self, offset_x: float, offset_y: float, scale: float) -> None:
        self.viewport = (offset_x, offset_y, scale if scale > 0 else 1.0)

    def to_virtual(self, pos):
        ox, oy, scale = self.viewport
        return ((pos[0] - ox) / scale, (pos[1] - oy) / scale)

    def current_buttons(self) -> list[Button]:
        if self.state == self.MENU:
            return [self.btn_play, self.btn_mute]
        if self.state == self.READY:
            return [self.btn_mute]
        if self.state == self.PLAYING:
            return [self.btn_pause, self.btn_mute]
        if self.state == self.PAUSED:
            return [self.btn_resume, self.btn_restart_pause, self.btn_menu_pause, self.btn_mute]
        if self.state == self.GAME_OVER:
            if self.game_over_timer >= 0.45:
                return [self.btn_again, self.btn_menu_over, self.btn_mute]
            return [self.btn_mute]
        return []

    def update_buttons(self) -> None:
        # Menu sound toggle is below the large title instead of covering it.
        self.btn_mute.rect.topleft = ((315, 559) if self.state == self.MENU
                                      else (VIRTUAL_W - 78, 10))
        self.btn_mute.icon = "mute" if self.muted else "sound"
        if self.assets.ui:
            self.btn_mute.image = self.assets.ui.get(
                "mute_icon" if self.muted else "sound_icon"
            )
        hovering = False
        for button in self.current_buttons():
            button.update(self.mouse, self.mouse_down)
            hovering = hovering or button.hovered
        try:
            pygame.mouse.set_cursor(
                pygame.SYSTEM_CURSOR_HAND if hovering else pygame.SYSTEM_CURSOR_ARROW
            )
        except pygame.error:
            pass

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.mouse = self.to_virtual(event.pos)
            self.mouse_down = bool(event.buttons[0])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse = self.to_virtual(event.pos)
            self.mouse_down = True
            self.on_click(self.mouse)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.mouse = self.to_virtual(event.pos)
            self.mouse_down = False
        elif event.type == pygame.KEYDOWN:
            self.handle_key(event.key)

    def on_click(self, pos) -> None:
        for button in self.current_buttons():
            if button.hit(pos):
                self.activate(button)
                return

        if self.state == self.MENU:
            self.start_ready()
        elif self.state == self.READY:
            self.begin_play()
        elif self.state == self.PLAYING:
            self.flap()

    def activate(self, button: Button) -> None:
        self.assets.sounds.play("click")
        if button is self.btn_play:
            self.start_ready()
        elif button is self.btn_pause:
            self.pause()
        elif button is self.btn_mute:
            self.toggle_mute()
        elif button is self.btn_resume:
            self.resume()
        elif button is self.btn_restart_pause:
            self.restart_now()
        elif button is self.btn_menu_pause:
            self.to_menu()
        elif button is self.btn_again:
            self.restart_now()
        elif button is self.btn_menu_over:
            self.to_menu()

    def flap(self) -> None:
        if self.state == self.PLAYING:
            self.bird.flap()
            self.particles.flap(self.bird.x - 8, self.bird.y + 6)
            self.assets.sounds.play("flap")

    def handle_key(self, key: int) -> None:
        if key == pygame.K_F1:
            self.debug = not self.debug
            return
        if key == pygame.K_m:
            self.toggle_mute()
            return
        if key == pygame.K_F12:
            self.screenshot()
            return

        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            if self.state == self.MENU:
                self.start_ready()
            elif self.state == self.READY:
                self.begin_play()
            elif self.state == self.PLAYING:
                self.flap()
            elif self.state == self.PAUSED:
                self.resume()
            elif self.state == self.GAME_OVER and self.game_over_timer >= 0.45:
                self.restart_now()
        elif key in (pygame.K_p, pygame.K_ESCAPE):
            if self.state == self.PLAYING:
                self.pause()
            elif self.state == self.PAUSED:
                self.resume()
            elif self.state == self.GAME_OVER:
                self.to_menu()
            elif self.state == self.READY:
                self.to_menu()
            elif self.state == self.MENU:
                self.quit_requested = True
        elif key == pygame.K_r:
            if self.state in (self.PLAYING, self.PAUSED, self.GAME_OVER):
                self.restart_now()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def viewport_for(self, size):
        """Letterbox the 360x640 canvas inside an arbitrary window size."""
        win_w, win_h = size
        scale = min(win_w / VIRTUAL_W, win_h / VIRTUAL_H)
        draw_w = max(1, int(VIRTUAL_W * scale))
        draw_h = max(1, int(VIRTUAL_H * scale))
        ox = (win_w - draw_w) // 2
        oy = (win_h - draw_h) // 2
        return ox, oy, scale

    def draw(self, window: pygame.Surface) -> None:
        self.draw_canvas()

        win_w, win_h = window.get_size()
        ox, oy, scale = self.viewport_for((win_w, win_h))
        draw_w = max(1, int(VIRTUAL_W * scale))
        draw_h = max(1, int(VIRTUAL_H * scale))
        self.set_viewport(ox, oy, scale)

        window.fill((12, 20, 28))
        scaled = pygame.transform.smoothscale(self.canvas, (draw_w, draw_h))

        if self.shake > 0.5:
            ox += random.randint(-int(self.shake), int(self.shake))
            oy += random.randint(-int(self.shake), int(self.shake))
        window.blit(scaled, (ox, oy))

    def draw_canvas(self) -> pygame.Surface:
        self.draw_world()
        self.draw_ui()
        self.draw_buttons()
        if self.debug:
            self.draw_debug()
        self.draw_toast()
        return self.canvas

    def draw_world(self) -> None:
        c = self.canvas
        if self.assets.background is not None:
            c.blit(self.assets.background, (0, 0))
        else:
            c.blit(self.assets.sky, (0, 0))

            # Parallax clouds.
            cloud_w = self.assets.clouds.get_width()
            cloud_offset = int(self.bg_offset * 0.10) % cloud_w
            c.blit(self.assets.clouds, (-cloud_offset, 54))
            c.blit(self.assets.clouds, (cloud_w - cloud_offset, 54))

            # Parallax hills.
            for layer, factor in (
                (self.assets.hills_far, 0.22),
                (self.assets.hills_near, 0.44),
            ):
                width = layer.get_width()
                offset = int(self.bg_offset * factor) % width
                c.blit(layer, (-offset, 0))
                c.blit(layer, (width - offset, 0))

        for pipe in self.pipes:
            pipe.draw(c)

        # Scrolling ground.
        tile_w = self.assets.ground.get_width()
        offset = int(self.ground_offset) % tile_w
        for x in range(-tile_w, VIRTUAL_W + tile_w, tile_w):
            c.blit(self.assets.ground, (x - offset, GROUND_Y))

        if self.debug and len(self.trail) > 2:
            points = []
            count = len(self.trail)
            for index, y in enumerate(self.trail):
                points.append((self.bird.x - (count - 1 - index) * 0.45, y))
            pygame.draw.lines(c, (255, 98, 120), False, points, 2)

        self.particles.draw(c)

        if self.state == self.MENU:
            # The custom logo already includes the featured bird. Avoid
            # drawing a second bird on top of the title artwork.
            if self.assets.ui.get("title_logo") is None:
                draw_bird_sprite(
                    c, self.assets, VIRTUAL_W / 2, 235,
                    math.sin(self.time * 2.0) * 5.0,
                    scale=1.6, wing_phase=self.time * 8.0, vy=0.0,
                )
        else:
            self.bird.draw(c, self.assets)

        if self.debug:
            # Visualise the collision geometry used in the maths.
            pygame.draw.circle(
                c,
                (255, 72, 90),
                (int(self.bird.x), int(self.bird.y)),
                int(BIRD_HITBOX_RADIUS),
                1,
            )
            for pipe in self.pipes:
                for rect in pipe.rects():
                    pygame.draw.rect(c, (255, 72, 90), pygame.Rect(*rect), 1)

    def draw_ui(self) -> None:
        if self.state == self.MENU:
            self.draw_menu()
        elif self.state == self.READY:
            self.draw_ready()
        elif self.state == self.PLAYING:
            self.draw_playing()
        elif self.state == self.PAUSED:
            self.draw_playing()
            self.draw_pause()
        elif self.state == self.GAME_OVER:
            self.draw_game_over()

    def draw_buttons(self) -> None:
        for button in self.current_buttons():
            button.draw(self.canvas, self.assets)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def draw_menu(self) -> None:
        c = self.canvas
        logo = self.assets.ui.get("title_logo")
        if logo is not None:
            # Alpha-matted image provided by the user, fitted into a 336 x 270
            # hero area without distorting its original proportions.
            max_w, max_h = 336, 270
            scale = min(max_w / logo.get_width(), max_h / logo.get_height())
            dims = (max(1, int(logo.get_width() * scale)),
                    max(1, int(logo.get_height() * scale)))
            display_logo = pygame.transform.smoothscale(logo, dims)
            c.blit(display_logo, display_logo.get_rect(center=(180, 151)))
        else:
            draw_text(c, "FLAPPY", self.assets.font(52, bold=True), WHITE,
                      center=(180, 93), outline=3, shadow=True)
            draw_text(c, "BIRD", self.assets.font(55, bold=True), WHITE,
                      center=(180, 150), outline=3, shadow=True)

        draw_panel(c, (110, 307, 140, 64), (255, 249, 228), radius=14,
                   border=(255, 255, 255), alpha=244)
        label = self.assets.ui.get("best_label")
        if label is not None:
            tag = pygame.transform.smoothscale(label, (78, 24))
            c.blit(tag, tag.get_rect(center=(180, 323)))
        else:
            draw_text(c, "BEST", self.assets.font(12, bold=True), INK,
                      center=(180, 322))
        draw_text(c, str(self.best), self.assets.font(24, bold=True), INK,
                  center=(180, 351))

        draw_text(c, "SPACE / CLICK to flap", self.assets.font(11, bold=True),
                  WHITE, center=(180, 509), shadow=True)
        draw_text(c, "F12 saves a screenshot", self.assets.font(9),
                  (210, 238, 244), center=(180, 531), shadow=True)
        draw_text(c, "P pause  |  M mute  |  F1 maths", self.assets.font(9),
                  WHITE, center=(180, 551), shadow=True)
        draw_text(c, FOOTER, self.assets.font(8), WHITE,
                  center=(180, 604), shadow=True, alpha=210)

    def draw_ready(self) -> None:
        c = self.canvas
        self.draw_hud()

        draw_text(c, "GET READY", self.assets.font(34, bold=True), WHITE,
                  center=(180, 150), outline=3, shadow=True)
        draw_text(
            c,
            "PASS THE PIPES",
            self.assets.font(9, bold=True),
            (230, 250, 252),
            center=(180, 195),
            shadow=True,
            alpha=220,
        )

        draw_panel(
            c,
            (78, 404, 204, 66),
            (219, 218, 150),
            radius=14,
            shadow=True,
            border=(82, 55, 71),
            alpha=235,
        )
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
        draw_text(
            c,
            "TAP  /  SPACE",
            self.assets.font(21, bold=True),
            lerp_color(WHITE, (255, 236, 160), pulse),
            center=(180, 424),
            outline=3,
            outline_color=(82, 55, 71),
            shadow=True,
        )
        draw_text(
            c,
            "to flap",
            self.assets.font(10, bold=True),
            (82, 55, 71),
            center=(180, 450),
        )
        draw_text(
            c,
            "P pause   ·   M mute   ·   F1 maths",
            self.assets.font(8),
            WHITE,
            center=(180, 522),
            shadow=True,
            alpha=180,
        )

    def draw_playing(self) -> None:
        self.draw_hud()

    def draw_hud(self) -> None:
        """Clear live SCORE / BEST badges; no sprite-sheet crop artifacts."""
        c = self.canvas
        draw_panel(c, (10, 9, 88, 58), (24, 61, 78),
                   radius=12, shadow=False, border=(100, 187, 200), alpha=228)
        best_label = self.assets.ui.get("best_label")
        if best_label is not None:
            image = pygame.transform.smoothscale(best_label, (65, 20))
            c.blit(image, image.get_rect(center=(54, 24)))
        else:
            draw_text(c, "BEST", self.assets.font(10, bold=True), WHITE,
                      center=(54, 24))
        draw_text(c, str(self.best), self.assets.font(21, bold=True), WHITE,
                  center=(54, 48), shadow=True)

        pulse = self.score_pop / 0.25 if self.score_pop > 0 else 0.0
        score_label = self.assets.ui.get("score_label")
        if score_label is not None:
            image = pygame.transform.smoothscale(score_label, (80, 24))
            c.blit(image, image.get_rect(center=(180, 20)))
        else:
            draw_text(c, "SCORE", self.assets.font(12, bold=True), WHITE,
                      center=(180, 22), outline=1, shadow=True)
        draw_text(c, str(self.score), self.assets.font(43 + int(8 * pulse), bold=True),
                  WHITE, center=(180, 61), outline=3, shadow=True)

    def draw_pause(self) -> None:
        c = self.canvas
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((9, 23, 35, 170))
        c.blit(overlay, (0, 0))
        draw_panel(c, (54, 191, 252, 293), (255, 250, 233),
                   radius=23, border=(255, 255, 255), alpha=250)
        draw_text(c, "PAUSED", self.assets.font(31, bold=True), INK,
                  center=(180, 230))
        draw_text(c, "Ready for another flight?", self.assets.font(10),
                  (99, 112, 120), center=(180, 263))
        draw_text(c, "P / ESC to resume", self.assets.font(9),
                  (103, 113, 128), center=(180, 472))

    def _blit_faded(self, surface: pygame.Surface, pos, alpha: int) -> None:
        if alpha >= 255:
            self.canvas.blit(surface, pos)
            return
        temp = surface.copy()
        temp.set_alpha(max(0, min(255, alpha)))
        self.canvas.blit(temp, pos)

    def draw_game_over(self) -> None:
        """Self-contained result card, independent of any sprite sheet."""
        c = self.canvas
        shade = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        shade.fill((7, 18, 30, 183))
        c.blit(shade, (0, 0))

        t = clamp(self.game_over_timer / 0.38, 0.0, 1.0)
        ease = ease_out_back(t)
        offset = int((1.0 - ease) * 26)
        alpha = int(255 * min(1.0, t * 1.7))
        draw_text(c, "GAME OVER", self.assets.font(37, bold=True), WHITE,
                  center=(180, 108 + offset), outline=3,
                  shadow=True, alpha=alpha)

        # Results card ends at y=401. Buttons begin at y=428, so they cannot
        # cover the scoreboard even when the game-over entrance animates.
        card = pygame.Rect(34, 157 + offset, 292, 244)
        draw_panel(c, card, (255, 248, 228), radius=22, shadow=True,
                   border=(255, 255, 255), border_width=3, alpha=alpha)
        draw_text(c, "RUN RESULTS", self.assets.font(10, bold=True),
                  (95, 110, 117), center=(180, card.y + 20), alpha=alpha)

        score_label = self.assets.ui.get("score_label")
        best_label = self.assets.ui.get("best_label")
        if score_label is not None:
            tag = pygame.transform.smoothscale(score_label, (82, 24))
            self._blit_faded(tag, tag.get_rect(center=(108, card.y + 55)).topleft, alpha)
        else:
            draw_text(c, "SCORE", self.assets.font(11, bold=True), (80, 95, 105),
                      center=(108, card.y + 55), alpha=alpha)
        if best_label is not None:
            tag = pygame.transform.smoothscale(best_label, (82, 24))
            self._blit_faded(tag, tag.get_rect(center=(252, card.y + 55)).topleft, alpha)
        else:
            draw_text(c, "BEST", self.assets.font(11, bold=True), (80, 95, 105),
                      center=(252, card.y + 55), alpha=alpha)

        pygame.draw.line(c, (219, 213, 194), (180, card.y + 43),
                         (180, card.y + 122), 1)
        draw_text(c, str(self.score), self.assets.font(40, bold=True), INK,
                  center=(108, card.y + 99), alpha=alpha)
        draw_text(c, str(self.best), self.assets.font(40, bold=True), INK,
                  center=(252, card.y + 99), alpha=alpha)
        pygame.draw.line(c, (225, 218, 204), (62, card.y + 140),
                         (298, card.y + 140), 2)

        medal = pygame.Surface((86, 86), pygame.SRCALPHA)
        draw_medal(medal, (43, 43), 29, self.medal_tier)
        medal.set_alpha(alpha)
        c.blit(medal, (66, card.y + 146))
        draw_text(c, medal_name(self.medal_tier), self.assets.font(17, bold=True),
                  INK, center=(226, card.y + 180), alpha=alpha)
        draw_text(c, "NEW PERSONAL BEST" if self.new_best else "KEEP FLYING!",
                  self.assets.font(9, bold=True),
                  (218, 112, 49) if self.new_best else (110, 127, 134),
                  center=(226, card.y + 207), alpha=alpha)

        draw_text(c, "SPACE to retry", self.assets.font(10, bold=True),
                  WHITE, center=(180, 575), shadow=True, alpha=225)

    def draw_debug(self) -> None:
        c = self.canvas
        # Panels sit just above the ground so the score and top HUD stay clear.
        py = GROUND_Y - 150
        draw_panel(c, (6, py, 200, 150), (8, 22, 30), radius=8, shadow=False, border=(92, 176, 196), alpha=200)
        lines = [
            "MATHS MODE  [F1]",
            f"state   {self.STATE_NAMES[self.state]}",
            f"fps     {self.fps_smooth:5.1f}",
            f"y       {self.bird.y:6.1f}",
            f"v_y     {self.bird.vy:6.1f}",
            f"g       {self.current_gravity():6.1f}",
            f"pipe v  {self.pipe_speed():6.1f}",
            f"gap     {self.current_gap():6.1f}",
            f"score   {self.score}",
            "v' = v + g·Δt",
            "y' = y + v'·Δt",
        ]
        font = self.assets.font(9, mono=True)
        for index, line in enumerate(lines):
            draw_text(c, line, font, (210, 243, 247), topleft=(14, py + 5 + index * 12))

        # Live y-vs-time graph, which makes the parabolic motion visible.
        gx, gy, gw, gh = 212, py, 142, 150
        draw_panel(c, (gx, gy, gw, gh), (8, 22, 30), radius=8, shadow=False, border=(92, 176, 196), alpha=200)
        plot = pygame.Rect(gx + 8, gy + 18, gw - 16, gh - 28)
        pygame.draw.rect(c, (76, 132, 146), plot, 1)
        draw_text(c, "y vs t", self.assets.font(8, mono=True), (180, 226, 234), topleft=(gx + 8, gy + 5))
        if len(self.trail) > 2:
            n = len(self.trail)
            points = []
            for index, y in enumerate(self.trail):
                px = plot.x + 2 + (index / (n - 1)) * (plot.w - 4)
                py = plot.y + 2 + (y / GROUND_Y) * (plot.h - 4)
                points.append((px, py))
            pygame.draw.lines(c, (255, 198, 92), False, points, 2)
            pygame.draw.circle(c, (255, 98, 120), (int(points[-1][0]), int(points[-1][1])), 2)

    def draw_toast(self) -> None:
        if self.toast_timer <= 0:
            return
        alpha = int(255 * min(1.0, self.toast_timer / 0.4))
        draw_panel(
            self.canvas,
            (78, 566, 204, 28),
            (10, 26, 34),
            radius=14,
            shadow=False,
            border=(120, 190, 204),
            alpha=min(220, alpha),
        )
        draw_text(
            self.canvas,
            self.toast,
            self.assets.font(9, bold=True),
            WHITE,
            center=(180, 580),
            alpha=alpha,
        )
