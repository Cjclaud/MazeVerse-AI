import math
import random
import pygame
from app_paths import resolve_existing_path
from settings import WIDTH, HEIGHT, DEEP_SPACE, SOFT_CYAN, ELECTRIC_BLUE, WHITE


class LevelCard:
    def __init__(self, level_number, rect):
        self.level_number = level_number
        self.rect = rect


class LevelSelect:
    def __init__(self, total_levels=15):
        self.title_font = pygame.font.SysFont("arial", 54, bold=True)
        self.level_font = pygame.font.SysFont("arial", 40, bold=True)
        self.small_font = pygame.font.SysFont("arial", 18, bold=True)
        self.info_font = pygame.font.SysFont("arial", 15)
        self.lock_font = pygame.font.SysFont("arial", 15, bold=True)

        try:
            self.bg = pygame.image.load(resolve_existing_path("assets/space_bg.png")).convert()
            self.bg = pygame.transform.scale(self.bg, (WIDTH, HEIGHT))
        except Exception:
            self.bg = None

        self.stars = self.create_stars(120)
        self.anim_time = 0

        self.total_levels = total_levels
        self.unlocked_levels = 1
        self.completed_levels = set()
        self.progress_data = {}
        self.stats_mode = "Solo"

        self.cards = []
        self.back_rect = None
        self.next_rect = None
        self.prev_rect = None
        self.solo_toggle_rect = None
        self.vs_ai_toggle_rect = None

        self.cards_per_page = 9
        self.current_page = 0
        self.selected_index = 0

        # -------------------------
        # CLEAN LAYOUT
        # -------------------------
        self.panel_width = 1080
        self.panel_height = 600
        self.panel_x = (WIDTH - self.panel_width) // 2
        self.panel_y = 185

        self.grid_cols = 3
        self.grid_rows = 3

        # Reduced so 3 rows fit properly
        self.card_width = 240
        self.card_height = 135
        self.gap_x = 115
        self.gap_y = 26

        grid_width = self.grid_cols * self.card_width + (self.grid_cols - 1) * self.gap_x
        self.grid_start_x = (WIDTH - grid_width) // 2
        self.grid_start_y = self.panel_y + 78

        # Controls are now BELOW the cards
        self.page_label_y = self.panel_y + self.panel_height - 92
        self.button_y = self.panel_y + self.panel_height - 54
        self.footer_y = HEIGHT - 22

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
        self.progress_data = data or {}

        completed = []
        for level_str, pdata in self.progress_data.items():
            if pdata.get("completed"):
                try:
                    completed.append(int(level_str))
                except ValueError:
                    pass

        self.completed_levels = set(completed)

        if completed:
            self.unlocked_levels = min(self.total_levels, max(completed) + 1)
        else:
            self.unlocked_levels = 1

    def set_stats_mode(self, mode):
        self.stats_mode = "VS AI" if mode == "VS AI" else "Solo"

    def get_mode_stats(self, level_num):
        level_key = str(level_num)
        pdata = self.progress_data.get(level_key, {})
        mode_stats = pdata.get("mode_stats", {})
        selected = mode_stats.get(self.stats_mode)
        if isinstance(selected, dict):
            return selected
        return {
            "completed": bool(pdata.get("completed", False)),
            "best_score": int(pdata.get("best_score", 0) or 0),
            "best_ai_score": int(pdata.get("best_ai_score", 0) or 0),
            "best_time": pdata.get("best_time"),
            "items_used": list(pdata.get("items_used", [])),
        }

    def create_level_cards(self):
        self.cards = []

        start_level = self.current_page * self.cards_per_page + 1
        end_level = min(start_level + self.cards_per_page - 1, self.total_levels)

        visible_levels = list(range(start_level, end_level + 1))

        for i, level_num in enumerate(visible_levels):
            row = i // self.grid_cols
            col = i % self.grid_cols

            x = self.grid_start_x + col * (self.card_width + self.gap_x)
            y = self.grid_start_y + row * (self.card_height + self.gap_y)

            rect = pygame.Rect(x, y, self.card_width, self.card_height)
            self.cards.append(LevelCard(level_num, rect))

        self.back_rect = pygame.Rect(WIDTH // 2 - 140, self.button_y, 280, 54)
        self.prev_rect = pygame.Rect(self.panel_x + 24, self.button_y, 150, 54)
        self.next_rect = pygame.Rect(self.panel_x + self.panel_width - 174, self.button_y, 150, 54)
        self.solo_toggle_rect = pygame.Rect(self.panel_x + 26, self.panel_y + 18, 118, 38)
        self.vs_ai_toggle_rect = pygame.Rect(self.panel_x + 154, self.panel_y + 18, 128, 38)

        self.selected_index = min(self.selected_index, max(0, len(self.cards) - 1))

    def update(self):
        self.anim_time += 1

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
            cols = self.grid_cols

            if event.key == pygame.K_LEFT and self.selected_index < len(self.cards):
                self.selected_index = max(0, self.selected_index - 1)

            elif event.key == pygame.K_RIGHT and self.selected_index < len(self.cards):
                self.selected_index = min(len(self.cards) - 1, self.selected_index + 1)

            elif event.key == pygame.K_UP and self.selected_index < len(self.cards):
                self.selected_index = max(0, self.selected_index - cols)

            elif event.key == pygame.K_DOWN and self.selected_index < len(self.cards):
                self.selected_index = min(len(self.cards) - 1, self.selected_index + cols)

            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.selected_index < len(self.cards):
                    level_num = self.cards[self.selected_index].level_number
                    if level_num <= self.unlocked_levels:
                        return {"action": "play_level", "level": level_num}

            elif event.key == pygame.K_ESCAPE:
                return {"action": "back"}
            elif event.key == pygame.K_TAB:
                self.stats_mode = "VS AI" if self.stats_mode == "Solo" else "Solo"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.solo_toggle_rect and self.solo_toggle_rect.collidepoint(event.pos):
                self.stats_mode = "Solo"
                return None

            if self.vs_ai_toggle_rect and self.vs_ai_toggle_rect.collidepoint(event.pos):
                self.stats_mode = "VS AI"
                return None

            for i, card in enumerate(self.cards):
                if card.rect.collidepoint(event.pos):
                    self.selected_index = i
                    level_num = card.level_number
                    if level_num <= self.unlocked_levels:
                        return {"action": "play_level", "level": level_num}

            if self.back_rect and self.back_rect.collidepoint(event.pos):
                return {"action": "back"}

            if self.prev_rect and self.prev_rect.collidepoint(event.pos):
                if self.current_page > 0:
                    self.current_page -= 1
                    self.create_level_cards()

            if self.next_rect and self.next_rect.collidepoint(event.pos):
                max_page = (self.total_levels - 1) // self.cards_per_page
                if self.current_page < max_page:
                    self.current_page += 1
                    self.create_level_cards()

        return None

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
        title_y = 96

        for offset in range(8, 0, -2):
            glow_surf = self.title_font.render("SELECT LEVEL", True, ELECTRIC_BLUE)
            glow_surf.set_alpha(22)
            glow_rect = glow_surf.get_rect(center=(WIDTH // 2, title_y))
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                screen.blit(glow_surf, glow_rect.move(dx, dy))

        title_surf = self.title_font.render("SELECT LEVEL", True, SOFT_CYAN)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, title_y))
        screen.blit(title_surf, title_rect)

    def draw_progress_bar(self, screen):
        completed = len(self.completed_levels)
        total = self.total_levels
        progress = completed / total if total > 0 else 0

        bar_width = 480
        bar_height = 14
        x = (WIDTH - bar_width) // 2
        y = 150

        pygame.draw.rect(screen, (35, 55, 95), (x, y, bar_width, bar_height), border_radius=7)

        fill_width = int(bar_width * progress)
        if fill_width > 0:
            pygame.draw.rect(screen, (0, 220, 255), (x, y, fill_width, bar_height), border_radius=7)

        text = self.small_font.render(
            f"Progress: {completed}/{total} COMPLETED",
            True,
            (180, 220, 255)
        )
        screen.blit(text, text.get_rect(midleft=(x, y - 12)))

    def draw_panel(self, screen):
        for i in range(18, 0, -4):
            glow_surf = pygame.Surface(
                (self.panel_width + i * 2, self.panel_height + i * 2),
                pygame.SRCALPHA
            )
            pygame.draw.rect(glow_surf, (0, 120, 255, 12), glow_surf.get_rect(), border_radius=24)
            screen.blit(glow_surf, (self.panel_x - i, self.panel_y - i))

        panel = pygame.Surface((self.panel_width, self.panel_height), pygame.SRCALPHA)
        panel.fill((12, 22, 46, 150))
        screen.blit(panel, (self.panel_x, self.panel_y))
        pygame.draw.rect(
            screen,
            (80, 160, 255),
            (self.panel_x, self.panel_y, self.panel_width, self.panel_height),
            2,
            border_radius=24
        )

    def draw_stats_toggle(self, screen):
        label = self.info_font.render("STAT VIEW", True, (175, 215, 255))
        screen.blit(label, (self.panel_x + 304, self.panel_y + 30))

        for rect, text, active in (
            (self.solo_toggle_rect, "SOLO", self.stats_mode == "Solo"),
            (self.vs_ai_toggle_rect, "VS AI", self.stats_mode == "VS AI"),
        ):
            fill = (18, 72, 116) if active else (16, 28, 56)
            border = (120, 235, 255) if active else (80, 150, 220)
            pygame.draw.rect(screen, fill, rect, border_radius=14)
            pygame.draw.rect(screen, border, rect, 2, border_radius=14)
            text_surf = self.small_font.render(text, True, WHITE if active else SOFT_CYAN)
            screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def draw_locked_pattern(self, screen, rect):
        pattern_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for x in range(-rect.height, rect.width, 18):
            pygame.draw.line(
                pattern_surface,
                (100, 100, 120, 35),
                (x, 0),
                (x + rect.height, rect.height),
                2
            )
        screen.blit(pattern_surface, rect.topleft)

    def draw_level_cards(self, screen):
        pulse = 0.5 + 0.5 * math.sin(self.anim_time * 0.08)

        for i, card in enumerate(self.cards):
            level_num = card.level_number
            selected = (self.selected_index == i)
            unlocked = level_num <= self.unlocked_levels

            rect = card.rect.inflate(8, 8) if selected else card.rect.copy()

            if selected:
                alpha = int(10 + 16 * pulse)
                for glow_size in range(20, 0, -4):
                    glow = pygame.Surface((rect.width + glow_size * 2, rect.height + glow_size * 2), pygame.SRCALPHA)
                    pygame.draw.rect(glow, (0, 210, 255, alpha), glow.get_rect(), border_radius=22)
                    screen.blit(glow, (rect.x - glow_size, rect.y - glow_size))

            if unlocked:
                body = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(body, (14, 28, 60, 225), body.get_rect(), border_radius=20)
                screen.blit(body, rect.topleft)

                gloss = pygame.Surface((rect.width - 14, 28), pygame.SRCALPHA)
                pygame.draw.rect(gloss, (255, 255, 255, 14), gloss.get_rect(), border_radius=12)
                screen.blit(gloss, (rect.x + 7, rect.y + 6))

                border_color = (0, 245, 255) if selected else (0, 190, 230)
                pygame.draw.rect(screen, border_color, rect, 2, border_radius=20)

                level_key = str(level_num)
                mode_pdata = self.get_mode_stats(level_num)

                if mode_pdata.get("completed"):
                    badge_rect = pygame.Rect(rect.x + 12, rect.y + 10, 112, 28)
                    pygame.draw.rect(screen, (18, 72, 48), badge_rect, border_radius=12)
                    badge_text = self.small_font.render("COMPLETED", True, (90, 255, 160))
                    screen.blit(badge_text, badge_text.get_rect(center=badge_rect.center))

                    level_surf = self.level_font.render(f"{level_num:02}", True, WHITE)
                    level_rect = level_surf.get_rect(center=(rect.centerx, rect.y + 58))
                    screen.blit(level_surf, level_rect)

                    left_label = "BEST"
                    right_label = "AI" if self.stats_mode == "VS AI" else "TIME"
                    best_value_text = str(mode_pdata.get("best_score", 0))
                    best_time = mode_pdata.get("best_time")
                    right_value_text = (
                        str(mode_pdata.get("best_ai_score", 0))
                        if self.stats_mode == "VS AI"
                        else ("--" if best_time is None else f"{best_time}s")
                    )

                    best_label = self.info_font.render(left_label, True, (155, 185, 230))
                    right_label_surf = self.info_font.render(right_label, True, (0, 245, 255))
                    best_value = self.small_font.render(best_value_text, True, WHITE)
                    right_value = self.small_font.render(right_value_text, True, SOFT_CYAN)

                    screen.blit(best_label, (rect.x + 18, rect.bottom - 38))
                    screen.blit(right_label_surf, (rect.right - 48, rect.bottom - 38))
                    screen.blit(best_value, (rect.x + 18, rect.bottom - 20))
                    screen.blit(right_value, (rect.right - 48, rect.bottom - 20))

                    if self.stats_mode == "VS AI":
                        best_ai_difficulty = mode_pdata.get("best_ai_difficulty_beaten")
                        if best_ai_difficulty:
                            diff_badge = pygame.Rect(rect.x + 126, rect.y + 10, 102, 28)
                            pygame.draw.rect(screen, (52, 22, 84), diff_badge, border_radius=12)
                            pygame.draw.rect(screen, (190, 130, 255), diff_badge, 2, border_radius=12)
                            diff_text = self.info_font.render(best_ai_difficulty.upper(), True, (235, 220, 255))
                            screen.blit(diff_text, diff_text.get_rect(center=diff_badge.center))
                else:
                    level_surf = self.level_font.render(f"{level_num:02}", True, SOFT_CYAN if selected else WHITE)
                    level_rect = level_surf.get_rect(center=(rect.centerx, rect.y + 58))
                    screen.blit(level_surf, level_rect)

                    ready_label = "UNPLAYED" if self.stats_mode == "Solo" else "NO VS AI RUN"
                    ready_text = self.small_font.render(ready_label, True, (120, 220, 255))
                    screen.blit(ready_text, ready_text.get_rect(center=(rect.centerx, rect.bottom - 16)))

                difficulty = "Easy" if level_num <= 3 else "Medium" if level_num <= 7 else "Hard"
                diff_color = (
                    (100, 255, 140) if difficulty == "Easy"
                    else (255, 200, 80) if difficulty == "Medium"
                    else (255, 90, 90)
                )
                diff_text = self.info_font.render(f"● {difficulty}", True, diff_color)
                diff_rect = diff_text.get_rect(center=(rect.centerx, rect.bottom + 16))
                screen.blit(diff_text, diff_rect)

            else:
                body = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(body, (18, 20, 34, 210), body.get_rect(), border_radius=20)
                screen.blit(body, rect.topleft)
                pygame.draw.rect(screen, (90, 90, 120), rect, 2, border_radius=20)
                self.draw_locked_pattern(screen, rect)

                lock_circle_center = (rect.centerx, rect.y + 42)
                pygame.draw.circle(screen, (38, 38, 56), lock_circle_center, 20)
                pygame.draw.circle(screen, (120, 120, 150), lock_circle_center, 20, 2)

                lock_text = self.lock_font.render("LOCK", True, (185, 185, 210))
                screen.blit(lock_text, lock_text.get_rect(center=lock_circle_center))

                locked_text = self.small_font.render("LOCKED", True, (165, 165, 185))
                screen.blit(locked_text, locked_text.get_rect(center=(rect.centerx, rect.y + 80)))

                req_text = self.info_font.render("Finish previous", True, (120, 120, 145))
                screen.blit(req_text, req_text.get_rect(center=(rect.centerx, rect.bottom - 18)))

    def draw_button(self, screen, rect, text):
        mouse = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse)
        glow_color = (0, 255, 255) if hovered else (0, 150, 255)

        if hovered:
            for g in range(12, 0, -3):
                glow = pygame.Surface((rect.width + g * 2, rect.height + g * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*glow_color, 20), glow.get_rect(), border_radius=14)
                screen.blit(glow, (rect.x - g, rect.y - g))

        pygame.draw.rect(screen, (20, 35, 70), rect, border_radius=14)
        pygame.draw.rect(screen, glow_color, rect, 2, border_radius=14)

        text_surf = self.small_font.render(text, True, WHITE)
        screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def draw_navigation(self, screen):
        max_page = (self.total_levels - 1) // self.cards_per_page

        page_text = self.small_font.render(
            f"PAGE {self.current_page + 1} / {max_page + 1}",
            True,
            (170, 205, 255)
        )
        page_rect = page_text.get_rect(center=(WIDTH // 2, self.page_label_y))
        screen.blit(page_text, page_rect)

        if self.current_page > 0:
            self.draw_button(screen, self.prev_rect, "PREV")

        self.draw_button(screen, self.back_rect, "BACK")

        if self.current_page < max_page:
            self.draw_button(screen, self.next_rect, "NEXT")

    def draw_footer(self, screen):
        info = self.info_font.render(
            "Select a level to begin your mission  |  TAB switches stats  |  ESC to return",
            True,
            (170, 205, 255)
        )
        info_rect = info.get_rect(center=(WIDTH // 2, self.footer_y))
        screen.blit(info, info_rect)

    def draw_gradient_background(self, screen):
        for y in range(HEIGHT):
            blend = y / HEIGHT
            r = int(DEEP_SPACE[0] * (1 - blend) + 10 * blend)
            g = int(DEEP_SPACE[1] * (1 - blend) + 15 * blend)
            b = int(DEEP_SPACE[2] * (1 - blend) + 45 * blend)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    def draw(self, screen):
        if self.bg:
            screen.blit(self.bg, (0, 0))
        else:
            self.draw_gradient_background(screen)
        self.draw_stars(screen)
        self.draw_title(screen)
        self.draw_progress_bar(screen)
        self.draw_panel(screen)
        self.draw_stats_toggle(screen)
        self.draw_level_cards(screen)
        self.draw_navigation(screen)
        self.draw_footer(screen)
