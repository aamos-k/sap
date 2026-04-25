from __future__ import annotations
import pygame
from entities.limb import LimbId, LIMB_LABELS, LIMB_KEYS
from game.turn_manager import TurnManager, TurnState
from entities.spear import Spear

FONT_SIZE_LARGE  = 20
FONT_SIZE_SMALL  = 14
BTN_W, BTN_H     = 52, 36
BTN_GAP          = 8
BTN_MARGIN_X     = 16
BTN_MARGIN_Y     = 16

BTN_NORMAL   = ( 50,  50,  70)
BTN_HOVER    = ( 70,  70,  90)
BTN_SELECTED = (180, 160,  30)
BTN_BORDER   = (120, 120, 140)
BTN_TEXT     = (230, 230, 230)
LABEL_COL    = (200, 200, 200)
FLASH_COL    = (255, 180,  60)
GAME_OVER_BG = (  0,   0,   0, 180)

SHOP_BG      = ( 20,  18,  30, 210)
SHOP_BORDER  = (100,  80, 180)
SHOP_GOLD    = (255, 210,  60)
SHOP_TITLE   = (200, 160, 255)
SHOP_ITEM_OK = (160, 230, 160)
SHOP_ITEM_NO = ( 90,  90,  90)
SHOP_KEY_COL = (255, 210,  60)
DEPTH_COL    = (100, 200, 255)
GA_COL       = (180, 130, 255)

LIMB_ORDER = [LimbId.LEFT_ARM, LimbId.RIGHT_ARM, LimbId.LEFT_LEG, LimbId.RIGHT_LEG]

SHOP_W = 220
SHOP_ITEM_H = 48
SHOP_PAD = 10


