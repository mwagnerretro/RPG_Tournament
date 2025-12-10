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


# main battle loop
def run_loop():
    battle_id = 1

    while True:
        f1_base, f2_base = select_fighters_ui(fighters)

        # rematch loop
        while True:
            move_log, total_turns = simulate_battle(f1_base, f2_base, battle_id)
            save_moves(move_log)

            # animation clones
            f1_anim = f1_base.clone_for_battle()
            f2_anim = f2_base.clone_for_battle()
            f1_anim.reset_for_battle()
            f2_anim.reset_for_battle()

            render_frame(f1_anim, f2_anim, "Battle start!")
            pygame.time.delay(400)

            # replay each move
            for m in move_log:

                if f1_anim.health <= 0 or f2_anim.health <= 0:
                    break

                msg = m["message"]

                attacker = f1_anim if m["attacker"] == f1_anim.name else f2_anim
                defender = f1_anim if m["defender"] == f1_anim.name else f2_anim

                prev_st   = m["attacker_stamina_before"]
                after_cost = m["attacker_stamina_after_cost"]
                final_st   = m["attacker_stamina_after"]

                hp_before = m["defender_health_before"]
                hp_after  = m["defender_health_after"]

                defender.health = hp_after
                attacker.current_stamina = prev_st

                # stamina cost animation
                if prev_st != after_cost:
                    animate_stamina_change(
                        f1_anim, f2_anim,
                        prev_st, after_cost,
                        left=(attacker is f1_anim),
                        frames=8,
                        message=msg
                    )
                    attacker.current_stamina = after_cost

                # knockback animation
                dmg_to_f1 = max(0, hp_before - hp_after) if defender is f1_anim else 0
                dmg_to_f2 = max(0, hp_before - hp_after) if defender is f2_anim else 0
                animate_knockback(f1_anim, f2_anim, (dmg_to_f1, dmg_to_f2), msg)

                # regen animation
                if final_st != after_cost:
                    animate_stamina_change(
                        f1_anim, f2_anim,
                        after_cost, final_st,
                        left=(attacker is f1_anim),
                        frames=8,
                        message=msg
                    )
                    attacker.current_stamina = final_st

                render_frame(f1_anim, f2_anim, msg)
                pygame.time.delay(HIT_PAUSE_MS)

            # determine winner
            winner = f1_anim.name if f1_anim.health > 0 else f2_anim.name
            loser  = f2_anim.name if winner == f1_anim.name else f1_anim.name

            df = pd.DataFrame(move_log)
            stats = {
                "battle_id": battle_id,
                "fighter1": f1_base.name,
                "fighter2": f2_base.name,
                "winner": winner,
                "loser": loser,
                "winner_hp": max(f1_anim.health, f2_anim.health),
                "turns": total_turns,
                "total_damage_winner": df[df["attacker"] == winner]["damage_dealt"].sum(),
                "total_damage_loser": df[df["attacker"] == loser]["damage_dealt"].sum(),
                "total_misses": df[df["hit"] == False].shape[0],
                "total_dodges": df[df["hit"] == False].shape[0],
                "crits_winner": df[(df["attacker"] == winner) & (df["critical"] == True)].shape[0],
                "crits_loser": df[(df["attacker"] == loser) & (df["critical"] == True)].shape[0],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_results(stats)
            battle_id += 1

            # defeated text
            DEFEAT_FONT = pygame.font.SysFont("Arial", 36, bold=True)
            defeated_surf = DEFEAT_FONT.render("DEFEATED!", True, (255, 0, 0))

            if loser == f1_anim.name:
                sprite = sprite_cache[f1_anim.name]
                x = (win.get_width() // 4) - (sprite.get_width() // 2)
                y = win.get_height() // 2 - sprite.get_height() // 2
            else:
                sprite = sprite_cache[f2_anim.name]
                x = (3 * win.get_width() // 4) - (sprite.get_width() // 2)
                y = win.get_height() // 2 - sprite.get_height() // 2

            draw_text_outline(win, "DEFEATED!", DEFEAT_FONT,
                              x + sprite.get_width() // 2 - defeated_surf.get_width() // 2,
                              y + sprite.get_height() // 2 - defeated_surf.get_height() // 2,
                              (255, 0, 0), (0, 0, 0))
            pygame.display.update()
            pygame.time.delay(800)

            # winner text
            WIN_FONT = pygame.font.SysFont("Arial", 48, bold=True)
            text = f"WINNER: {winner}"
            surf = WIN_FONT.render(text, True, (0, 0, 0))

            draw_text_outline(win, text, WIN_FONT,
                              win.get_width() // 2 - surf.get_width() // 2,
                              win.get_height() - 200,
                              (0, 0, 0), (255, 255, 255))

            pygame.display.update()

            # buttons
            btn_w, btn_h, spacing = 220, 50, 30
            total_w = btn_w * 3 + spacing * 2
            left_x = (win.get_width() - total_w) // 2
            y_btn = win.get_height() - 120

            buttons = [
                {"label": "Refight",
                 "rect": pygame.Rect(left_x, y_btn, btn_w, btn_h),
                 "color": (180, 230, 200)},
                {"label": "New Fighters",
                 "rect": pygame.Rect(left_x + btn_w + spacing, y_btn, btn_w, btn_h),
                 "color": (200, 200, 230)},
                {"label": "Quit",
                 "rect": pygame.Rect(left_x + 2 * (btn_w + spacing), y_btn, btn_w, btn_h),
                 "color": (240, 200, 200)},
            ]

            draw_buttons(buttons)
            pygame.display.update()

            choice = wait_for_choice(buttons)

            if choice == "Refight":
                continue
            elif choice == "New Fighters":
                break
            else:
                pygame.quit()
                sys.exit()


if __name__ == "__main__":
    run_loop()
