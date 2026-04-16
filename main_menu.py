import math
import random
import pygame
from app_paths import resolve_existing_path
from settings import WIDTH, HEIGHT, DEEP_SPACE, CYAN, SOFT_CYAN, ELECTRIC_BLUE, WHITE, GLOW_BLUE


class MenuButton:
    def __init__(self, text, x, y, width, height, action, icon=""):
        self.text = text
        self.icon = icon
        self.base_rect = pygame.Rect(x, y, width, height)
        self.rect = self.base_rect.copy()
        self.action = action
        self.hovered = False
        self.base_color = (14, 24, 50)
        self.border_color = (70, 150, 255)
        self.hover_color = (0, 255, 255)
        self.text_color = WHITE
        self.scale = 1.0
        self.target_scale = 1.0

    def update(self, mouse_pos):
        self.hovered = self.base_rect.collidepoint(mouse_pos)
        self.target_scale = 1.03 if self.hovered else 1.0
        self.scale += (self.target_scale - self.scale) * 0.18
        if self.hovered:
            self.scale += 0.01 * math.sin(pygame.time.get_ticks() * 0.01)

        new_w = int(self.base_rect.width * self.scale)
        new_h = int(self.base_rect.height * self.scale)
        self.rect = pygame.Rect(0, 0, new_w, new_h)
        self.rect.center = self.base_rect.center

    def draw(self, screen, font, selected=False):
        active = self.hovered or selected
        pulse = (math.sin(pygame.time.get_ticks() * 0.006) + 1) / 2

        outer_glow = (0, 210, 255, int(16 + pulse * 16) if active else 8)
        border_main = (0, 245, 255) if active else (70, 170, 255)
        border_inner = (130, 220, 255) if active else (110, 180, 255)

        # Stronger outer glow
        for i in range(20, 0, -4):
            glow_surf = pygame.Surface((self.rect.width + i * 2, self.rect.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                outer_glow,
                glow_surf.get_rect(),
                border_radius=20
            )
            screen.blit(glow_surf, (self.rect.x - i, self.rect.y - i))

        # Main body
        fill = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            fill,
            (8, 20, 52, 230) if active else (10, 18, 44, 210),
            fill.get_rect(),
            border_radius=16
        )
        screen.blit(fill, self.rect.topleft)

        # Outer border
        pygame.draw.rect(screen, border_main, self.rect, 2, border_radius=16)

        # Inner border
        inner_rect = self.rect.inflate(-8, -8)
        pygame.draw.rect(screen, border_inner, inner_rect, 1, border_radius=12)

        # Top gloss
        gloss = pygame.Surface((self.rect.width - 12, self.rect.height // 2), pygame.SRCALPHA)
        pygame.draw.rect(
            gloss,
            (255, 255, 255, 26 if active else 14),
            gloss.get_rect(),
            border_radius=12
        )
        screen.blit(gloss, (self.rect.x + 6, self.rect.y + 4))

        # Center light streak
        mid_y = self.rect.centery
        pygame.draw.line(screen, (0, 220, 255), (self.rect.x + 18, mid_y), (self.rect.right - 18, mid_y), 2)

        # Small bright energy points
        pygame.draw.circle(screen, (120, 240, 255), (self.rect.x + 22, mid_y), 3)
        pygame.draw.circle(screen, (120, 240, 255), (self.rect.right - 22, mid_y), 3)

        # Optional hover sweep
        if active:
            sweep_x = (pygame.time.get_ticks() // 4) % (self.rect.width + 80) - 40
            sweep = pygame.Surface((50, self.rect.height - 8), pygame.SRCALPHA)
            pygame.draw.rect(sweep, (255, 255, 255, 26), sweep.get_rect(), border_radius=10)
            screen.blit(sweep, (self.rect.x + sweep_x, self.rect.y + 4))

        label = f"{self.icon}  {self.text}" if self.icon else self.text
        text_surf = font.render(label, True, (225, 245, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

        # energy connection beam to center
        beam = pygame.Surface((self.rect.width, 2), pygame.SRCALPHA)
        pygame.draw.line(beam, (0, 200, 255, 40), (0, 1), (self.rect.width, 1), 2)
        screen.blit(beam, (self.rect.x, self.rect.centery))


class MainMenu:
    def __init__(self):
        self.title_font_big = pygame.font.SysFont("arial", 64, bold=True)
        self.title_font_small = pygame.font.SysFont("arial", 26, bold=True)
        self.button_font = pygame.font.SysFont("arial", 24, bold=True)
        self.info_font = pygame.font.SysFont("arial", 17)
        self.brand_font = pygame.font.SysFont("arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("arial", 15)
        self.credit_label_font = pygame.font.SysFont("arial", 18, bold=True)
        self.credit_name_font = pygame.font.SysFont("arial", 20, bold=True)

        self.stars = self.create_stars(55)
        self.pulse = 0
        self.selected_index = 0
        self.scan_offset = 0
        self.title_float = 0
        self.light_sweep_x = -400
        self.bg_parallax_offset = 0
        self.menu_breath = 0
        self.particles = self.create_particles(28)
        self.ai_difficulties = ["Easy", "Medium", "Hard", "Insane"]

        button_width = 396
        button_height = 52
        start_x = (WIDTH - button_width) // 2
        start_y = 332
        gap = 12

        self.buttons = [
            MenuButton("START SOLO", start_x, start_y, button_width, button_height, "start_solo"),
            MenuButton("PLAY VS AI", start_x, start_y + (button_height + gap), button_width, button_height, "start_vs_ai"),
            MenuButton("AI DIFFICULTY", start_x, start_y + 2 * (button_height + gap), button_width, button_height, "cycle_ai_difficulty"),
            MenuButton("SELECT LEVEL", start_x, start_y + 3 * (button_height + gap), button_width, button_height, "level_select"),
            MenuButton("SETTINGS", start_x, start_y + 4 * (button_height + gap), button_width, button_height, "settings"),
            MenuButton("EXIT", start_x, start_y + 5 * (button_height + gap), button_width, button_height, "exit"),
        ]

        self.background = None
        self.bg_zoom = 1.0
        self.load_background()

        self.click_sound = None
        self.runtime_settings = {}

    def set_click_sound(self, sound):
        self.click_sound = sound

    def load_background(self):
        """
        Load main menu background image.

        Save your image as one of these:
        assets/menu_bg.png
        menu_bg.png
        assets/mazeverse_menu_bg.png
        mazeverse_menu_bg.png
        """
        possible_paths = [
            "assets/menu_bg.png",
            "menu_bg.png",
            "assets/mazeverse_menu_bg.png",
            "mazeverse_menu_bg.png",
        ]

        for path in possible_paths:
            try:
                self.background = pygame.image.load(resolve_existing_path(path)).convert()
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
                "speed": random.uniform(0.15, 0.8),
                "alpha": random.randint(80, 255),
                "drift": random.uniform(-0.15, 0.15),
            })
        return stars

    def create_particles(self, count):
        particles = []
        for _ in range(count):
            particles.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.randint(2, 4),
                "speed_y": random.uniform(0.15, 0.5),
                "speed_x": random.uniform(-0.2, 0.2),
                "alpha": random.randint(40, 120),
            })
        return particles

    def update(self):
        self.pulse += 0.04
        self.scan_offset = (self.scan_offset + 2) % (HEIGHT + 120)
        self.title_float = math.sin(self.pulse * 1.5) * 4
        self.bg_zoom = min(1.05, self.bg_zoom + 0.00008)
        self.light_sweep_x += 6
        if self.light_sweep_x > WIDTH + 300:
            self.light_sweep_x = -400

        self.bg_parallax_offset = math.sin(self.pulse * 0.35) * 8
        self.menu_breath = math.sin(self.pulse * 1.2) * 3

        for star in self.stars:
            star["y"] += star["speed"]
            star["x"] += star["drift"]

            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

            if star["x"] < 0:
                star["x"] = WIDTH
            elif star["x"] > WIDTH:
                star["x"] = 0

        mouse_pos = pygame.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            button.update(mouse_pos)
            if button.hovered:
                self.selected_index = i

        button_width = 396
        button_height = 52
        start_x = (WIDTH - button_width) // 2
        start_y = 332 + int(self.menu_breath)
        gap = 12

        for i, button in enumerate(self.buttons):
            button.base_rect = pygame.Rect(
                start_x,
                start_y + i * (button_height + gap),
                button_width,
                button_height
            )

        for p in self.particles:
            p["y"] -= p["speed_y"]
            p["x"] += p["speed_x"]

            if p["y"] < -10:
                p["y"] = HEIGHT + 10
                p["x"] = random.randint(0, WIDTH)

            if p["x"] < -10:
                p["x"] = WIDTH + 10
            elif p["x"] > WIDTH + 10:
                p["x"] = -10

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    self.play_click_sound()
                    if button.action == "cycle_ai_difficulty":
                        self.cycle_ai_difficulty()
                    return button.action

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                selected_button = self.buttons[self.selected_index]
                if selected_button.action == "cycle_ai_difficulty":
                    self.play_click_sound()
                    self.cycle_ai_difficulty(reverse=(event.key == pygame.K_LEFT))
                    return "cycle_ai_difficulty"
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.play_click_sound()
                if self.buttons[self.selected_index].action == "cycle_ai_difficulty":
                    self.cycle_ai_difficulty()
                return self.buttons[self.selected_index].action

        return None

    def cycle_ai_difficulty(self, reverse=False):
        current = self.runtime_settings.get("ai_difficulty", "Medium")
        try:
            index = self.ai_difficulties.index(current)
        except ValueError:
            index = 1

        step = -1 if reverse else 1
        self.runtime_settings["ai_difficulty"] = self.ai_difficulties[(index + step) % len(self.ai_difficulties)]

    def play_click_sound(self):
        from settings import SOUND_ENABLED  # fallback (optional)

        if self.click_sound:
            runtime_sfx = self.runtime_settings.get("sfx") if self.runtime_settings else None
            if runtime_sfx is None:
                runtime_sfx = SOUND_ENABLED

            if runtime_sfx and self.click_sound.get_volume() > 0:
                self.click_sound.play()

    def draw_gradient_background(self, screen):
        for y in range(HEIGHT):
            blend = y / HEIGHT
            r = int(DEEP_SPACE[0] * (1 - blend) + 8 * blend)
            g = int(DEEP_SPACE[1] * (1 - blend) + 16 * blend)
            b = int(DEEP_SPACE[2] * (1 - blend) + 52 * blend)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    def draw_background_image(self, screen):
        if not self.background:
            self.draw_gradient_background(screen)
            return

        img_w, img_h = self.background.get_size()
        screen_ratio = WIDTH / HEIGHT
        img_ratio = img_w / img_h

        # Scale without distortion
        if img_ratio > screen_ratio:
            scale = HEIGHT / img_h
        else:
            scale = WIDTH / img_w

        scale *= self.bg_zoom

        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        bg_scaled = pygame.transform.smoothscale(self.background, (new_w, new_h))

        x = (WIDTH - new_w) // 2
        y = (HEIGHT - new_h) // 2
        screen.blit(bg_scaled, (x + int(self.bg_parallax_offset), y))

        # Dark overlay so UI stays readable
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 115))
        screen.blit(overlay, (0, 0))

    def draw_stars(self, screen):
        for star in self.stars:
            surf = pygame.Surface((star["r"] * 4, star["r"] * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                surf,
                (180, 220, 255, star["alpha"]),
                (star["r"] * 2, star["r"] * 2),
                star["r"]
            )
            screen.blit(surf, (star["x"], star["y"]))

    def draw_particles(self, screen):
        for p in self.particles:
            glow = pygame.Surface((p["r"] * 8, p["r"] * 8), pygame.SRCALPHA)

            pygame.draw.circle(
                glow,
                (0, 220, 255, p["alpha"]),
                (p["r"] * 4, p["r"] * 4),
                p["r"] + 2
            )

            pygame.draw.circle(
                glow,
                (180, 240, 255, p["alpha"]),
                (p["r"] * 4, p["r"] * 4),
                p["r"]
            )

            screen.blit(glow, (p["x"], p["y"]))

    def draw_light_sweep(self, screen):
        beam = pygame.Surface((260, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(
            beam,
            (120, 220, 255, 24),
            [(70, 0), (190, 0), (260, HEIGHT), (0, HEIGHT)]
        )
        screen.blit(beam, (self.light_sweep_x, 0))

    def draw_grid(self, screen):
        grid_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        horizon_y = HEIGHT - 220
        spacing = 40

        for x in range(0, WIDTH + spacing, spacing):
            pygame.draw.line(
                grid_surface,
                (40, 90, 160, 42),
                (x, horizon_y),
                (WIDTH // 2 + (x - WIDTH // 2) * 2, HEIGHT),
                1
            )

        for y in range(horizon_y, HEIGHT, 28):
            pygame.draw.line(grid_surface, (40, 90, 160, 30), (0, y), (WIDTH, y), 1)

        screen.blit(grid_surface, (0, 0))

    def draw_scanline(self, screen):
        scan = pygame.Surface((WIDTH, 36), pygame.SRCALPHA)
        pygame.draw.rect(scan, (0, 190, 255, 10), scan.get_rect(), border_radius=12)
        screen.blit(scan, (0, self.scan_offset - 36))

    def draw_glow_text(self, screen, text, font, color, center, glow_color):
        for offset in range(10, 0, -2):
            glow_surf = font.render(text, True, glow_color)
            glow_surf.set_alpha(22)
            glow_rect = glow_surf.get_rect(center=center)
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow_surf, glow_rect.move(dx, dy))

        main_surf = font.render(text, True, color)
        main_rect = main_surf.get_rect(center=center)
        screen.blit(main_surf, main_rect)

    def draw_ai_icon(self, screen, center_x, center_y):
        pulse_radius = 34 + int(math.sin(self.pulse * 2.2) * 3)

        for radius in range(pulse_radius + 16, pulse_radius, -4):
            glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 180, 255, 16), (radius, radius), radius)
            screen.blit(glow, (center_x - radius, center_y - radius))

        pygame.draw.circle(screen, CYAN, (center_x, center_y), pulse_radius, 2)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y), pulse_radius + 10, 1)
        pygame.draw.circle(screen, SOFT_CYAN, (center_x, center_y), 10)

        pygame.draw.line(screen, SOFT_CYAN, (center_x - 22, center_y), (center_x - 10, center_y), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x + 10, center_y), (center_x + 22, center_y), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x, center_y - 22), (center_x, center_y - 10), 2)
        pygame.draw.line(screen, SOFT_CYAN, (center_x, center_y + 10), (center_x, center_y + 22), 2)

        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x - 22, center_y), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x + 22, center_y), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y - 22), 3)
        pygame.draw.circle(screen, ELECTRIC_BLUE, (center_x, center_y + 22), 3)

    def draw_title_panel(self, screen):
        panel_width = 620
        panel_height = 132
        panel_x = (WIDTH - panel_width) // 2
        panel_y = 38 + int(self.title_float)

        for i in range(20, 0, -4):
            glow_surf = pygame.Surface((panel_width + i * 2, panel_height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 130, 255, 12), glow_surf.get_rect(), border_radius=24)
            screen.blit(glow_surf, (panel_x - i, panel_y - i))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((10, 20, 46, 150))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (80, 160, 255), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=22)

        pulse = int(36 + 18 * math.sin(self.pulse * 2))
        pygame.draw.circle(screen, (0, 200, 255, 20), (WIDTH // 2, panel_y + 72), pulse)

        inner_rect = pygame.Rect(panel_x + 10, panel_y + 10, panel_width - 20, panel_height - 20)
        pygame.draw.rect(screen, (100, 180, 255), inner_rect, 1, border_radius=18)

        self.draw_ai_icon(screen, WIDTH // 2, panel_y + 26)

        self.draw_glow_text(
            screen,
            "MAZEVERSE",
            self.title_font_big,
            SOFT_CYAN,
            (WIDTH // 2, panel_y + 76),
            ELECTRIC_BLUE
        )

        self.draw_glow_text(
            screen,
            "AI",
            self.title_font_small,
            WHITE,
            (WIDTH // 2, panel_y + 106),
            GLOW_BLUE
        )

    def draw_menu_panel(self, screen):
        panel_w = 492
        panel_h = 426
        panel_x = (WIDTH - panel_w) // 2
        panel_y = 286

        for i in range(26, 0, -4):
            glow = pygame.Surface((panel_w + i * 2, panel_h + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 180, 255, 10), glow.get_rect(), border_radius=28)
            screen.blit(glow, (panel_x - i, panel_y - i))

        body = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(body, (7, 16, 38, 156), body.get_rect(), border_radius=26)
        pygame.draw.rect(body, (120, 215, 255, 28), (18, 18, panel_w - 36, 70), border_radius=18)
        screen.blit(body, (panel_x, panel_y))

        pygame.draw.rect(screen, (85, 170, 255), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=26)
        pygame.draw.rect(screen, (175, 230, 255), (panel_x + 10, panel_y + 10, panel_w - 20, panel_h - 20), 1, border_radius=20)

        section_text = self.small_font.render("Choose your mission profile", True, (220, 242, 255))
        screen.blit(section_text, section_text.get_rect(center=(WIDTH // 2, panel_y + 37)))

        sub_text = self.info_font.render("Solo for a calm run, VS AI for a live race.", True, (175, 208, 240))
        screen.blit(sub_text, sub_text.get_rect(center=(WIDTH // 2, panel_y + 62)))

    def draw_center_glow(self, screen):
        center_glow = pygame.Surface((650, 650), pygame.SRCALPHA)
        pygame.draw.circle(center_glow, (0, 105, 255, 10), (325, 180), 130)
        pygame.draw.circle(center_glow, (0, 200, 255, 5), (325, 180), 80)
        screen.blit(center_glow, (WIDTH // 2 - 325, -20))

    def draw_credit_badge(self, screen, text, center_x, center_y, glow_rgb):
        badge_w = 244
        badge_h = 50
        rect = pygame.Rect(0, 0, badge_w, badge_h)
        rect.center = (center_x, center_y)

        # Outer glow
        for i in range(18, 0, -4):
            glow = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*glow_rgb, 22), glow.get_rect(), border_radius=20)
            screen.blit(glow, (rect.x - i, rect.y - i))

        # Body
        body = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(body, (12, 18, 38, 230), body.get_rect(), border_radius=18)
        screen.blit(body, rect.topleft)

        # Borders
        pygame.draw.rect(screen, glow_rgb, rect, 3, border_radius=18)
        pygame.draw.rect(screen, (255, 255, 255), rect.inflate(-10, -10), 1, border_radius=12)

        # Top gloss
        gloss = pygame.Surface((rect.width - 12, rect.height // 2), pygame.SRCALPHA)
        pygame.draw.rect(gloss, (255, 255, 255, 20), gloss.get_rect(), border_radius=12)
        screen.blit(gloss, (rect.x + 6, rect.y + 4))

        # Text
        text_surf = self.credit_name_font.render(text, True, (245, 248, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw_footer(self, screen):
        label_y = HEIGHT - 92

        pygame.draw.line(
            screen,
            (80, 180, 255, 60),
            (WIDTH // 2 - 140, label_y - 24),
            (WIDTH // 2 + 140, label_y - 24),
            1
        )

        label_text = self.credit_label_font.render("Created by", True, (215, 240, 255))
        label_rect = label_text.get_rect(center=(WIDTH // 2, label_y))

        label_box = pygame.Rect(0, 0, 190, 38)
        label_box.center = label_rect.center

        for i in range(12, 0, -3):
            glow = pygame.Surface((label_box.width + i * 2, label_box.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 210, 255, 18), glow.get_rect(), border_radius=14)
            screen.blit(glow, (label_box.x - i, label_box.y - i))

        box_fill = pygame.Surface((label_box.width, label_box.height), pygame.SRCALPHA)
        pygame.draw.rect(box_fill, (8, 22, 48, 180), box_fill.get_rect(), border_radius=14)
        screen.blit(box_fill, label_box.topleft)

        pygame.draw.rect(screen, (90, 200, 255), label_box, 2, border_radius=14)

        pygame.draw.line(screen, (120, 230, 255), (label_box.x - 28, label_box.centery), (label_box.x - 8, label_box.centery), 2)
        pygame.draw.line(screen, (120, 230, 255), (label_box.right + 8, label_box.centery), (label_box.right + 28, label_box.centery), 2)

        screen.blit(label_text, label_rect)

        badge_y = HEIGHT - 42
        self.draw_credit_badge(screen, "CJ (Munotida)", WIDTH // 2 - 164, badge_y, (255, 170, 40))
        self.draw_credit_badge(screen, "Paradise (Rutendo)", WIDTH // 2 + 164, badge_y, (160, 80, 255))

        nav_text = self.small_font.render("Use mouse or Up / Down / Enter to navigate", True, (170, 205, 255))
        nav_rect = nav_text.get_rect(center=(WIDTH // 2, HEIGHT - 12))
        screen.blit(nav_text, nav_rect)

    def draw(self, screen):
        self.draw_background_image(screen)
        self.draw_light_sweep(screen)
        self.draw_stars(screen)
        self.draw_particles(screen)
        self.draw_grid(screen)
        self.draw_scanline(screen)
        self.draw_center_glow(screen)
        self.draw_title_panel(screen)
        self.draw_menu_panel(screen)

        ai_label = self.runtime_settings.get("ai_difficulty", "Medium")
        self.buttons[2].text = f"AI DIFFICULTY: {ai_label.upper()}"

        for i, button in enumerate(self.buttons):
            button.draw(screen, self.button_font, selected=(i == self.selected_index))

        mode_text = "Tip: change AI difficulty before starting VS AI mode."
        mode_surf = self.small_font.render(mode_text, True, (205, 228, 255))
        mode_rect = mode_surf.get_rect(center=(WIDTH // 2, 708))
        screen.blit(mode_surf, mode_rect)

        self.draw_footer(screen)
