import random
import math
import pygame
from app_paths import resolve_existing_path
from settings import WIDTH, HEIGHT, DEEP_SPACE, CYAN, SOFT_CYAN, ELECTRIC_BLUE, WHITE, SETTINGS_BG_IMAGE, STAR_SCROLL_SPEED, NEBULA_PULSE_SPEED, BACKGROUND_DIM_ALPHA


class SettingsOption:
    def __init__(self, label, values, current_index=0):
        self.label = label
        self.values = values
        self.current_index = current_index

    @property
    def current_value(self):
        return self.values[self.current_index]

    def next_value(self):
        self.current_index = (self.current_index + 1) % len(self.values)

    def prev_value(self):
        self.current_index = (self.current_index - 1) % len(self.values)


class SettingsMenu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("arial", 54, bold=True)
        self.option_font = pygame.font.SysFont("arial", 28, bold=True)
        self.info_font = pygame.font.SysFont("arial", 18)
        self.small_font = pygame.font.SysFont("arial", 22, bold=True)

        self.stars = self.create_stars(120)
        self.selected_index = 0
        self.click_sound = None

        # Load background
        try:
            self.bg_image = pygame.image.load(resolve_existing_path(SETTINGS_BG_IMAGE)).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (WIDTH, HEIGHT))
        except Exception:
            self.bg_image = None

        self.bg_time = 0
        self.moving_stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(80)]

        self.options = [
            SettingsOption("Music", ["ON", "OFF"], 0),
            SettingsOption("Sound Effects", ["ON", "OFF"], 0),
            SettingsOption("Difficulty", ["EASY", "MEDIUM", "HARD"], 1),
            SettingsOption("Show Hints", ["ON", "OFF"], 0),
            SettingsOption("Fog of War", ["ON", "OFF"], 0),
            SettingsOption("Timer", ["ON", "OFF"], 0),
            SettingsOption("Back", ["RETURN"], 0),
        ]

        self.option_rects = []

    def set_click_sound(self, sound):
        """Set the click sound to be played on button presses"""
        self.click_sound = sound

    def create_stars(self, count):
        stars = []
        for _ in range(count):
            stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "r": random.randint(1, 3),
                "speed": random.uniform(0.15, 0.8),
                "alpha": random.randint(80, 255),
            })
        return stars

    def update(self):
        self.bg_time += 1

        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        self.moving_stars = [(x, (y + 0.3) % HEIGHT) for x, y in self.moving_stars]

        mouse_pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_index = i

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_LEFT:
                if self.options[self.selected_index].label != "Back":
                    self.options[self.selected_index].prev_value()

            elif event.key == pygame.K_RIGHT:
                if self.options[self.selected_index].label != "Back":
                    self.options[self.selected_index].next_value()

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                selected = self.options[self.selected_index]

                if selected.label == "Back":
                    self.play_click_sound()
                    return "back"
                else:
                    selected.next_value()

                    # Play only if SFX is still ON after the change
                    if self.options[1].current_value == "ON":
                        self.play_click_sound()

            elif event.key == pygame.K_ESCAPE:
                self.play_click_sound()
                return "back"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    selected = self.options[i]

                    if selected.label == "Back":
                        self.play_click_sound()
                        return "back"
                    else:
                        selected.next_value()

                        # Play only if SFX is still ON after the change
                        if self.options[1].current_value == "ON":
                            self.play_click_sound()

        return None

    def play_click_sound(self):
        """Play click sound only if SFX setting is ON"""
        sfx_enabled = self.options[1].current_value == "ON"
        if self.click_sound and sfx_enabled:
            self.click_sound.play()

    def get_settings(self):
        return {
            "music": self.options[0].current_value == "ON",
            "sfx": self.options[1].current_value == "ON",
            "difficulty": self.options[2].current_value,
            "show_hints": self.options[3].current_value == "ON",
            "fog": self.options[4].current_value == "ON",
            "timer": self.options[5].current_value == "ON",
        }

    def set_settings(self, current_settings):
        mapping = {
            "music": 0,
            "sfx": 1,
            "difficulty": 2,
            "show_hints": 3,
            "fog": 4,
            "timer": 5,
        }

        for key, index in mapping.items():
            if key not in current_settings:
                continue

            option = self.options[index]
            target = current_settings[key]

            if key == "difficulty":
                target_value = str(target).upper()
            else:
                target_value = "ON" if target else "OFF"

            if target_value in option.values:
                option.current_index = option.values.index(target_value)

    def draw_background(self, screen):
        if self.bg_image is None:
            for y in range(HEIGHT):
                blend = y / HEIGHT
                r = int(DEEP_SPACE[0] * (1 - blend) + 8 * blend)
                g = int(DEEP_SPACE[1] * (1 - blend) + 16 * blend)
                b = int(DEEP_SPACE[2] * (1 - blend) + 52 * blend)
                pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))
        else:
            # Subtle zoom/pulse effect
            scale = 1 + 0.01 * math.sin(self.bg_time * NEBULA_PULSE_SPEED)

            new_width = int(WIDTH * scale)
            new_height = int(HEIGHT * scale)

            bg_scaled = pygame.transform.smoothscale(self.bg_image, (new_width, new_height))

            # Center the zoom
            x = (WIDTH - new_width) // 2
            y = (HEIGHT - new_height) // 2

            screen.blit(bg_scaled, (x, y))

        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, BACKGROUND_DIM_ALPHA))
        screen.blit(overlay, (0, 0))

        # Moving stars
        for x_star, y_star in self.moving_stars:
            pygame.draw.circle(screen, (180, 220, 255), (int(x_star), int(y_star)), 1)


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

    def draw_title(self, screen):
        for offset in range(8, 0, -2):
            glow_surf = self.title_font.render("SETTINGS", True, ELECTRIC_BLUE)
            glow_surf.set_alpha(22)
            glow_rect = glow_surf.get_rect(center=(WIDTH // 2, 90))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow_surf, glow_rect.move(dx, dy))

        title_surf = self.title_font.render("SETTINGS", True, SOFT_CYAN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 90))
        screen.blit(title_surf, title_rect)

    def draw_panel(self, screen):
        panel_width = 760
        panel_height = 460
        panel_x = (WIDTH - panel_width) // 2
        panel_y = 150

        for i in range(18, 0, -4):
            glow_surf = pygame.Surface((panel_width + i * 2, panel_height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 120, 255, 12), glow_surf.get_rect(), border_radius=24)
            screen.blit(glow_surf, (panel_x - i, panel_y - i))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((12, 22, 46, 160))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (80, 160, 255), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=22)

        return panel_x, panel_y, panel_width, panel_height

    def draw_options(self, screen, panel_x, panel_y, panel_width):
        self.option_rects = []

        start_y = panel_y + 55
        row_height = 58
        row_x = panel_x + 55
        row_width = panel_width - 110

        for i, option in enumerate(self.options):
            y = start_y + i * row_height
            row_rect = pygame.Rect(row_x, y, row_width, 44)
            self.option_rects.append(row_rect)

            active = i == self.selected_index

            if active:
                for glow_size in range(10, 0, -2):
                    glow = pygame.Surface((row_rect.width + glow_size * 2, row_rect.height + glow_size * 2), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (0, 200, 255, 16), glow.get_rect(), border_radius=14)
                    screen.blit(glow, (row_rect.x - glow_size, row_rect.y - glow_size))

            fill_color = (24, 40, 72) if active else (18, 28, 55)
            border_color = CYAN if active else (70, 150, 255)

            pygame.draw.rect(screen, fill_color, row_rect, border_radius=12)
            pygame.draw.rect(screen, border_color, row_rect, 2, border_radius=12)

            label_color = SOFT_CYAN if active else WHITE
            value_color = CYAN if active else (180, 220, 255)

            label_surf = self.option_font.render(option.label, True, label_color)
            screen.blit(label_surf, (row_rect.x + 18, row_rect.y + 8))

            value_text = option.current_value
            value_surf = self.option_font.render(value_text, True, value_color)
            value_rect = value_surf.get_rect(midright=(row_rect.right - 18, row_rect.y + 22))
            screen.blit(value_surf, value_rect)

    def draw_footer(self, screen):
        info = self.info_font.render("Use mouse or ↑ ↓ ← → Enter | ESC = Back", True, (170, 205, 255))
        info_rect = info.get_rect(center=(WIDTH // 2, HEIGHT - 32))
        screen.blit(info, info_rect)

    def draw(self, screen):
        self.draw_background(screen)
        self.draw_title(screen)
        panel_x, panel_y, panel_width, _ = self.draw_panel(screen)
        self.draw_options(screen, panel_x, panel_y, panel_width)
        self.draw_footer(screen)
