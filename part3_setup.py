# part3_setup.py

import os
import sys
import warnings
import pandas as pd
import pygame

from part2_load_fighters import load_fighters, Fighter

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

CSV_PATH = os.path.join(SCRIPT_DIR, "fighters.csv")
SPRITE_DIR = os.path.join(SCRIPT_DIR, "sprites")
MOVES_PATH = os.path.join(SCRIPT_DIR, "battle_moves.csv")

# Pygame window setup
pygame.init()
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 580
win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("RPG Tournament")

CLOCK = pygame.time.Clock()
FPS = 60

# Fonts
FONT_SMALL = pygame.font.SysFont("Arial", 18)
FONT_MED   = pygame.font.SysFont("Arial", 22)
FONT_BIG   = pygame.font.SysFont("Arial", 48)

# Colors
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
RED    = (200, 0, 0)
GREEN  = (0, 200, 0)
BLUE   = (60, 160, 240)
YELLOW = (240, 200, 60)

# UI constants
SIDE_PANEL_ALPHA = 180
MESSAGE_HEIGHT = 70
DEFAULT_SPRITE_SIZE = (120, 120)
HEALTH_BAR_WIDTH = 260
STAMINA_BAR_WIDTH = 220
STAMINA_BAR_Y = 74

# Animation constants
KNOCKBACK_MAX_PIXELS = 160
KNOCKBACK_STEPS = 12
KNOCKBACK_FPS = 60
HIT_PAUSE_MS = 500

# Background surface
BG = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
BG.fill(WHITE)

# Load fighters from CSV (from Part 2)
fighters = load_fighters(CSV_PATH)

# Sprite cache
sprite_cache = {}

# Scale Sprite
def compute_sprite_scale(f: Fighter):
    try:
        mult = float(getattr(f, "sprite_scale", 1.0))
        w, h = DEFAULT_SPRITE_SIZE
        return (max(10, int(w * mult)), max(10, int(h * mult)))
    except Exception:
        return DEFAULT_SPRITE_SIZE

# Load all fighter sprites
def load_sprites():
    sprite_cache.clear()
    for f in fighters:
        filename = f.sprite
        path = os.path.join(SPRITE_DIR, filename) if filename else ""
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, compute_sprite_scale(f))
                sprite_cache[f.name] = img
                continue
            except Exception:
                pass

        fallback = pygame.Surface(compute_sprite_scale(f), pygame.SRCALPHA)
        fallback.fill(RED)
        sprite_cache[f.name] = fallback
        if filename:
            print(f"[WARN] Missing sprite for {f.name}: {filename}")

load_sprites()

