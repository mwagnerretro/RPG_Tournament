#part2_load_fighters.py
import os
import pandas as pd

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

CSV_PATH = os.path.join(SCRIPT_DIR, "fighters.csv")
SPRITE_DIR = os.path.join(SCRIPT_DIR, "sprites")


# Fighter Class
class Fighter:

    def __init__(self, row: dict):

        self._base_row = row.copy()

        self.name = row.get("name", "Unknown")
        self.cls = row.get("class", "")

        self.health = int(row.get("health", 0))
        self.max_health = self.health
        self.strength = int(row.get("strength", 0))
        self.defense = int(row.get("defense", 0))
        self.speed = int(row.get("speed", 0))
        self.stamina = int(row.get("stamina", 0))
        self.current_stamina = self.stamina

        self.critchance = float(row.get("critchance", 0.0))
        self.critmult = float(row.get("critmult", 1.0))
        self.evasion = float(row.get("evasion", 0.0))

        self.stamina_regen = int(row.get("stamina_regen", 2))
        self.stamina_light = int(row.get("stamina_light", 8))
        self.stamina_heavy = int(row.get("stamina_heavy", 16))

        self.sprite = (row.get("sprite") or "").strip()
        self.sprite_scale = float(row.get("sprite_scale", 1.0))

    # Reset Stats Before A Battle
    def reset_for_battle(self):
        self.health = self.max_health
        self.current_stamina = self.stamina

    # Is Fighter Alive
    def is_alive(self) -> bool:
        return self.health > 0

    # New Fighter on New Battles
    def clone_for_battle(self) -> "Fighter":
        return Fighter(self._base_row)


# Load Fighters From csv:
def load_fighters(csv_path=CSV_PATH):
    rows = pd.read_csv(csv_path).to_dict("records")
    return [Fighter(row) for row in rows]


# Preview from csv.
if __name__ == "__main__":
    fighters = load_fighters()
    print(f"Loaded {len(fighters)} Fighters From {CSV_PATH}\n")

    header = f"{'Idx':>3}  {'Name':12} {'Class':10} {'HP':>4} {'STR':>4} {'DEF':>4} {'SPD':>4} {'EVA':>5} {'STA':>4}"
    print(header)
    print("-" * len(header))

    for i, f in enumerate(fighters, 1):
        print(
            f"{i:3d}. {f.name[:12]:12} {f.cls[:10]:10} "
            f"{f.max_health:4d} {f.strength:4d} {f.defense:4d} {f.speed:4d} "
            f"{f.evasion:5.2f} {f.stamina:4d}"
        )
