# part6_ai_predict.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from sklearn.ensemble import RandomForestClassifier
from IPython.display import clear_output
import ipywidgets as widgets

plt.rcParams["figure.figsize"] = (10, 5)

# Paths
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

MOVES_PATH = os.path.join(SCRIPT_DIR, "battle_moves.csv")

# Output area

out6 = widgets.Output(layout={"border": "1px solid #ccc", "padding": "6px"})


# LOAD + PREPARE MODEL

def load_and_prepare():
    if not os.path.exists(MOVES_PATH):
        raise FileNotFoundError("battle_moves.csv missing — run battles first.")

    df = pd.read_csv(MOVES_PATH)

    kos = df[df["defender_health_after"] == 0]
    winners = kos.groupby("battle_id")["attacker"].first().rename("winner")

    agg = df.groupby(["battle_id", "attacker"]).agg(
        total_damage=("damage_dealt", "sum"),
        total_hits=("hit", "sum"),
        moves_used=("turn", "count"),
        crits=("critical", "sum"),
        avg_damage=("damage_dealt", "mean"),
        opp_hp_left=("defender_health_after", "last")
    ).reset_index()

    agg["crit_rate"] = agg["crits"] / agg["total_hits"].replace(0, 1)
    agg = agg.merge(winners, on="battle_id", how="left")
    agg["win"] = (agg["attacker"] == agg["winner"]).astype(int)

    rows = []
    for _, g in agg.groupby("battle_id"):
        if len(g) < 2:
            continue

        g = g.sort_values("moves_used", ascending=False).head(2)
        a, b = g.iloc[0], g.iloc[1]

        def make_row(A, B):
            return {
                "fighterA": A["attacker"],
                "fighterB": B["attacker"],
                "DMG": A["total_damage"] - B["total_damage"],
                "CRIT": A["crit_rate"] - B["crit_rate"],
                "AVG": A["avg_damage"] - B["avg_damage"],
                "MOVES": A["moves_used"] - B["moves_used"],
                "OPP_HP_LEFT": A["opp_hp_left"] - B["opp_hp_left"],
                "win": A["win"]
            }

        rows.append(make_row(a, b))
        rows.append(make_row(b, a))

    rel = pd.DataFrame(rows)
    if rel.empty:
        raise ValueError("Not enough usable battle data to train the AI.")

    FEATURES = ["DMG", "CRIT", "AVG", "MOVES", "OPP_HP_LEFT"]

    X = rel[FEATURES]
    y = rel["win"]

    model = RandomForestClassifier(n_estimators=300, random_state=60)
    model.fit(X, y)

    fighters = sorted(rel["fighterA"].unique())
    return rel, model, FEATURES, fighters

rel, model, FEATURES, fighters = load_and_prepare()


# PREDICTION
def predict_pair(f1, f2):
    f1_rows = rel[rel["fighterA"] == f1]
    f2_rows = rel[rel["fighterA"] == f2]

    if len(f1_rows) < 5:
        print(f"[X] Limited data for {f1} ({len(f1_rows)} samples)")
    if len(f2_rows) < 5:
        print(f"[X] Limited data for {f2} ({len(f2_rows)} samples)")

    f1s = f1_rows[FEATURES].mean().fillna(0)
    f2s = f2_rows[FEATURES].mean().fillna(0)

    row = (f1s - f2s).to_frame().T
    prob = float(model.predict_proba(row)[0, 1])
    return prob, f1s, f2s


# WIN PROBABILITY BAR

def plot_win_probability_bar(f1, f2, prob):
    fig, ax = plt.subplots(figsize=(8, 2.6))

    ax.set_title("Predicted Win Probability", fontweight="bold", pad=22)

    ax.barh([0], 1.0, height=0.35, color="#eeeeee")
    ax.barh([0], prob, height=0.35, color="#4aa4ff")
    ax.barh([0], 1 - prob, left=prob, height=0.35, color="#ff9f43")

    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("AI Confidence")

    outline = [pe.withStroke(linewidth=3, foreground="black")]

    ax.text(
        0.02, 1.25,
        f"{f1}: {prob:.1%}",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#4aa4ff",
        path_effects=outline
    )

    ax.text(
        0.98, 1.25,
        f"{f2}: {(1 - prob):.1%}",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#ff9f43",
        path_effects=outline
    )

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    plt.show()



# RADAR COMPARISON
feature_labels = {
    "DMG": "Damage Output",
    "CRIT": "Crit Rate",
    "AVG": "Avg Damage",
    "MOVES": "Moves Used",
    "OPP_HP_LEFT": "Opponent HP Left"
}

def plot_radar(f1, f2, f1s, f2s):
    labels = [feature_labels[f] for f in FEATURES]
    N = len(FEATURES)

    v1, v2 = f1s.values, f2s.values
    m = max(np.abs(np.concatenate([v1, v2])).max(), 1)
    v1, v2 = v1 / m, v2 / m

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
    angles = np.append(angles, angles[0])
    v1 = np.append(v1, v1[0])
    v2 = np.append(v2, v2[0])

    ax = plt.subplot(111, polar=True)

    ax.plot(angles, v1, linewidth=2, label=f1)
    ax.fill(angles, v1, alpha=0.3)

    ax.plot(angles, v2, linewidth=2, label=f2)
    ax.fill(angles, v2, alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels([])
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    ax.set_title("Relative Fighter Comparison", pad=20, fontweight="bold")

    plt.show()

# UI

fighter1_dd = widgets.Dropdown(options=fighters, description="Fighter 1:")
fighter2_dd = widgets.Dropdown(options=fighters, description="Fighter 2:")
predict_btn = widgets.Button(description="Predict", button_style="success")

def on_predict(b):
    with out6:
        clear_output(wait=True)

        f1, f2 = fighter1_dd.value, fighter2_dd.value
        if f1 == f2:
            print("Pick two different fighters.")
            return

        prob, f1s, f2s = predict_pair(f1, f2)

        print("AI PREDICTION")
        print(f"{f1} WINS WITH {prob:.2f} PROBABILITY")

        if prob > 0.65:
            print("Strong advantage")
        elif prob > 0.55:
            print("Slight advantage")
        else:
            print("Very close match")

        plot_win_probability_bar(f1, f2, prob)
        plot_radar(f1, f2, f1s, f2s)

predict_btn.on_click(on_predict)

display(widgets.VBox([
    widgets.HTML("<h3><b>Part 6 — AI Fight Outcome Predictor</b></h3>"),
    widgets.HBox([fighter1_dd, fighter2_dd, predict_btn]),
    out6
]))
