import math
import random
import pygame
from app_paths import resolve_existing_path
from settings import (
    WIDTH,
    HEIGHT,
    SPLASH_DURATION,
    DEEP_SPACE,
    CYAN,
    SOFT_CYAN,
    ELECTRIC_BLUE,
    WHITE,
    GLOW_BLUE,
)


class SplashScreen:
    def __init__(self):
        self.start_time = pygame.time.get_ticks()
        self.stars = self.create_stars(120)

        # Fonts
        self.font_big = pygame.font.SysFont("arial", 72, bold=True)
        self.font_mid = pygame.font.SysFont("arial", 30, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.font_tiny = pygame.font.SysFont("arial", 16)
        self.credit_label_font = pygame.font.SysFont("arial", 22, bold=True)
        self.credit_name_font = pygame.font.SysFont("arial", 24, bold=True)

        # Animation values
        self.pulse = 0
        self.fade_alpha = 0
        self.dev_alpha = 0
        self.title_y_offset = 20
        self.bg_zoom = 1.0

        # Background image
        self.background = None
        self.load_background()

    def load_background(self):
        """
        Load splash background image.
        Put your generated image in your project folder and rename it to:
            assets/mazeverse_splash_bg.png

        If the image is missing, the code will fall back to the gradient background.
        """
        possible_paths = [
            "assets/mazeverse_splash_bg.png",
            "mazeverse_splash_bg.png",
            "assets/splash_bg.png",
            "splash_bg.png",
        ]

        for path in possible_paths:
            try:
                image = pygame.image.load(resolve_existing_path(path)).convert()
                self.background = image
                return
            except Exception:
                continue

        self.background = None

    def create_stars(self, count):
        stars = []
        for _ in range(count):
            stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.randint(1, 3),
                "speed": random.uniform(0.2, 1.2),
                "alpha": random.randint(80, 255),
            })
        return stars

    def update(self):
        self.pulse += 0.05

        # Smooth fade in
        if self.fade_alpha < 255:
            self.fade_alpha = min(255, self.fade_alpha + 4)

        # Delay developer credit fade in slightly
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > 1200 and self.dev_alpha < 255:
            self.dev_alpha = min(255, self.dev_alpha + 5)

        # Small cinematic zoom
        self.bg_zoom = min(1.06, self.bg_zoom + 0.00015)

        # Title settles into place
        if self.title_y_offset > 0:
            self.title_y_offset = max(0, self.title_y_offset - 0.4)

        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        done = elapsed >= SPLASH_DURATION
        return done

    def draw_gradient_background(self, screen):
        for y in range(HEIGHT):
            blend = y / HEIGHT
            r = int(DEEP_SPACE[0] * (1 - blend) + 10 * blend)
            g = int(DEEP_SPACE[1] * (1 - blend) + 15 * blend)
            b = int(DEEP_SPACE[2] * (1 - blend) + 45 * blend)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    def draw_background_image(self, screen):
        if not self.background:
            self.draw_gradient_background(screen)
            return

        img_w, img_h = self.background.get_size()
        screen_ratio = WIDTH / HEIGHT
        img_ratio = img_w / img_h

        # Scale WITHOUT distortion
        if img_ratio > screen_ratio:
            # Image is wider â†’ fit height
            scale = HEIGHT / img_h
        else:
            # Image is taller â†’ fit width
            scale = WIDTH / img_w

        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        bg_scaled = pygame.transform.smoothscale(self.background, (new_w, new_h))

        # Center crop
        x = (WIDTH - new_w) // 2
        y = (HEIGHT - new_h) // 2

        screen.blit(bg_scaled, (x, y))

        # Overlay for readability
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        screen.blit(overlay, (0, 0))

    def draw_stars(self, screen):
        for star in self.stars:
            star_surface = pygame.Surface((star["r"] * 4, star["r"] * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                star_surface,
                (180, 220, 255, star["alpha"]),
                (star["r"] * 2, star["r"] * 2),
                star["r"]
            )
            screen.blit(star_surface, (star["x"], star["y"]))

    def draw_glow_text(self, screen, text, font, color, center, glow_color, alpha=255):
        for offset in range(10, 0, -2):
            glow_surf = font.render(text, True, glow_color)
            glow_surf.set_alpha(max(10, alpha // 12))
            glow_rect = glow_surf.get_rect(center=center)

            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow_surf, glow_rect.move(dx, dy))

        main_surf = font.render(text, True, color)
        main_surf.set_alpha(alpha)
        main_rect = main_surf.get_rect(center=center)
        screen.blit(main_surf, main_rect)

    def draw_ai_icon(self, screen, center_x, center_y):
        pulse_radius = 42 + int(math.sin(self.pulse * 2) * 5)

        # Outer glow rings
        for radius in range(pulse_radius + 22, pulse_radius, -4):
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 180, 255, 16), (radius, radius), radius)
            screen.blit(glow, (center_x - radius, center_y - radius))

        # Rotating pulse illusion through oscillating rings
        pygame.draw.circle(screen, CYAN, (center_x, center_y), pulse_radius, 2)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y), pulse_radius + 12, 1)

        # Core
        pygame.draw.circle(screen, SOFT_CYAN, (center_x, center_y), 12)

        # Chip lines
        pygame.draw.line(screen, SOFT_CYAN, (center_x - 28, center_y), (center_x - 12, center_y), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x + 12, center_y), (center_x + 28, center_y), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x, center_y - 28), (center_x, center_y - 12), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x, center_y + 12), (center_x, center_y + 28), 2)

        # End nodes
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x - 28, center_y), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x + 28, center_y), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y - 28), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y + 28), 3)

    def draw_loading_bar(self, screen):
        elapsed = pygame.time.get_ticks() - self.start_time
        delay = 600
        if elapsed < delay:
            progress = 0.0
        else:
            t = min((elapsed - delay) / (SPLASH_DURATION - delay), 1.0)
            progress = 1 - (1 - t) ** 3

        bar_width = 380
        bar_height = 18
        x = (WIDTH - bar_width) // 2
        # Keep loading section clearly above creator credits.
        y = HEIGHT - 160

        # Outer glow
        for i in range(10, 0, -2):
            glow = pygame.Surface((bar_width + i * 2, bar_height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 180, 255, 18), glow.get_rect(), border_radius=12)
            screen.blit(glow, (x - i, y - i))

        # Border
        pygame.draw.rect(screen, (80, 170, 255), (x, y, bar_width, bar_height), 2, border_radius=10)

        # Fill
        fill_width = int((bar_width - 6) * progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(x + 3, y + 3, fill_width, bar_height - 6)
            pygame.draw.rect(screen, CYAN, fill_rect, border_radius=8)

            # moving shine
            shine_x = x + 3 + max(0, fill_width - 40)
            shine = pygame.Surface((30, bar_height - 6), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 55))
            screen.blit(shine, (shine_x, y + 3))

        loading_text = self.font_mid.render("LOADING...", True, WHITE)
        loading_rect = loading_text.get_rect(center=(WIDTH // 2, y - 34))
        screen.blit(loading_text, loading_rect)

    def draw_credit_badge(self, screen, text, center_x, center_y, glow_rgb):
        badge_w = 280
        badge_h = 58
        rect = pygame.Rect(0, 0, badge_w, badge_h)
        rect.center = (center_x, center_y)

        for i in range(18, 0, -4):
            glow = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*glow_rgb, 22), glow.get_rect(), border_radius=20)
            screen.blit(glow, (rect.x - i, rect.y - i))

        body = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(body, (12, 18, 38, 230), body.get_rect(), border_radius=18)
        screen.blit(body, rect.topleft)

        pygame.draw.rect(screen, glow_rgb, rect, 3, border_radius=18)
        pygame.draw.rect(screen, (255, 255, 255), rect.inflate(-10, -10), 1, border_radius=12)

        gloss = pygame.Surface((rect.width - 12, rect.height // 2), pygame.SRCALPHA)
        pygame.draw.rect(gloss, (255, 255, 255, 20), gloss.get_rect(), border_radius=12)
        screen.blit(gloss, (rect.x + 6, rect.y + 4))

        text_surf = self.credit_name_font.render(text, True, (245, 248, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw_developer_credit(self, screen):
        # Anchor credits near bottom without overlapping loading section.
        label_y = HEIGHT - 102

        pygame.draw.line(
            screen,
            (80, 180, 255, 60),
            (WIDTH // 2 - 180, label_y - 30),
            (WIDTH // 2 + 180, label_y - 30),
            1
        )

        label_text = self.credit_label_font.render("Created by", True, (215, 240, 255))
        label_rect = label_text.get_rect(center=(WIDTH // 2, label_y))

        label_box = pygame.Rect(0, 0, 220, 46)
        label_box.center = label_rect.center

        for i in range(12, 0, -3):
            glow = pygame.Surface((label_box.width + i * 2, label_box.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 210, 255, 18), glow.get_rect(), border_radius=14)
            screen.blit(glow, (label_box.x - i, label_box.y - i))

        box_fill = pygame.Surface((label_box.width, label_box.height), pygame.SRCALPHA)
        pygame.draw.rect(box_fill, (8, 22, 48, 180), box_fill.get_rect(), border_radius=14)
        screen.blit(box_fill, label_box.topleft)

        pygame.draw.rect(screen, (90, 200, 255), label_box, 2, border_radius=14)
        pygame.draw.line(screen, (120, 230, 255), (label_box.x - 34, label_box.centery), (label_box.x - 8, label_box.centery), 2)
        pygame.draw.line(screen, (120, 230, 255), (label_box.right + 8, label_box.centery), (label_box.right + 34, label_box.centery), 2)
        screen.blit(label_text, label_rect)

        badge_y = HEIGHT - 36
        self.draw_credit_badge(screen, "CJ (Munotida)", WIDTH // 2 - 190, badge_y, (255, 170, 40))
        self.draw_credit_badge(screen, "Paradise (Rutendo)", WIDTH // 2 + 190, badge_y, (160, 80, 255))

    def draw_top_right_brand(self, screen):
        small_brand = self.font_tiny.render("Powered by Adaptive Intelligence", True, (150, 180, 255))
        small_brand.set_alpha(min(220, self.fade_alpha))
        screen.blit(small_brand, (WIDTH - small_brand.get_width() - 28, 24))

    def draw(self, screen):
        # Background
        self.draw_background_image(screen)

        # Floating stars on top of image
        self.draw_stars(screen)

        # Center cinematic glow
        center_glow = pygame.Surface((560, 560), pygame.SRCALPHA)
        pygame.draw.circle(center_glow, (0, 120, 255, 32), (280, 280), 200)
        pygame.draw.circle(center_glow, (0, 200, 255, 16), (280, 280), 130)
        screen.blit(center_glow, (WIDTH // 2 - 280, HEIGHT // 2 - 300))

        # Small top-right accent
        self.draw_top_right_brand(screen)

        # AI icon
        self.draw_ai_icon(screen, WIDTH // 2, HEIGHT // 2 - 135)

        # Main title
        self.draw_glow_text(
            screen,
            "MAZEVERSE",
            self.font_big,
            SOFT_CYAN,
            (WIDTH // 2, HEIGHT // 2 + self.title_y_offset - 18),
            ELECTRIC_BLUE,
            alpha=self.fade_alpha
        )

        self.draw_glow_text(
            screen,
            "AI",
            self.font_mid,
            WHITE,
            (WIDTH // 2, HEIGHT // 2 + self.title_y_offset + 42),
            GLOW_BLUE,
            alpha=self.fade_alpha
        )

        subtitle = self.font_small.render("Intelligent Maze Navigation Experience", True, (190, 215, 255))
        subtitle.set_alpha(min(255, self.fade_alpha))
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + self.title_y_offset + 88))
        screen.blit(subtitle, subtitle_rect)

        # Loading first, then credits below it.
        self.draw_loading_bar(screen)
        self.draw_developer_credit(screen)
