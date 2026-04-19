import math
import random
import pygame
from app_paths import resolve_existing_path

# Global settings from main context
WIDTH, HEIGHT = 1280, 820
CYAN = (0, 245, 255)
WHITE = (255, 255, 255)
TEXT_SUBCOLOR = (160, 200, 255)

class MenuButton:
    def __init__(self, text, x, y, w, h, action, icon=""):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.action = action
        self.icon = icon
        self.is_hovered = False
        self.hover_offset = 0
        self.glow_alpha = 0

    def draw(self, screen, font):
        # Smooth hover animations
        target_offset = 12 if self.is_hovered else 0
        self.hover_offset += (target_offset - self.hover_offset) * 0.2
        
        target_glow = 255 if self.is_hovered else 0
        self.glow_alpha += (target_glow - self.glow_alpha) * 0.15

        draw_rect = self.rect.copy()
        draw_rect.x += self.hover_offset

        # Outer Glow Layer
        if self.glow_alpha > 5:
            glow_surf = pygame.Surface((draw_rect.w + 20, draw_rect.h + 20), pygame.SRCALPHA)
            for i in range(5):
                alpha = int((self.glow_alpha / (i + 1)) * 0.3)
                pygame.draw.rect(glow_surf, (0, 245, 255, alpha), (10-i*2, 10-i*2, draw_rect.w+i*4, draw_rect.h+i*4), border_radius=12+i)
            screen.blit(glow_surf, (draw_rect.x - 10, draw_rect.y - 10))

        # Main Button Body (Glass effect)
        bg_alpha = 180 if self.is_hovered else 140
        bg_surf = pygame.Surface((draw_rect.w, draw_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (15, 30, 60, bg_alpha), (0,0,draw_rect.w, draw_rect.h), border_radius=12)
        screen.blit(bg_surf, (draw_rect.x, draw_rect.y))
        
        # Border
        border_color = CYAN if self.is_hovered else (40, 80, 150)
        pygame.draw.rect(screen, border_color, draw_rect, 2, border_radius=12)

        # Text and Icon
        label = f"{self.icon} {self.text}" if self.icon else self.text
        text_color = WHITE if self.is_hovered else TEXT_SUBCOLOR
        text_surf = font.render(label, True, text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

class MainMenu:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.title_font = pygame.font.SysFont("arial", 48, bold=True)
        
        # Modern Button Layout
        button_width = 320
        button_height = 48
        gap = 12
        start_x = (WIDTH - button_width) // 2
        start_y = 310
        
        self.buttons = [
            MenuButton("START SOLO", start_x, start_y, button_width, button_height, "start_solo", "⚡"),
            MenuButton("PLAY VS AI", start_x, start_y + (button_height + gap), button_width, button_height, "start_vs_ai", "🤖"),
            MenuButton("MOBILE RACE", start_x, start_y + 2 * (button_height + gap), button_width, button_height, "mobile_race", "📱"),
            MenuButton("AI DIFFICULTY", start_x, start_y + 3 * (button_height + gap), button_width, button_height, "cycle_ai_difficulty", "⚙️"),
            MenuButton("SELECT LEVEL", start_x, start_y + 4 * (button_height + gap), button_width, button_height, "level_select", "📍"),
            MenuButton("SETTINGS", start_x, start_y + 5 * (button_height + gap), button_width, button_height, "settings", "🛠️"),
            MenuButton("EXIT", start_x, start_y + 6 * (button_height + gap), button_width, button_height, "exit", "✖"),
        ]
        
        self.runtime_settings = {}
        self.click_sound = None
        self.load_background()
        self.bg_zoom = 1.0
        self.grid_scroll = 0

    def load_background(self):
        try:
            self.background = pygame.image.load(resolve_existing_path("assets/menu_bg.png")).convert()
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except:
            self.background = None

    def set_click_sound(self, sound):
        self.click_sound = sound

    def update(self):
        mx, my = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.is_hovered = btn.rect.collidepoint((mx, my))
        
        self.grid_scroll = (self.grid_scroll + 2) % 40
        self.bg_zoom = 1.0 + 0.02 * math.sin(pygame.time.get_ticks() * 0.001)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.is_hovered:
                    if self.click_sound:
                        self.click_sound.play()
                    
                    if btn.action == "cycle_ai_difficulty":
                        diffs = ["Easy", "Medium", "Hard"]
                        curr = self.runtime_settings.get("ai_difficulty", "Medium")
                        nxt = diffs[(diffs.index(curr) + 1) % len(diffs)]
                        self.runtime_settings["ai_difficulty"] = nxt
                    
                    return btn.action
        return None

    def draw(self, screen):
        # Draw Background Image
        if self.background:
            scaled_bg = pygame.transform.scale(self.background, (int(WIDTH * self.bg_zoom), int(HEIGHT * self.bg_zoom)))
            bg_rect = scaled_bg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(scaled_bg, bg_rect)
        else:
            screen.fill((4, 6, 18))

        # Draw Grid Effect (Original Horizon Style)
        grid_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        horizon_y = HEIGHT - 220
        for x in range(0, WIDTH + 40, 40):
            # Perspective lines
            pygame.draw.line(grid_surf, (0, 245, 255, 40), (WIDTH // 2, horizon_y), (x, HEIGHT), 1)
        
        # Horizontal lines (scrolling)
        for y in range(horizon_y, HEIGHT + 40, 40):
            yy = y + (self.grid_scroll % 40)
            if yy <= HEIGHT:
                alpha = int(255 * ((yy - horizon_y) / (HEIGHT - horizon_y)))
                pygame.draw.line(grid_surf, (0, 245, 255, alpha // 4), (0, yy), (WIDTH, yy), 1)
        
        screen.blit(grid_surf, (0, 0))

        # Draw Title
        title_surf = self.title_font.render("MAZEVERSE AI", True, CYAN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 160))
        
        # Title Glow
        glow_surf = self.title_font.render("MAZEVERSE AI", True, (0, 245, 255, 60))
        screen.blit(glow_surf, (title_rect.x, title_rect.y + 3))
        screen.blit(title_surf, title_rect)
        
        subtitle_surf = self.small_font.render("ADAPTIVE INTELLIGENT NAVIGATION SYSTEM", True, TEXT_SUBCOLOR)
        subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, 215))
        screen.blit(subtitle_surf, subtitle_rect)

        # Update dynamic button text
        ai_label = self.runtime_settings.get("ai_difficulty", "Medium")
        self.buttons[3].text = f"AI DIFFICULTY: {ai_label.upper()}"

        # Draw Buttons
        for btn in self.buttons:
            btn.draw(screen, self.font)

        # Version Info
        ver_surf = self.small_font.render("v2.5.0 | Education Edition", True, (100, 130, 180))
        screen.blit(ver_surf, (20, HEIGHT - 30))
