# part7_mass_simulator

import os
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
from IPython.display import display, clear_output
import ipywidgets as widgets

from part2_load_fighters import load_fighters
from part4_battle import simulate_battle, save_results
from part3_setup import save_moves

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

MOVES_PATH = os.path.join(SCRIPT_DIR, "battle_moves.csv")
RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.csv")


#LOAD FIGHTERS
fighters = load_fighters()
fighter_names = sorted(f.name for f in fighters)


fighter_by_name = {f.name: f for f in fighters}


#CLEAR OUTPUT AREA FOR JUPYTER DISPLAY

part7_out = widgets.Output(
    layout={"border": "1px solid #ccc", "padding": "6px"}
)


#HELPER FUNCTIONS
def get_next_battle_id():
    if os.path.exists(RESULTS_PATH):
        try:
            df = pd.read_csv(RESULTS_PATH)
            if len(df) > 0:
                return df["battle_id"].max() + 1
        except:
            pass
    return 1

#RUN MANY BATTLES AUTOMATICALLY
def run_many(f1, f2, n):

    battle_id = get_next_battle_id()
    results = []

    for _ in tqdm(range(n), desc="Simulating battles"):

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

        stats = {
            "battle_id": battle_id,
            "fighter1": f1,
            "fighter2": f2,
            "winner": winner,
            "loser": loser,
            "turns": turns
        }

        save_results(stats)
        results.append(stats)

        battle_id += 1

    if len(results) == 0:
        print("WARNING: No completed battles recorded.")

    return pd.DataFrame(results)


# USER INTERFACE ELEMENTS

fighter1_dd = widgets.Dropdown(
    options=fighter_names,
    description="Fighter 1:"
)

fighter2_dd = widgets.Dropdown(
    options=fighter_names,
    description="Fighter 2:"
)

num_box = widgets.IntText(
    value=50,
    min=1,
    description="# Battles:"
)

simulate_btn = widgets.Button(
    description="Run Simulations",
    button_style="success"
)


#BUTTON CALLBACKS

def on_simulate(b):
    with part7_out:
        clear_output(wait=True)

        f1 = fighter1_dd.value
        f2 = fighter2_dd.value
        n = num_box.value

        if f1 == f2:
            print("Pick two different fighters.")
            return

        print(f"Running {n} simulated battles: {f1} vs {f2}...\n")

        df = run_many(f1, f2, n)

        print("Simulation complete! Sample of recorded results:")
        display(df.head())


        print("Refresh Part 5 to update graphs and Part 6 to retrain the AI model.")


simulate_btn.on_click(on_simulate)


#FINAL LAYOUT

display(
    widgets.VBox([
        widgets.HTML(
            "<h3>Part 7 — Mass Battle Simulator</h3>"
            "<p>Generate large datasets for statistics and AI training.</p>"
        ),
        widgets.HBox([fighter1_dd, fighter2_dd, num_box, simulate_btn]),
        part7_out
    ])
)
