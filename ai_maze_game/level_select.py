import random
import pygame
from settings import WIDTH, HEIGHT, DEEP_SPACE, CYAN, SOFT_CYAN, ELECTRIC_BLUE, WHITE


class LevelCard:
    def __init__(self, level_number, rect):
        self.level_number = level_number
        self.rect = rect


class LevelSelect:
    def __init__(self, total_levels=15):
        self.title_font = pygame.font.SysFont("arial", 54, bold=True)
        self.level_font = pygame.font.SysFont("arial", 34, bold=True)
        self.small_font = pygame.font.SysFont("arial", 20, bold=True)
        self.info_font = pygame.font.SysFont("arial", 18)
        self.lock_font = pygame.font.SysFont("arial", 18, bold=True)

        self.stars = self.create_stars(120)

        self.total_levels = total_levels
        self.unlocked_levels = 8
        self.completed_levels = {1, 2, 3}

        self.cards = []
        self.back_rect = None
        self.next_rect = None
        self.prev_rect = None

        self.cards_per_page = 9
        self.current_page = 0

        self.selected_index = 0
        self.create_level_cards()

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

    def set_progress(self, unlocked_levels, completed_levels):
        self.unlocked_levels = unlocked_levels
        self.completed_levels = set(completed_levels)

    def set_progress_data(self, data):
        self.progress_data = data

    def create_level_cards(self):
        self.cards = []

        start_level = self.current_page * self.cards_per_page + 1
        end_level = min(start_level + self.cards_per_page - 1, self.total_levels)

        cols = 3
        card_width = 150
        card_height = 100
        gap_x = 40
        gap_y = 30

        total_width = cols * card_width + (cols - 1) * gap_x
        start_x = (WIDTH - total_width) // 2
        start_y = 190

        visible_levels = list(range(start_level, end_level + 1))

        for i, level_num in enumerate(visible_levels):
            row = i // cols
            col = i % cols

            x = start_x + col * (card_width + gap_x)
            y = start_y + row * (card_height + gap_y)

            rect = pygame.Rect(x, y, card_width, card_height)
            self.cards.append(LevelCard(level_num, rect))

        self.back_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 95, 200, 50)
        self.prev_rect = pygame.Rect(150, HEIGHT - 95, 120, 50)
        self.next_rect = pygame.Rect(WIDTH - 270, HEIGHT - 95, 120, 50)

        self.selected_index = min(self.selected_index, len(self.cards))

    def update(self):
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, WIDTH)

        mouse_pos = pygame.mouse.get_pos()

        for i, card in enumerate(self.cards):
            if card.rect.collidepoint(mouse_pos):
                self.selected_index = i
                return

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            cols = 3

            if event.key == pygame.K_LEFT:
                if self.selected_index < len(self.cards):
                    self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_RIGHT:
                if self.selected_index < len(self.cards):
                    self.selected_index = min(len(self.cards) - 1, self.selected_index + 1)

            elif event.key == pygame.K_UP:
                if self.selected_index < len(self.cards):
                    self.selected_index = max(0, self.selected_index - cols)

            elif event.key == pygame.K_DOWN:
                if self.selected_index < len(self.cards):
                    self.selected_index = min(len(self.cards) - 1, self.selected_index + cols)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.selected_index < len(self.cards):
                    level_num = self.cards[self.selected_index].level_number
                    if level_num <= self.unlocked_levels:
                        return {"action": "play_level", "level": level_num}

            elif event.key == pygame.K_ESCAPE:
                return {"action": "back"}

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, card in enumerate(self.cards):
                if card.rect.collidepoint(event.pos):
                    self.selected_index = i
                    level_num = card.level_number
                    if level_num <= self.unlocked_levels:
                        return {"action": "play_level", "level": level_num}

            if self.back_rect.collidepoint(event.pos):
                return {"action": "back"}

            if self.prev_rect.collidepoint(event.pos):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.create_level_cards()

            if self.next_rect.collidepoint(event.pos):
                max_page = (self.total_levels - 1) // self.cards_per_page
                if self.current_page < max_page:
                    self.current_page += 1
                    self.create_level_cards()

        return None

    def draw_gradient_background(self, screen):
        for y in range(HEIGHT):
            blend = y / HEIGHT
            r = int(DEEP_SPACE[0] * (1 - blend) + 8 * blend)
            g = int(DEEP_SPACE[1] * (1 - blend) + 16 * blend)
            b = int(DEEP_SPACE[2] * (1 - blend) + 48 * blend)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    def draw_stars(self, screen):
        for star in self.stars:
            surf = pygame.Surface((star["r"] * 4, star["r"] * 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 220, 255, star["alpha"]), (star["r"] * 2, star["r"] * 2), star["r"])
            screen.blit(surf, (star["x"], star["y"]))

    def draw_title(self, screen):
        for offset in range(8, 0, -2):
            glow_surf = self.title_font.render("SELECT LEVEL", True, ELECTRIC_BLUE)
            glow_surf.set_alpha(22)
            glow_rect = glow_surf.get_rect(center=(WIDTH // 2, 90))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow_surf, glow_rect.move(dx, dy))

        title_surf = self.title_font.render("SELECT LEVEL", True, SOFT_CYAN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 90))
        screen.blit(title_surf, title_rect)

    def draw_panel(self, screen):
        panel_width = 700
        panel_height = 470
        panel_x = (WIDTH - panel_width) // 2
        panel_y = 140

        for i in range(18, 0, -4):
            glow_surf = pygame.Surface((panel_width + i * 2, panel_height + i * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 120, 255, 12), glow_surf.get_rect(), border_radius=24)
            screen.blit(glow_surf, (panel_x - i, panel_y - i))

        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((12, 22, 46, 160))
        screen.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(screen, (80, 160, 255), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=22)

    def draw_locked_pattern(self, screen, rect):
        pattern_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        for x in range(-rect.height, rect.width, 18):
            pygame.draw.line(pattern_surface, (100, 100, 120, 35), (x, 0), (x + rect.height, rect.height), 2)

        screen.blit(pattern_surface, (rect.x, rect.y))

    def draw_level_cards(self, screen):
        for i, card in enumerate(self.cards):
            level_num = card.level_number
            selected = (self.selected_index == i)
            unlocked = level_num <= self.unlocked_levels
            completed = level_num in self.completed_levels

            if selected:
                for glow_size in range(12, 0, -3):
                    glow = pygame.Surface((card.rect.width + glow_size * 2, card.rect.height + glow_size * 2), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (0, 200, 255, 16), glow.get_rect(), border_radius=18)
                    screen.blit(glow, (card.rect.x - glow_size, card.rect.y - glow_size))

            if unlocked:
                fill_color = (20, 32, 62) if selected else (16, 24, 48)
                border_color = CYAN if selected else (70, 150, 255)

                pygame.draw.rect(screen, fill_color, card.rect, border_radius=18)
                pygame.draw.rect(screen, border_color, card.rect, 2, border_radius=18)

                level_key = str(level_num)
                pdata = getattr(self, "progress_data", {}).get(level_key)

                if pdata and pdata.get("completed"):
                    # badge
                    badge_rect = pygame.Rect(card.rect.x + 10, card.rect.y + 10, 92, 24)
                    pygame.draw.rect(screen, (18, 60, 40), badge_rect, border_radius=10)
                    badge_text = self.small_font.render("COMPLETED", True, (90, 255, 160))
                    screen.blit(badge_text, (badge_rect.x + 8, badge_rect.y + 3))

                    # level number big and centered
                    level_surf = self.level_font.render(f"{level_num:02}", True, WHITE)
                    level_rect = level_surf.get_rect(center=(card.rect.centerx, card.rect.y + 54))
                    screen.blit(level_surf, level_rect)

                    # labels
                    best_label = self.lock_font.render("BEST", True, (150, 180, 230))
                    ai_label = self.lock_font.render("AI", True, (0, 255, 255))
                    screen.blit(best_label, (card.rect.x + 14, card.rect.bottom - 34))
                    screen.blit(ai_label, (card.rect.right - 40, card.rect.bottom - 34))

                    # values
                    best_value = self.small_font.render(str(pdata.get("best_score", 0)), True, WHITE)
                    ai_value = self.small_font.render(str(pdata.get("best_ai_score", 0)), True, SOFT_CYAN)
                    screen.blit(best_value, (card.rect.x + 14, card.rect.bottom - 18))
                    screen.blit(ai_value, (card.rect.right - 40, card.rect.bottom - 18))

                else:
                    level_surf = self.level_font.render(f"{level_num:02}", True, SOFT_CYAN if selected else WHITE)
                    level_rect = level_surf.get_rect(center=(card.rect.centerx, card.rect.centery - 8))
                    screen.blit(level_surf, level_rect)

                    ready_text = self.small_font.render("READY", True, (120, 220, 255))
                    ready_rect = ready_text.get_rect(center=(card.rect.centerx, card.rect.bottom - 22))
                    screen.blit(ready_text, ready_rect)

            else:
                pygame.draw.rect(screen, (20, 20, 32), card.rect, border_radius=18)
                pygame.draw.rect(screen, (90, 90, 120), card.rect, 2, border_radius=18)
                self.draw_locked_pattern(screen, card.rect)

                lock_circle_center = (card.rect.centerx, card.rect.y + 38)
                pygame.draw.circle(screen, (38, 38, 56), lock_circle_center, 20)
                pygame.draw.circle(screen, (120, 120, 150), lock_circle_center, 20, 2)

                lock_text = self.lock_font.render("LOCK", True, (185, 185, 210))
                lock_rect = lock_text.get_rect(center=lock_circle_center)
                screen.blit(lock_text, lock_rect)

                locked_text = self.small_font.render("LOCKED", True, (165, 165, 185))
                locked_rect = locked_text.get_rect(center=(card.rect.centerx, card.rect.y + 74))
                screen.blit(locked_text, locked_rect)

                req_text = self.lock_font.render("Finish previous", True, (120, 120, 145))
                req_rect = req_text.get_rect(center=(card.rect.centerx, card.rect.bottom - 16))
                screen.blit(req_text, req_rect)

    def draw_button(self, screen, rect, text, active=False):
        if active:
            for glow_size in range(10, 0, -2):
                glow = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow, (0, 200, 255, 16), glow.get_rect(), border_radius=14)
                screen.blit(glow, (rect.x - glow_size, rect.y - glow_size))

        fill_color = (24, 40, 72) if active else (18, 28, 55)
        border_color = CYAN if active else (70, 150, 255)

        pygame.draw.rect(screen, fill_color, rect, border_radius=14)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=14)

        text_surf = self.small_font.render(text, True, SOFT_CYAN if active else WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)

    def draw_navigation(self, screen):
        max_page = (self.total_levels - 1) // self.cards_per_page
        page_text = self.small_font.render(f"PAGE {self.current_page + 1} / {max_page + 1}", True, (170, 205, 255))
        page_rect = page_text.get_rect(center=(WIDTH // 2, HEIGHT - 125))
        screen.blit(page_text, page_rect)

        if self.current_page > 0:
            self.draw_button(screen, self.prev_rect, "PREV")

        if self.current_page < max_page:
            self.draw_button(screen, self.next_rect, "NEXT")

        self.draw_button(screen, self.back_rect, "BACK")

    def draw_footer(self, screen):
        info = self.info_font.render("Click unlocked level to start | ESC = Back", True, (170, 205, 255))
        info_rect = info.get_rect(center=(WIDTH // 2, HEIGHT - 24))
        screen.blit(info, info_rect)

    def draw(self, screen):
        self.draw_gradient_background(screen)
        self.draw_stars(screen)
        self.draw_title(screen)
        self.draw_panel(screen)
        self.draw_level_cards(screen)
        self.draw_navigation(screen)
        self.draw_footer(screen)
