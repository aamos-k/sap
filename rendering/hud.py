from __future__ import annotations
import pygame
from entities.limb import LimbId, LIMB_LABELS, LIMB_KEYS
from game.turn_manager import TurnManager, TurnState

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


LIMB_ORDER = [LimbId.LEFT_ARM, LimbId.RIGHT_ARM, LimbId.LEFT_LEG, LimbId.RIGHT_LEG]


class HUD:
    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        pygame.font.init()
        self.font_large = pygame.font.SysFont("monospace", FONT_SIZE_LARGE, bold=True)
        self.font_small = pygame.font.SysFont("monospace", FONT_SIZE_SMALL)

        # Pre-compute button rects (bottom-left)
        self.btn_rects: dict[LimbId, pygame.Rect] = {}
        total_w = len(LIMB_ORDER) * BTN_W + (len(LIMB_ORDER) - 1) * BTN_GAP
        start_x = BTN_MARGIN_X
        y = screen_h - BTN_MARGIN_Y - BTN_H
        for i, lid in enumerate(LIMB_ORDER):
            x = start_x + i * (BTN_W + BTN_GAP)
            self.btn_rects[lid] = pygame.Rect(x, y, BTN_W, BTN_H)

    def draw(self, screen: pygame.Surface, tm: TurnManager,
             mouse_pos: tuple[int, int], seed: int = 0) -> None:
        self._draw_turn_label(screen, tm)
        self._draw_limb_buttons(screen, tm, mouse_pos)
        self._draw_instructions(screen, tm)
        self._draw_flash(screen, tm)
        self._draw_seed(screen, seed)
        if tm.state == TurnState.GAME_OVER:
            self._draw_game_over(screen, tm)

    def _draw_turn_label(self, screen: pygame.Surface, tm: TurnManager) -> None:
        if tm.state in (TurnState.PLAYER_SELECT_LIMB, TurnState.PLAYER_SELECT_TARGET,
                        TurnState.PLAYER_RESOLVE):
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

    def _draw_instructions(self, screen: pygame.Surface, tm: TurnManager) -> None:
        if tm.state == TurnState.PLAYER_SELECT_LIMB:
            msg = "Select a limb (buttons or 1-4)  |  ESC = cancel"
        elif tm.state == TurnState.PLAYER_SELECT_TARGET:
            lbl = LIMB_LABELS.get(tm.selected_limb, "?")
            msg = f"Moving {lbl} — click target in cave  |  ESC = cancel"
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
