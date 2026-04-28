import math
import pygame
from app_paths import resolve_existing_path

# Global settings from main context
WIDTH, HEIGHT = 1280, 820
CYAN = (0, 245, 255)
WHITE = (255, 255, 255)
TEXT_SUBCOLOR = (160, 200, 255)
TEXT_MUTED = (118, 150, 205)
PANEL_BORDER = (70, 130, 220)
PANEL_FILL = (8, 18, 42)
BUTTON_IDLE = (10, 22, 52)
BUTTON_HOVER = (18, 42, 84)
ACCENT_GOLD = (255, 212, 120)


def draw_vertical_gradient(surface, top_color, bottom_color):
    width, height = surface.get_size()
    if height <= 1:
        surface.fill(top_color)
        return

    for y in range(height):
        mix = y / (height - 1)
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * mix),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * mix),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * mix),
            int(top_color[3] + (bottom_color[3] - top_color[3]) * mix),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


class MenuButton:
    def __init__(self, text, x, y, w, h, action, icon=""):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.action = action
        self.icon = icon
        self.is_hovered = False
        self.is_selected = False
        self.hover_offset = 0
        self.glow_alpha = 0
        self.sheen_offset = 0

    def draw(self, screen, font):
        is_active = self.is_hovered or self.is_selected
        target_offset = 8 if is_active else 0
        self.hover_offset += (target_offset - self.hover_offset) * 0.2

        target_glow = 210 if is_active else 0
        self.glow_alpha += (target_glow - self.glow_alpha) * 0.15
        if self.is_hovered:
            self.sheen_offset = (self.sheen_offset + 12) % (self.rect.w + 120)
        else:
            self.sheen_offset = 0

        draw_rect = self.rect.copy()
        draw_rect.x += round(self.hover_offset)

        if self.glow_alpha > 5:
            glow_surf = pygame.Surface((draw_rect.w + 28, draw_rect.h + 28), pygame.SRCALPHA)
            for i in range(5):
                alpha = int((self.glow_alpha / (i + 1)) * 0.26)
                pygame.draw.rect(
                    glow_surf,
                    (0, 245, 255, alpha),
                    (14 - i * 2, 14 - i * 2, draw_rect.w + i * 4, draw_rect.h + i * 4),
                    border_radius=16 + i,
                )
            screen.blit(glow_surf, (draw_rect.x - 14, draw_rect.y - 14))

        bg_surf = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        if self.is_hovered:
            draw_vertical_gradient(bg_surf, (*BUTTON_HOVER, 228), (10, 26, 60, 228))
        elif self.is_selected:
            draw_vertical_gradient(bg_surf, (16, 34, 72, 212), (8, 20, 48, 212))
        else:
            draw_vertical_gradient(bg_surf, (*BUTTON_IDLE, 188), (7, 16, 40, 188))
        pygame.draw.rect(bg_surf, (255, 255, 255, 22), (0, 0, draw_rect.w, draw_rect.h // 2), border_radius=14)
        if self.is_hovered:
            sheen = pygame.Surface((80, draw_rect.h), pygame.SRCALPHA)
            draw_vertical_gradient(sheen, (255, 255, 255, 0), (255, 255, 255, 32))
            bg_surf.blit(sheen, (self.sheen_offset - 80, 0), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(bg_surf, (draw_rect.x, draw_rect.y))

        border_color = CYAN if self.is_hovered else ((120, 210, 255) if self.is_selected else PANEL_BORDER)
        pygame.draw.rect(screen, border_color, draw_rect, 2, border_radius=14)
        if is_active:
            pygame.draw.line(
                screen,
                ACCENT_GOLD,
                (draw_rect.x + 8, draw_rect.centery),
                (draw_rect.x + 26, draw_rect.centery),
                3,
            )
        pygame.draw.line(
            screen,
            (180, 235, 255) if is_active else (95, 140, 200),
            (draw_rect.x + 20, draw_rect.y + 10),
            (draw_rect.right - 20, draw_rect.y + 10),
            1,
        )

        label = f"{self.icon} {self.text}" if self.icon else self.text
        text_color = WHITE if is_active else (210, 230, 255)
        text_surf = font.render(label, True, text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)


class MainMenu:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.tag_font = pygame.font.SysFont("arial", 18, bold=True)
        self.title_font = pygame.font.SysFont("arial", 56, bold=True)
        self.subtitle_font = pygame.font.SysFont("arial", 18)

        button_width = 332
        button_height = 46
        gap = 14
        start_x = (WIDTH - button_width) // 2
        start_y = 336

        self.buttons = [
            MenuButton("START SOLO", start_x, start_y, button_width, button_height, "start_solo"),
            MenuButton("PLAY VS AI", start_x, start_y + (button_height + gap), button_width, button_height, "start_vs_ai"),
            MenuButton("MOBILE RACE", start_x, start_y + 2 * (button_height + gap), button_width, button_height, "mobile_race"),
            MenuButton("AI DIFFICULTY", start_x, start_y + 3 * (button_height + gap), button_width, button_height, "cycle_ai_difficulty"),
            MenuButton("SELECT LEVEL", start_x, start_y + 4 * (button_height + gap), button_width, button_height, "level_select"),
            MenuButton("SETTINGS", start_x, start_y + 5 * (button_height + gap), button_width, button_height, "settings"),
            MenuButton("EXIT", start_x, start_y + 6 * (button_height + gap), button_width, button_height, "exit"),
        ]

        stack_height = len(self.buttons) * button_height + (len(self.buttons) - 1) * gap
        self.menu_panel_rect = pygame.Rect(start_x - 36, start_y - 26, button_width + 72, stack_height + 52)
        self.title_panel_rect = pygame.Rect((WIDTH // 2) - 310, 84, 620, 172)

        self.runtime_settings = {}
        self.click_sound = None
        self.load_background()
        self.bg_zoom = 1.0
        self.grid_scroll = 0
        self.selected_index = 0

    def load_background(self):
        try:
            self.background = pygame.image.load(resolve_existing_path("assets/menu_bg.png")).convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except Exception:
            self.background = None

    def set_click_sound(self, sound):
        self.click_sound = sound

    def update(self):
        mx, my = pygame.mouse.get_pos()
        hovered_index = None
        for index, btn in enumerate(self.buttons):
            btn.is_hovered = btn.rect.collidepoint((mx, my))
            if btn.is_hovered:
                hovered_index = index

        if hovered_index is not None:
            self.selected_index = hovered_index

        for index, btn in enumerate(self.buttons):
            btn.is_selected = index == self.selected_index

        self.grid_scroll = (self.grid_scroll + 2) % 40
        self.bg_zoom = 1.0 + 0.02 * math.sin(pygame.time.get_ticks() * 0.001)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.click_sound:
                    self.click_sound.play()
                return self._trigger_action(self.buttons[self.selected_index].action)
            elif event.key == pygame.K_ESCAPE:
                if self.click_sound:
                    self.click_sound.play()
                return "exit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.is_hovered:
                    if self.click_sound:
                        self.click_sound.play()
                    return self._trigger_action(btn.action)
        return None

    def _trigger_action(self, action):
        if action == "cycle_ai_difficulty":
            diffs = ["Easy", "Medium", "Hard"]
            curr = self.runtime_settings.get("ai_difficulty", "Medium")
            curr_index = diffs.index(curr) if curr in diffs else 1
            self.runtime_settings["ai_difficulty"] = diffs[(curr_index + 1) % len(diffs)]
        return action

    def draw(self, screen):
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.0022)

        if self.background:
            scaled_bg = pygame.transform.scale(
                self.background,
                (int(WIDTH * self.bg_zoom), int(HEIGHT * self.bg_zoom)),
            )
            bg_rect = scaled_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_bg, bg_rect)
        else:
            screen.fill((4, 6, 18))

        dim_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_vertical_gradient(dim_overlay, (4, 10, 22, 82), (2, 6, 18, 138))
        screen.blit(dim_overlay, (0, 0))

        focus_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        focus_alpha = int(125 + 35 * pulse)
        pygame.draw.ellipse(focus_overlay, (12, 28, 58, focus_alpha), (WIDTH // 2 - 260, 235, 520, 560))
        pygame.draw.ellipse(focus_overlay, (0, 245, 255, 18), (WIDTH // 2 - 220, 270, 440, 420), 2)
        screen.blit(focus_overlay, (0, 0))

        grid_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        horizon_y = HEIGHT - 220
        for x in range(0, WIDTH + 40, 40):
            pygame.draw.line(grid_surf, (0, 245, 255, 40), (WIDTH // 2, horizon_y), (x, HEIGHT), 1)

        for y in range(horizon_y, HEIGHT + 40, 40):
            yy = y + (self.grid_scroll % 40)
            if yy <= HEIGHT:
                alpha = int(255 * ((yy - horizon_y) / (HEIGHT - horizon_y)))
                pygame.draw.line(grid_surf, (0, 245, 255, alpha // 4), (0, yy), (WIDTH, yy), 1)

        screen.blit(grid_surf, (0, 0))

        panel_surf = pygame.Surface((self.menu_panel_rect.w, self.menu_panel_rect.h), pygame.SRCALPHA)
        draw_vertical_gradient(panel_surf, (*PANEL_FILL, 175), (6, 14, 34, 228))
        pygame.draw.rect(panel_surf, (255, 255, 255, 16), (0, 0, self.menu_panel_rect.w, 34), border_radius=24)
        pygame.draw.rect(panel_surf, (120, 200, 255, 18), (18, 18, self.menu_panel_rect.w - 36, self.menu_panel_rect.h - 36), 1, border_radius=20)
        screen.blit(panel_surf, self.menu_panel_rect.topleft)
        pygame.draw.rect(screen, (46, 98, 185), self.menu_panel_rect, 1, border_radius=24)
        pygame.draw.line(
            screen,
            (75, 150, 235),
            (self.menu_panel_rect.centerx, self.menu_panel_rect.y + 18),
            (self.menu_panel_rect.centerx, self.menu_panel_rect.bottom - 18),
            1,
        )

        title_panel_surf = pygame.Surface((self.title_panel_rect.w, self.title_panel_rect.h), pygame.SRCALPHA)
        draw_vertical_gradient(title_panel_surf, (8, 22, 56, 158), (6, 16, 36, 205))
        pygame.draw.rect(title_panel_surf, (255, 255, 255, 20), (0, 0, self.title_panel_rect.w, 34), border_radius=28)
        screen.blit(title_panel_surf, self.title_panel_rect.topleft)
        pygame.draw.rect(screen, (75, 170, 255), self.title_panel_rect, 3, border_radius=28)
        pygame.draw.line(
            screen,
            (130, 220, 255),
            (self.title_panel_rect.x + 28, self.title_panel_rect.bottom - 42),
            (self.title_panel_rect.right - 28, self.title_panel_rect.bottom - 42),
            1,
        )

        tag_surf = self.tag_font.render("NEURAL MAZE PROTOCOL", True, WHITE)
        tag_rect = tag_surf.get_rect(center=(WIDTH // 2, 115))
        screen.blit(tag_surf, tag_rect)

        title_surf = self.title_font.render("MAZEVERSE AI", True, CYAN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 170))
        glow_surf = self.title_font.render("MAZEVERSE AI", True, (0, 245, 255, 60))
        screen.blit(glow_surf, (title_rect.x, title_rect.y + 4))
        screen.blit(title_surf, title_rect)

        subtitle_surf = self.subtitle_font.render("Adaptive intelligent navigation system", True, (190, 222, 255))
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 220))
        screen.blit(subtitle_surf, subtitle_rect)

        ai_label = self.runtime_settings.get("ai_difficulty", "Medium")
        self.buttons[3].text = f"AI DIFFICULTY: {ai_label.upper()}"

        for btn in self.buttons:
            btn.draw(screen, self.font)

        hint_surf = self.small_font.render("Arrow keys / W-S to move   Enter to select", True, TEXT_MUTED)
        hint_rect = hint_surf.get_rect(center=(WIDTH // 2, self.menu_panel_rect.bottom + 22))
        screen.blit(hint_surf, hint_rect)

        ver_surf = self.small_font.render("v2.5.0 | Education Edition", True, TEXT_MUTED)
        screen.blit(ver_surf, (20, HEIGHT - 30))