class HUD:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        pygame.font.init()
        self.font_large = pygame.font.SysFont("monospace", FONT_SIZE_LARGE, bold=True)
        self.font_small = pygame.font.SysFont("monospace", FONT_SIZE_SMALL)

        # Pre-compute button rects (bottom-left)
        self.btn_rects: dict[LimbId, pygame.Rect] = {}
        start_x = BTN_MARGIN_X
        y = screen_h - BTN_MARGIN_Y - BTN_H
        for i, lid in enumerate(LIMB_ORDER):
            x = start_x + i * (BTN_W + BTN_GAP)
            self.btn_rects[lid] = pygame.Rect(x, y, BTN_W, BTN_H)

        spear_x = (start_x + len(LIMB_ORDER) * (BTN_W + BTN_GAP) + BTN_GAP * 2)
        self._spear_btn_rect = pygame.Rect(spear_x, y, BTN_W + 8, BTN_H)

        # Shop panel rect (right side, vertically centred)
        self._shop_surf = pygame.Surface((SHOP_W, screen_h), pygame.SRCALPHA)

    def draw(self, screen: pygame.Surface, tm: TurnManager,
             mouse_pos: tuple[int, int], seed: int = 0,
             spear: Spear | None = None,
             depth_tiles: float = 0.0,
             coins: int = 0,
             player_in_shop: bool = False,
             player_hp: int = 10,
             player_max_hp: int = 10,
             hp_upgrade_cost: int = 8,
             reach_upgrade_cost: int = 5,
             generation: int = 0,
             total_deaths: int = 0) -> None:
        self._draw_turn_label(screen, tm)
        self._draw_depth_meter(screen, depth_tiles)
        self._draw_limb_buttons(screen, tm, mouse_pos)
        self._draw_spear_button(screen, tm, mouse_pos, spear)
        self._draw_instructions(screen, tm, spear)
        self._draw_flash(screen, tm)
        self._draw_seed(screen, seed)
        if player_in_shop:
            self._draw_shop(screen, coins, player_hp, player_max_hp,
                            hp_upgrade_cost, reach_upgrade_cost,
                            generation, total_deaths)
        if tm.state == TurnState.GAME_OVER:
            self._draw_game_over(screen, tm)

    def _draw_turn_label(self, screen: pygame.Surface, tm: TurnManager) -> None:
        if tm.state in (TurnState.PLAYER_SELECT_LIMB, TurnState.PLAYER_SELECT_TARGET,
                        TurnState.PLAYER_RESOLVE, TurnState.ROPE_PLACE):
            text = f"Turn {tm.turn_number}  PLAYER"
            colour = (100, 200, 255)
        elif tm.state in (TurnState.ENEMY_THINK, TurnState.ENEMY_RESOLVE):
            text = f"Turn {tm.turn_number}  ENEMY"
            colour = (255, 120, 60)
        else:
            text = f"Turn {tm.turn_number}"
            colour = (200, 200, 200)

        surf = self.font_large.render(text, True, colour)
        screen.blit(surf, (16, 12))

    def _draw_depth_meter(self, screen: pygame.Surface, depth_tiles: float) -> None:
        depth_int = int(depth_tiles)
        text = f"Depth: {depth_int} m"
        surf = self.font_large.render(text, True, DEPTH_COL)
        screen.blit(surf, (16, 36))

    def _draw_shop(self, screen: pygame.Surface,
                   coins: int, player_hp: int, player_max_hp: int,
                   hp_upgrade_cost: int, reach_upgrade_cost: int,
                   generation: int, total_deaths: int) -> None:
        items = [
            ("[Q]", "Restore HP",    f"{3} coins",      coins >= 3 and player_hp < player_max_hp),
            ("[E]", f"+2 Max HP",    f"{hp_upgrade_cost} coins",    coins >= hp_upgrade_cost),
            ("[Z]", "+Limb Reach",   f"{reach_upgrade_cost} coins", coins >= reach_upgrade_cost),
        ]

        header_h   = 62
        items_h    = len(items) * SHOP_ITEM_H
        footer_h   = 50
        panel_h    = header_h + items_h + footer_h + SHOP_PAD * 2
        panel_x    = self.screen_w - SHOP_W - 12
        panel_y    = self.screen_h // 2 - panel_h // 2

        # Background panel
        panel_surf = pygame.Surface((SHOP_W, panel_h), pygame.SRCALPHA)
        panel_surf.fill(SHOP_BG)
        pygame.draw.rect(panel_surf, SHOP_BORDER, (0, 0, SHOP_W, panel_h), 2, border_radius=6)
        screen.blit(panel_surf, (panel_x, panel_y))

        y = panel_y + SHOP_PAD

        # Title
        title = self.font_large.render("** SHOP **", True, SHOP_TITLE)
        screen.blit(title, (panel_x + SHOP_W // 2 - title.get_width() // 2, y))
        y += title.get_height() + 4

        # Coins
        coin_surf = self.font_large.render(f"Coins: {coins}", True, SHOP_GOLD)
        screen.blit(coin_surf, (panel_x + SHOP_W // 2 - coin_surf.get_width() // 2, y))
        y += coin_surf.get_height() + 8

        # Separator
        pygame.draw.line(screen, SHOP_BORDER,
                         (panel_x + 6, y), (panel_x + SHOP_W - 6, y))
        y += 6

        # Items
        for key_label, item_name, cost_text, affordable in items:
            col = SHOP_ITEM_OK if affordable else SHOP_ITEM_NO
            key_surf  = self.font_large.render(key_label, True, SHOP_KEY_COL if affordable else SHOP_ITEM_NO)
            name_surf = self.font_large.render(item_name, True, col)
            cost_surf = self.font_small.render(cost_text,  True, SHOP_GOLD if affordable else SHOP_ITEM_NO)
            screen.blit(key_surf,  (panel_x + 8,  y + 2))
            screen.blit(name_surf, (panel_x + 52, y + 2))
            screen.blit(cost_surf, (panel_x + 52, y + 24))
            y += SHOP_ITEM_H

        # Footer: GA info
        pygame.draw.line(screen, SHOP_BORDER,
                         (panel_x + 6, y), (panel_x + SHOP_W - 6, y))
        y += 6
        if generation == 0:
            ga_text = "GA: no evolutions yet"
        else:
            ga_text = f"GA Gen {generation}  kills: {total_deaths}"
        ga_surf = self.font_small.render(ga_text, True, GA_COL)
        screen.blit(ga_surf, (panel_x + SHOP_W // 2 - ga_surf.get_width() // 2, y))

    def _draw_limb_buttons(self, screen: pygame.Surface, tm: TurnManager,
                           mouse_pos: tuple[int, int]) -> None:
        active = tm.state == TurnState.PLAYER_SELECT_LIMB
        for lid in LIMB_ORDER:
            rect = self.btn_rects[lid]
            is_selected = (tm.selected_limb == lid)
            is_hover = active and rect.collidepoint(mouse_pos)

            if is_selected:
                col = BTN_SELECTED
            elif is_hover:
                col = BTN_HOVER
            else:
                col = BTN_NORMAL if active else (30, 30, 40)

            pygame.draw.rect(screen, col, rect, border_radius=4)
            pygame.draw.rect(screen, BTN_BORDER, rect, 1, border_radius=4)

            label = LIMB_LABELS[lid]
            key   = LIMB_KEYS[lid]
            t1 = self.font_large.render(label, True, BTN_TEXT if active else (80, 80, 80))
            t2 = self.font_small.render(f"[{key}]", True, (150, 150, 150) if active else (50, 50, 50))
            screen.blit(t1, (rect.x + 8, rect.y + 4))
            screen.blit(t2, (rect.x + 6, rect.y + 22))

    def _draw_spear_button(self, screen: pygame.Surface, tm: TurnManager,
                           mouse_pos: tuple[int, int],
                           spear: Spear | None) -> None:
        rect = self._spear_btn_rect
        active = (tm.state == TurnState.PLAYER_SELECT_LIMB and
                  spear is not None and spear.held)
        selected = tm.state == TurnState.PLAYER_SELECT_THROW

        if selected:
            col = (180, 60, 30)
        elif active:
            col = BTN_NORMAL if not rect.collidepoint(mouse_pos) else BTN_HOVER
        else:
            col = (30, 30, 40)

        pygame.draw.rect(screen, col, rect, border_radius=4)
        pygame.draw.rect(screen, BTN_BORDER, rect, 1, border_radius=4)

        label_col = BTN_TEXT if active or selected else (80, 80, 80)
        key_col   = (150, 150, 150) if active or selected else (50, 50, 50)
        t1 = self.font_large.render("SPEAR", True, label_col)
        t2 = self.font_small.render("[T]", True, key_col)
        screen.blit(t1, (rect.x + 4, rect.y + 4))
        screen.blit(t2, (rect.x + 12, rect.y + 22))

        if spear is not None and not spear.held and not spear.in_flight:
            pygame.draw.circle(screen, (255, 220, 80),
                               (rect.right - 8, rect.top + 8), 4)

    def _draw_instructions(self, screen: pygame.Surface, tm: TurnManager,
                           spear: Spear | None = None) -> None:
        if tm.state == TurnState.PLAYER_SELECT_LIMB:
            held = spear is not None and spear.held
            spear_hint = "  |  [T] throw spear" if held else ""
            msg = f"Select a limb (1-4)  |  [R] rope  |  [F] rope step  |  [X] clear rope{spear_hint}"
        elif tm.state == TurnState.PLAYER_SELECT_TARGET:
            lbl = LIMB_LABELS.get(tm.selected_limb, "?")
            msg = f"Moving {lbl} — click target in cave  |  ESC = cancel"
        elif tm.state == TurnState.PLAYER_SELECT_THROW:
            msg = "Click to throw spear  |  ESC = cancel"
        elif tm.state == TurnState.ROPE_PLACE:
            msg = "Rope: click to add waypoint  |  [X] undo  |  [R]/ESC = done"
        elif tm.state in (TurnState.ENEMY_THINK, TurnState.ENEMY_RESOLVE):
            msg = "Enemy is thinking..."
        else:
            msg = ""

        if msg:
            surf = self.font_small.render(msg, True, LABEL_COL)
            screen.blit(surf, (self.screen_w - surf.get_width() - 16,
                               self.screen_h - 20))

    def _draw_flash(self, screen: pygame.Surface, tm: TurnManager) -> None:
        if tm.flash_message:
            surf = self.font_large.render(tm.flash_message, True, FLASH_COL)
            x = self.screen_w // 2 - surf.get_width() // 2
            y = self.screen_h // 2 - 60
            screen.blit(surf, (x, y))

    def _draw_game_over(self, screen: pygame.Surface, tm: TurnManager) -> None:
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        if tm.winner == "player":
            msg = "YOU WIN!"
            col = (100, 255, 120)
        else:
            msg = "YOU DIED"
            col = (255,  80,  60)

        big = pygame.font.SysFont("monospace", 56, bold=True)
        t = big.render(msg, True, col)
        screen.blit(t, (self.screen_w // 2 - t.get_width() // 2,
                        self.screen_h // 2 - 40))
        sub = self.font_large.render("Press R to restart", True, (180, 180, 180))
        screen.blit(sub, (self.screen_w // 2 - sub.get_width() // 2,
                          self.screen_h // 2 + 30))

    def _draw_seed(self, screen: pygame.Surface, seed: int) -> None:
        surf = self.font_small.render(f"seed: {seed}", True, (90, 90, 110))
        screen.blit(surf, (self.screen_w - surf.get_width() - 10, 10))

    def hit_test_limb_button(self, pos: tuple[int, int]) -> LimbId | None:
        for lid, rect in self.btn_rects.items():
            if rect.collidepoint(pos):
                return lid
        return None

    def hit_test_spear_button(self, pos: tuple[int, int]) -> bool:
        return self._spear_btn_rect.collidepoint(pos)
