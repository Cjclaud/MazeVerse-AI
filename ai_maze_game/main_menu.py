import math
import random
import pygame
from settings import WIDTH, HEIGHT, DEEP_SPACE, CYAN, SOFT_CYAN, ELECTRIC_BLUE, WHITE, GLOW_BLUE, SOUND_ENABLED


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

        new_w = int(self.base_rect.width * self.scale)
        new_h = int(self.base_rect.height * self.scale)
        self.rect = pygame.Rect(0, 0, new_w, new_h)
        self.rect.center = self.base_rect.center

    def draw(self, screen, font, selected=False):
        active = self.hovered or selected

        glow_alpha = 20 if active else 8
        glow_color = (0, 210, 255, glow_alpha)

        for i in range(14, 0, -3):
            glow_surf = pygame.Surface((self.rect.width + i * 2, self.rect.height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf,
                glow_color,
                glow_surf.get_rect(),
                border_radius=18
            )
            screen.blit(glow_surf, (self.rect.x - i, self.rect.y - i))

        fill_color = (24, 42, 78) if active else self.base_color
        pygame.draw.rect(screen, fill_color, self.rect, border_radius=14)

        border = self.hover_color if active else self.border_color
        pygame.draw.rect(screen, border, self.rect, 2, border_radius=14)

        inner_rect = self.rect.inflate(-10, -10)
        pygame.draw.rect(screen, (120, 190, 255), inner_rect, 1, border_radius=10)

        # top highlight
        highlight = pygame.Surface((self.rect.width - 8, max(8, self.rect.height // 3)), pygame.SRCALPHA)
        pygame.draw.rect(highlight, (255, 255, 255, 18 if active else 8), highlight.get_rect(), border_radius=12)
        screen.blit(highlight, (self.rect.x + 4, self.rect.y + 4))

        label = f"{self.icon}  {self.text}" if self.icon else self.text
        text_surf = font.render(label, True, SOFT_CYAN if active else self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class MainMenu:
    def __init__(self):
        self.title_font_big = pygame.font.SysFont("arial", 64, bold=True)
        self.title_font_small = pygame.font.SysFont("arial", 30, bold=True)
        self.button_font = pygame.font.SysFont("arial", 28, bold=True)
        self.info_font = pygame.font.SysFont("arial", 18)
        self.brand_font = pygame.font.SysFont("arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)

        self.stars = self.create_stars(135)
        self.pulse = 0
        self.selected_index = 0
        self.scan_offset = 0
        self.title_float = 0

        button_width = 330
        button_height = 66
        start_x = (WIDTH - button_width) // 2
        start_y = HEIGHT // 2 - 10
        gap = 24

        self.buttons = [
            MenuButton("START GAME", start_x, start_y, button_width, button_height, "start", icon="▶"),
            MenuButton("SELECT LEVEL", start_x, start_y + (button_height + gap), button_width, button_height, "level_select", icon="▦"),
            MenuButton("SETTINGS", start_x, start_y + 2 * (button_height + gap), button_width, button_height, "settings", icon="⚙"),
            MenuButton("EXIT", start_x, start_y + 3 * (button_height + gap), button_width, button_height, "exit", icon="⏻"),
        ]

        self.background = None
        self.bg_zoom = 1.0
        self.load_background()

        self.click_sound = None

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
                self.background = pygame.image.load(path).convert()
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

    def update(self):
        self.pulse += 0.04
        self.scan_offset = (self.scan_offset + 2) % (HEIGHT + 120)
        self.title_float = math.sin(self.pulse * 1.5) * 4
        self.bg_zoom = min(1.05, self.bg_zoom + 0.00008)

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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    self.play_click_sound()
                    return button.action

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.play_click_sound()
                return self.buttons[self.selected_index].action

        return None

    def play_click_sound(self):
        if SOUND_ENABLED and self.click_sound:
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
        screen.blit(bg_scaled, (x, y))

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
        scan = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
        pygame.draw.rect(scan, (0, 190, 255, 18), scan.get_rect())
        screen.blit(scan, (0, self.scan_offset - 80))

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
        panel_height = 180
        panel_x = (WIDTH - panel_width) // 2
        panel_y = 82 + int(self.title_float)

        for i in range(20, 0, -4):
            glow_surf = pygame.Surface((panel_width + i * 2, panel_height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 130, 255, 12), glow_surf.get_rect(), border_radius=24)
            screen.blit(glow_surf, (panel_x - i, panel_y - i))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((10, 20, 46, 150))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (80, 160, 255), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=22)

        inner_rect = pygame.Rect(panel_x + 10, panel_y + 10, panel_width - 20, panel_height - 20)
        pygame.draw.rect(screen, (100, 180, 255), inner_rect, 1, border_radius=18)

        self.draw_ai_icon(screen, WIDTH // 2, panel_y + 40)

        self.draw_glow_text(
            screen,
            "MAZEVERSE",
            self.title_font_big,
            SOFT_CYAN,
            (WIDTH // 2, panel_y + 105),
            ELECTRIC_BLUE
        )

        self.draw_glow_text(
            screen,
            "AI",
            self.title_font_small,
            WHITE,
            (WIDTH // 2, panel_y + 148),
            GLOW_BLUE
        )

    def draw_center_glow(self, screen):
        center_glow = pygame.Surface((760, 760), pygame.SRCALPHA)
        pygame.draw.circle(center_glow, (0, 105, 255, 26), (380, 210), 185)
        pygame.draw.circle(center_glow, (0, 200, 255, 10), (380, 210), 110)
        screen.blit(center_glow, (WIDTH // 2 - 380, -70))

    def draw_footer(self, screen):
        nav_text = self.info_font.render("Use mouse or ↑ ↓ Enter to navigate", True, (170, 205, 255))
        nav_rect = nav_text.get_rect(center=(WIDTH // 2, HEIGHT - 28))
        screen.blit(nav_text, nav_rect)

        brand_text = self.small_font.render("👑 CJ (Muno) × Paradise (Rutendo) ✨", True, (160, 210, 255))
        brand_rect = brand_text.get_rect(center=(WIDTH // 2, HEIGHT - 54))
        screen.blit(brand_text, brand_rect)

    def draw(self, screen):
        self.draw_background_image(screen)
        self.draw_stars(screen)
        self.draw_grid(screen)
        self.draw_scanline(screen)
        self.draw_center_glow(screen)
        self.draw_title_panel(screen)

        for i, button in enumerate(self.buttons):
            button.draw(screen, self.button_font, selected=(i == self.selected_index))

        self.draw_footer(screen)