# Draw UI bars and labels
def draw_ui(f1: Fighter, f2: Fighter, surface, interp_st_left=None, interp_st_right=None):
    pygame.draw.rect(surface, WHITE, (0, 0, WINDOW_WIDTH, 120))

    surface.blit(FONT_SMALL.render(f"{f1.name} ({int(f1.health)} HP)", True, BLACK),
                (WINDOW_WIDTH // 4 - 140, 6))
    surface.blit(FONT_SMALL.render(f"{f2.name} ({int(f2.health)} HP)", True, BLACK),
                (3 * WINDOW_WIDTH // 4 - 140, 6))

    pygame.draw.rect(surface, RED, (WINDOW_WIDTH // 4 - 130, 35, HEALTH_BAR_WIDTH, 20))
    pygame.draw.rect(surface, GREEN,
        (WINDOW_WIDTH // 4 - 130, 35,
        max(0, HEALTH_BAR_WIDTH * (f1.health / max(1, f1.max_health))), 20))

    pygame.draw.rect(surface, RED, (3 * WINDOW_WIDTH // 4 - 130, 35, HEALTH_BAR_WIDTH, 20))
    pygame.draw.rect(surface, GREEN,
        (3 * WINDOW_WIDTH // 4 - 130, 35,
        max(0, HEALTH_BAR_WIDTH * (f2.health / max(1, f2.max_health))), 20))

    left_st = interp_st_left if interp_st_left is not None else f1.current_stamina
    right_st = interp_st_right if interp_st_right is not None else f2.current_stamina

    st_left_x = WINDOW_WIDTH // 4 - STAMINA_BAR_WIDTH // 2
    st_right_x = 3 * WINDOW_WIDTH // 4 - STAMINA_BAR_WIDTH // 2

    frac1 = max(0, min(1.0, left_st / max(1, f1.stamina)))
    frac2 = max(0, min(1.0, right_st / max(1, f2.stamina)))

    color1 = BLUE if frac1 > 0.5 else (YELLOW if frac1 > 0.2 else RED)
    color2 = BLUE if frac2 > 0.5 else (YELLOW if frac2 > 0.2 else RED)

    pygame.draw.rect(surface, (200, 200, 200), (st_left_x, STAMINA_BAR_Y, STAMINA_BAR_WIDTH, 14))
    pygame.draw.rect(surface, color1, (st_left_x, STAMINA_BAR_Y, int(STAMINA_BAR_WIDTH * frac1), 14))
    surface.blit(FONT_SMALL.render(f"Stamina: {int(left_st)}/{f1.stamina}", True, BLACK),
                 (st_left_x, STAMINA_BAR_Y - 18))

    pygame.draw.rect(surface, (200, 200, 200), (st_right_x, STAMINA_BAR_Y, STAMINA_BAR_WIDTH, 14))
    pygame.draw.rect(surface, color2, (st_right_x, STAMINA_BAR_Y, int(STAMINA_BAR_WIDTH * frac2), 14))
    surface.blit(FONT_SMALL.render(f"Stamina: {int(right_st)}/{f2.stamina}", True, BLACK),
                 (st_right_x, STAMINA_BAR_Y - 18))

# Draw a message box at the bottom
def draw_message(msg, surface):
    rect = pygame.Rect(0, WINDOW_HEIGHT - MESSAGE_HEIGHT, WINDOW_WIDTH, MESSAGE_HEIGHT)
    pygame.draw.rect(surface, WHITE, rect)
    surf = FONT_MED.render(msg, True, BLACK)
    surface.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2,
                        WINDOW_HEIGHT - MESSAGE_HEIGHT + (MESSAGE_HEIGHT - surf.get_height()) // 2))

# Draw fighter stat panel
def draw_side(f: Fighter, left, surface):
    panel_w = 150
    x = 8 if left else WINDOW_WIDTH - panel_w - 8
    y = 130

    panel = pygame.Surface((panel_w, 220), pygame.SRCALPHA)
    panel.fill((240, 240, 240, SIDE_PANEL_ALPHA))
    surface.blit(panel, (x, y))

    stats = [
        f"Class: {f.cls}",
        f"Health: {int(f.max_health)}",
        f"Strength: {int(f.strength)}",
        f"Defense: {int(f.defense)}",
        f"Speed: {int(f.speed)}",
        f"Stamina: {int(f.stamina)}",
        f"Crit %: {f.critchance:.2f}",
        f"Evasion: {f.evasion:.2f}",
    ]

    ty = y + 8
    for line in stats:
        surface.blit(FONT_SMALL.render(line, True, (30, 30, 30)), (x + 8, ty))
        ty += 20

# Render a single animation frame
def render_frame(f1: Fighter, f2: Fighter, message, pos1_offset=(0,0), pos2_offset=(0,0),
                 interp_st_left=None, interp_st_right=None):

    frame = BG.copy()

    surf1 = sprite_cache.get(f1.name)
    surf2 = sprite_cache.get(f2.name)

    pos1 = (WINDOW_WIDTH // 4 - surf1.get_width() // 2 + pos1_offset[0],
            WINDOW_HEIGHT // 2 - surf1.get_height() // 2 + pos1_offset[1])
    pos2 = (3 * WINDOW_WIDTH // 4 - surf2.get_width() // 2 + pos2_offset[0],
            WINDOW_HEIGHT // 2 - surf2.get_height() // 2 + pos2_offset[1])

    frame.blit(surf1, pos1)
    frame.blit(surf2, pos2)

    draw_ui(f1, f2, frame, interp_st_left, interp_st_right)
    draw_side(f1, True, frame)
    draw_side(f2, False, frame)
    draw_message(message, frame)

    win.blit(frame, (0, 0))
    pygame.display.update()

# Animation: knockback
def animate_knockback(f1: Fighter, f2: Fighter, dmg, message):
    dmg1, dmg2 = dmg
    max1 = f1.max_health or 1
    max2 = f2.max_health or 1

    kb1 = int(min(KNOCKBACK_MAX_PIXELS, (dmg1 / max1) * KNOCKBACK_MAX_PIXELS)) if max1 > 0 else 0
    kb2 = int(min(KNOCKBACK_MAX_PIXELS, (dmg2 / max2) * KNOCKBACK_MAX_PIXELS)) if max2 > 0 else 0

    if dmg1 > 0 and kb1 < 12: kb1 = 12
    if dmg2 > 0 and kb2 < 12: kb2 = 12

    for step in range(KNOCKBACK_STEPS):
        t = (step + 1) / KNOCKBACK_STEPS
        off1 = int(-kb1 * t)
        off2 = int(kb2 * t)
        render_frame(f1, f2, message, (off1, 0), (off2, 0))
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        CLOCK.tick(KNOCKBACK_FPS)

    for step in range(KNOCKBACK_STEPS):
        t = 1 - (step + 1) / KNOCKBACK_STEPS
        off1 = int(-kb1 * t)
        off2 = int(kb2 * t)
        render_frame(f1, f2, message, (off1, 0), (off2, 0))
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        CLOCK.tick(KNOCKBACK_FPS)

# Animation: stamina bar change
def animate_stamina_change(f1: Fighter, f2: Fighter, prev, cur, left=True, frames=10, message=""):
    for step in range(frames):
        t = (step + 1) / frames
        v = prev + (cur - prev) * t
        if left:
            render_frame(f1, f2, message, interp_st_left=v)
        else:
            render_frame(f1, f2, message, interp_st_right=v)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        CLOCK.tick(FPS)

# Save battle moves to CSV
def save_moves(move_log, path=MOVES_PATH):
    if not move_log:
        return
    df = pd.DataFrame(move_log)
    if os.path.exists(path):
        try:
            existing = pd.read_csv(path)
            df = pd.concat([existing, df], ignore_index=True)
        except Exception:
            pass
    df.to_csv(path, index=False)

# Character selection UI
def select_fighters_ui(fighters_list):
    CARD_W = 260
    CARD_H = 140
    PADDING = 20

    cols = min(3, len(fighters_list))
    selected = []

    while True:
        win.fill((245, 245, 245))
        mouse = pygame.mouse.get_pos()
        clicked = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                clicked = True

        for idx, f in enumerate(fighters_list):
            col = idx % cols
            row = idx // cols

            x = PADDING + col * (CARD_W + PADDING)
            y = 60 + row * (CARD_H + PADDING)
            rect = pygame.Rect(x, y, CARD_W, CARD_H)

            color = (220, 230, 255) if f.name in selected else (255, 255, 255)
            pygame.draw.rect(win, color, rect)
            pygame.draw.rect(win, (200, 200, 200), rect, 2)

            surf = sprite_cache.get(f.name)
            if surf:
                small = pygame.transform.smoothscale(surf, (80, 80))
                win.blit(small, (x + 10, y + 10))

            win.blit(FONT_MED.render(f"{idx+1}. {f.name}", True, BLACK), (x + 100, y + 10))
            win.blit(FONT_SMALL.render(f"Class: {f.cls}", True, BLACK), (x + 100, y + 40))
            win.blit(FONT_SMALL.render(f"HP: {int(f.max_health)}", True, BLACK), (x + 100, y + 64))

            if clicked and rect.collidepoint(mouse):
                if f.name in selected:
                    selected.remove(f.name)
                else:
                    if len(selected) < 2:
                        selected.append(f.name)
                if len(selected) == 2:
                    f1 = next(ff for ff in fighters_list if ff.name == selected[0])
                    f2 = next(ff for ff in fighters_list if ff.name == selected[1])
                    return f1, f2

        win.blit(
            FONT_MED.render("Click two fighters to select.", True, BLACK),
            (20, 10),
        )

        pygame.display.update()
        CLOCK.tick(30)
