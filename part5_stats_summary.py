# part5_stats_summary.py

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

plt.rcParams["figure.figsize"] = (10, 5)

SCRIPT_DIR = os.getcwd()
MOVES_PATH = os.path.join(SCRIPT_DIR, "battle_moves.csv")
RESULTS_PATH = os.path.join(SCRIPT_DIR, "results.csv")

# LOAD DATA

if not os.path.exists(MOVES_PATH):
    raise FileNotFoundError("battle_moves.csv not found. Run some battles first!")

df_moves = pd.read_csv(MOVES_PATH)
df_results = pd.read_csv(RESULTS_PATH) if os.path.exists(RESULTS_PATH) else None

print("Loaded move and result logs.")

# 1. FIGHTER PARTICIPATION

print("\n----- 1. Fighter Participation Summary -----")

df_part = (
    df_moves
    .groupby("attacker")
    .size()
    .reset_index(name="Total Moves")
    .rename(columns={"attacker": "Fighter"})
    .sort_values("Total Moves", ascending=False)
)

display(df_part)

plt.bar(df_part["Fighter"], df_part["Total Moves"])
plt.title("Total Moves Recorded Per Fighter")
plt.ylabel("Moves")
plt.xticks(rotation=45)
plt.show()

# 2. WIN / LOSS PERFORMANCE

print("\n----- 2. Win / Loss Summary -----")

wins = df_results["winner"].value_counts()
losses = df_results["loser"].value_counts()

fighters = sorted(set(wins.index).union(losses.index))
rows = []

for f in fighters:
    w = wins.get(f, 0)
    l = losses.get(f, 0)
    total = w + l
    winrate = w / total if total > 0 else 0
    rows.append([f, w, l, total, winrate])

df_win = pd.DataFrame(
    rows,
    columns=["Fighter", "Wins", "Losses", "Total Fights", "Win Rate"]
)

df_win["Win Rate %"] = (df_win["Win Rate"] * 100).round(1)
df_win = df_win.sort_values("Win Rate", ascending=False)

display(df_win)

plt.bar(df_win["Fighter"], df_win["Win Rate %"])
plt.axhline(50, linestyle="--", color="black", label="Perfect Balance (50%)")
plt.ylabel("Win Rate (%)")
plt.title("Win Rate Per Fighter")
plt.xticks(rotation=45)
plt.legend()
plt.show()

# 3. BALANCE SCORE

print("\n----- 3. Balance Score -----")

df_win["Balance Score"] = abs(df_win["Win Rate"] - 0.5).round(2)

display(df_win[["Fighter", "Win Rate %", "Balance Score", "Total Fights"]])

plt.bar(df_win["Fighter"], df_win["Balance Score"])
plt.axhline(0.25, linestyle="--", color="red", label="High Imbalance")
plt.title("Balance Score (Lower = More Fair)")
plt.ylabel("Distance from 50%")
plt.xticks(rotation=45)
plt.legend()
plt.show()

# 4. WIN RATE VS PARTICIPATION

print("\n----- 4. Win Rate vs Participation -----")

df_compare = df_win.merge(df_part, on="Fighter", how="left")

x = np.arange(len(df_compare))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 5))

ax1.bar(
    x - width / 2,
    df_compare["Total Moves"],
    width,
    color="#4c72b0"
)
ax1.set_ylabel("Total Moves")

ax2 = ax1.twinx()
ax2.bar(
    x + width / 2,
    df_compare["Win Rate %"],
    width,
    color="#dd8452"
)
ax2.set_ylabel("Win Rate (%)")
ax2.axhline(50, linestyle="--", color="black", alpha=0.4)

ax1.set_xticks(x)
ax1.set_xticklabels(df_compare["Fighter"], rotation=45)

legend_handles = [
    Patch(facecolor="#4c72b0", label="Total Moves"),
    Patch(facecolor="#dd8452", label="Win Rate (%)")
]

ax1.legend(
    handles=legend_handles,
    loc="upper center",
    ncol=2,
    frameon=False
)

plt.title("Win Rate vs Participation")
plt.tight_layout()
plt.show()

# 5. RADAR CHART

print("\n----- 5. Radar Chart (Fighter Comparison) -----")

metrics = ["Win Rate", "Total Fights", "Balance Score"]

radar_df = df_win[["Fighter"] + metrics].copy()

for m in metrics:
    radar_df[m] = radar_df[m] / radar_df[m].max()

angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
angles += angles[:1]

plt.figure(figsize=(6, 6))
ax = plt.subplot(111, polar=True)

for _, row in radar_df.iterrows():
    values = row[metrics].tolist()
    values += values[:1]
    ax.plot(angles, values, label=row["Fighter"])
    ax.fill(angles, values, alpha=0.12)

ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
plt.title("Relative Fighter Comparison (Radar)")
plt.legend(bbox_to_anchor=(1.25, 1.1))
plt.show()

# 6. WIN RATE OVER TIME

print("\n----- 6. Win Rate Over Time -----")

plt.figure(figsize=(10, 5))

for fighter in df_results["winner"].unique():

    fights = df_results[
        (df_results["winner"] == fighter) |
        (df_results["loser"] == fighter)
    ].copy()

    fights["Win"] = (fights["winner"] == fighter).astype(int)

    fights["Win Rate %"] = (
        fights["Win"].cumsum() / np.arange(1, len(fights) + 1)
    ) * 100

    plt.plot(
        range(1, len(fights) + 1),
        fights["Win Rate %"],
        label=fighter
    )

plt.xlabel("Fight Number (For That Fighter)")
plt.ylabel("Win Rate (%)")
plt.title("Win Rate Over Time")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()

# 7. BALANCING TIPS

print("\n----- 7. Balancing Tips -----\n")

for _, row in df_win.iterrows():
    name = row["Fighter"]
    winrate = row["Win Rate %"]
    fights = row["Total Fights"]

    if fights < 5:
        print(f"[!] {name}: Too few battles to get balance.")
    elif winrate > 65:
        print(f"[X] {name}: Likely overpowered.")
    elif winrate < 35:
        print(f"[X] {name}: Likely underpowered.")
    else:
        print(f"[O] {name}: Appears balanced.")
