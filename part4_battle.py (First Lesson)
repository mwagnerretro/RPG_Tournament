# part4_battle.py

import os
import sys
import time
import pygame
import random
import pandas as pd

from part3_setup import (
    fighters, sprite_cache, select_fighters_ui,
    render_frame, animate_knockback, animate_stamina_change,
    save_moves, HIT_PAUSE_MS, CLOCK, FPS, win, FONT_MED
)
from part2_load_fighters import Fighter

# file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.csv")
MOVES_PATH   = os.path.join(SCRIPT_DIR, "battle_moves.csv")


# draw text with outline
def draw_text_outline(surface, text, font, x, y, color,
                      outline_color=(0, 0, 0), thickness=2):

    for ox in range(-thickness, thickness + 1):
        for oy in range(-thickness, thickness + 1):
            if ox == 0 and oy == 0:
                continue
            outline = font.render(text, True, outline_color)
            surface.blit(outline, (x + ox, y + oy))

    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))


# speed → time until next turn
def time_inc_for_speed(speed):
    return 100.0 / max(1.0, float(speed))


# choose the attack type (light / heavy)
def choose_attack_type(attacker: Fighter):
    cls = attacker.cls
    prob_heavy = 0.25

    if cls in ("Warrior", "Berserker"):
        prob_heavy += 0.15
    if cls == "Rogue":
        prob_heavy -= 0.10

    if random.random() < prob_heavy:
        base = attacker.stamina_heavy
        mult = 1.6
        variance = (-3, 5)
        atk_type = "heavy attack"
    else:
        base = attacker.stamina_light
        mult = 1.0
        variance = (-1, 2)
        atk_type = "light attack"

    cost = max(1, base + random.randint(-2, 2))
    return atk_type, cost, mult, variance


# main logic battle (no animations)
def simulate_battle(f1_base: Fighter, f2_base: Fighter, battle_id):

    # fresh fighter copies
    a = f1_base.clone_for_battle()
    b = f2_base.clone_for_battle()
    a.reset_for_battle()
    b.reset_for_battle()

    # timers
    a_next = 0.0
    b_next = 0.0
    a_inc  = time_inc_for_speed(a.speed)
    b_inc  = time_inc_for_speed(b.speed)

    move_log = []
    turn = 0
    tick = 0

    # loop until someone dies
    while a.health > 0 and b.health > 0 and tick < 3000:
        tick += 1

        # pick attacker based on timers
        if a_next <= b_next:
            attacker, defender = a, b
            cur_time, inc = a_next, a_inc
        else:
            attacker, defender = b, a
            cur_time, inc = b_next, b_inc

        turn += 1

        att_st_before = attacker.current_stamina
        def_hp_before = defender.health

        atk_type, cost, mult, variance = choose_attack_type(attacker)

        # exhaustion checks
        if attacker.current_stamina < cost:

            # tired strike
            if attacker.current_stamina >= 2:
                atk_type = "tired_strike"
                cost = max(1, cost // 2)
                mult = 0.5
                variance = (-1, 1)

            # fully exhausted
            else:
                attacker_after_cost = att_st_before
                attacker.current_stamina = min(attacker.stamina,
                                               attacker_after_cost + attacker.stamina_regen)
                defender.current_stamina = min(defender.stamina,
                                               defender.current_stamina + defender.stamina_regen)

                msg = f"{attacker.name} is exhausted and rests."

                move_log.append({
                    "battle_id": battle_id, "time": cur_time, "turn": turn,
                    "attacker": attacker.name, "defender": defender.name,
                    "attack_type": "skip", "stamina_cost": 0,
                    "attacker_stamina_before": att_st_before,
                    "attacker_stamina_after_cost": attacker_after_cost,
                    "attacker_stamina_after": attacker.current_stamina,
                    "defender_health_before": def_hp_before,
                    "defender_health_after": defender.health,
                    "hit": False, "damage_dealt": 0, "critical": False,
                    "message": msg
                })

                if attacker is a:
                    a_next += a_inc
                else:
                    b_next += b_inc
                continue

        # apply stamina cost
        attacker_after_cost = max(0, att_st_before - cost)

        # evasion
        dodged = random.random() < defender.evasion

        if dodged:
            damage = 0
            crit = False
            def_hp_after = defender.health
            msg = f"{defender.name} dodges {attacker.name}!"

        else:
            base = max(0, attacker.strength - defender.defense + random.randint(*variance))
            crit = random.random() < attacker.critchance
            damage = max(0, int(base * mult * (attacker.critmult if crit else 1.0)))
            def_hp_after = max(0, defender.health - damage)
            defender.health = def_hp_after
            msg = f"{attacker.name} uses {atk_type} on {defender.name} for {damage}{' (CRIT)' if crit else ''}!"

        # regen stamina
        attacker.current_stamina = min(attacker.stamina,
                                       attacker_after_cost + attacker.stamina_regen)
        defender.current_stamina = min(defender.stamina,
                                       defender.current_stamina + defender.stamina_regen)

        # log move
        move_log.append({
            "battle_id": battle_id, "time": cur_time, "turn": turn,
            "attacker": attacker.name, "defender": defender.name,
            "attack_type": atk_type, "stamina_cost": cost,
            "attacker_stamina_before": att_st_before,
            "attacker_stamina_after_cost": attacker_after_cost,
            "attacker_stamina_after": attacker.current_stamina,
            "defender_health_before": def_hp_before,
            "defender_health_after": def_hp_after,
            "hit": not dodged,
            "damage_dealt": damage,
            "critical": crit,
            "message": msg
        })

        # move attacker timer
        if attacker is a:
            a_next += inc
        else:
            b_next += inc

    return move_log, turn


# save results to CSV
def save_results(stats):
    df_new = pd.DataFrame([stats])
    if os.path.exists(RESULTS_PATH):
        df_old = pd.read_csv(RESULTS_PATH)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(RESULTS_PATH, index=False)


# draw button UI
def draw_buttons(buttons):
    for b in buttons:
        pygame.draw.rect(win, b['color'], b['rect'])
        pygame.draw.rect(win, (0, 0, 0), b['rect'], 2)
        txt = FONT_MED.render(b['label'], True, (0, 0, 0))
        win.blit(txt, (b['rect'].x + (b['rect'].w - txt.get_width()) // 2,
                       b['rect'].y + (b['rect'].h - txt.get_height()) // 2))


# wait for button click
def wait_for_choice(buttons):
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "Quit"
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = e.pos
                for b in buttons:
                    if b['rect'].collidepoint(pos):
                        return b['label']
        CLOCK.tick(30)

# The code will not work if you run it without the rest of the code from Part4_battle.py (Main Loop) lesson.
