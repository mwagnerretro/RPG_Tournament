# part8_bracket.py

import os
import random
import pandas as pd
from IPython.display import display, clear_output
import ipywidgets as widgets

from part2_load_fighters import load_fighters
from part4_battle import simulate_battle, save_results
from part3_setup import save_moves

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.csv")


# LOAD FIGHTERS
fighters = load_fighters()
fighter_names = [f.name for f in fighters]
fighter_by_name = {f.name: f for f in fighters}


# OUTPUT AREA
part8_out = widgets.Output(
    layout={"border": "1px solid #ccc", "padding": "6px"}
)


# HELPERS

def get_next_battle_id():
    if os.path.exists(RESULTS_PATH):
        try:
            df = pd.read_csv(RESULTS_PATH)
            if len(df) > 0:
                return df["battle_id"].max() + 1
        except:
            pass
    return 1


# RUN ONE MATCH

def run_match(f1, f2, fights_per_match, battle_id):
    wins = {f1: 0, f2: 0}

    for _ in range(fights_per_match):
        moves, turns = simulate_battle(
            fighter_by_name[f1],
            fighter_by_name[f2],
            battle_id
        )
        save_moves(moves)

        df = pd.DataFrame(moves)
        kos = df[df["defender_health_after"] == 0]

        if len(kos) == 0:
            battle_id += 1
            continue

        ko = kos.iloc[-1]
        winner = ko["attacker"]
        loser = ko["defender"]

        wins[winner] += 1

        save_results({
            "battle_id": battle_id,
            "fighter1": f1,
            "fighter2": f2,
            "winner": winner,
            "loser": loser,
            "turns": turns
        })

        battle_id += 1

    match_winner = max(wins, key=wins.get)
    return match_winner, wins, battle_id


# RUN FULL BRACKET

def run_bracket(fighter_list, fights_per_match):
    battle_id = get_next_battle_id()
    round_num = 1
    fighters = fighter_list[:]

    while len(fighters) > 1:
        print(f"\nROUND {round_num}")
        next_round = []

        for i in range(0, len(fighters), 2):

            # Bye if odd number
            if i + 1 >= len(fighters):
                print(f"{fighters[i]} advances with a BYE")
                next_round.append(fighters[i])
                continue

            f1 = fighters[i]
            f2 = fighters[i + 1]

            winner, wins, battle_id = run_match(
                f1, f2, fights_per_match, battle_id
            )

            print(f"{f1} vs {f2} → {winner} wins ({wins[f1]}–{wins[f2]})")
            next_round.append(winner)

        fighters = next_round
        round_num += 1

    return fighters[0]


# CLICK-TO-SELECT FIGHTERS

selected_fighters = []
fighter_buttons = {}

def toggle_fighter(name):
    btn = fighter_buttons[name]

    if name in selected_fighters:
        selected_fighters.remove(name)
        btn.button_style = ""
    else:
        selected_fighters.append(name)
        btn.button_style = "info"


fighters_grid = widgets.GridBox(
    children=[
        widgets.ToggleButton(
            description=name,
            layout=widgets.Layout(width="150px")
        )
        for name in fighter_names
    ],
    layout=widgets.Layout(
        grid_template_columns="repeat(4, 160px)"
    )
)

for btn in fighters_grid.children:
    fighter_buttons[btn.description] = btn
    btn.observe(
        lambda c, n=btn.description: toggle_fighter(n),
        names="value"
    )


# CONTROLS

fights_per_match_box = widgets.IntText(
    value=5,
    min=1,
    description="Fights per match:",
    style={"description_width": "160px"}
)

start_btn = widgets.Button(
    description="Start Bracket",
    button_style="success"
)

clear_btn = widgets.Button(
    description="Clear Selection",
    button_style="warning"
)


# CALLBACKS

def on_clear(b):
    selected_fighters.clear()
    for btn in fighter_buttons.values():
        btn.value = False
        btn.button_style = ""


def on_start(b):
    with part8_out:
        clear_output(wait=True)

        if len(selected_fighters) < 2:
            print("Select at least two fighters.")
            return

        print("STARTING BRACKET TOURNAMENT")
        print("Fighter order:")
        for i, f in enumerate(selected_fighters, 1):
            print(f"{i}. {f}")

        champion = run_bracket(
            selected_fighters,
            fights_per_match_box.value
        )

        print("\nTOURNAMENT CHAMPION:", champion)


start_btn.on_click(on_start)
clear_btn.on_click(on_clear)


# FINAL LAYOUT

display(
    widgets.VBox([
        widgets.HTML(
            "<h3>Part 8 — Bracket Tournament</h3>"
            "<p>Fighters advance in the order you select them.</p>"
        ),
        fighters_grid,
        fights_per_match_box,
        widgets.HBox([start_btn, clear_btn]),
        part8_out
    ])
)
