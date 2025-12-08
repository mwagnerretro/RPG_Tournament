# part1_fighters.py
import os
import pandas as pd

# Setup the File Paths
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

CSV_PATH = os.path.join(SCRIPT_DIR, "fighters.csv")
SPRITE_DIR = os.path.join(SCRIPT_DIR, "sprites")
os.makedirs(SPRITE_DIR, exist_ok=True)

# Class Modifiers

CLASS_MODIFIERS = {
    "Tank":      {"health": +10, "strength": 0,  "defense": +3, "speed": -2, "stamina": +10,
                  "evasion": 0.04, "stamina_regen": 2, "stamina_light": 8,  "stamina_heavy": 16},
    "Warrior":   {"health": +5,  "strength": +2, "defense": +1, "speed": 0,  "stamina": +5,
                  "evasion": 0.06, "stamina_regen": 2, "stamina_light": 8,  "stamina_heavy": 16},
    "Mage":      {"health": -5,  "strength": +3, "defense": -2, "speed": +2, "stamina": -5,
                  "evasion": 0.12, "stamina_regen": 3, "stamina_light": 6,  "stamina_heavy": 12},
    "Rogue":     {"health": 0,   "strength": +1, "defense": 0,  "speed": +5, "stamina": 0,
                  "evasion": 0.18, "stamina_regen": 4, "stamina_light": 6,  "stamina_heavy": 12},
    "Archer":    {"health": 0,   "strength": +2, "defense": 0,  "speed": +3, "stamina": 0,
                  "evasion": 0.14, "stamina_regen": 3, "stamina_light": 7,  "stamina_heavy": 14},
    "Berserker": {"health": +10, "strength": +4, "defense": -1, "speed": -1, "stamina": +5,
                  "evasion": 0.05, "stamina_regen": 2, "stamina_light": 10, "stamina_heavy": 18},
}


def apply_class_modifiers(fighter):    
    class_name = fighter.get("class", "")
    modifiers = CLASS_MODIFIERS.get(class_name, {})

    for stat_name, class_value in modifiers.items():
        special_stats = ("evasion", "stamina_regen", "stamina_light", "stamina_heavy")
        if stat_name in special_stats:
            fighter[stat_name] = class_value        
        else:
            base_value = fighter.get(stat_name, 0)
            new_value = base_value + class_value
            fighter[stat_name] = new_value


# Fighters
FIGHTERS = [
    {
        "name":         "Cheetah",
        "class":        "Rogue",
        "health":       100,
        "strength":     25,
        "defense":      10,
        "speed":        20,
        "stamina":      100,
        "critchance":   0.20,
        "critmult":     1.5,
        "sprite":       "cheetah.png",
        "sprite_scale": 1.0,
    },
    {
        "name":         "Retro",
        "class":        "Warrior",
        "health":       120,
        "strength":     20,
        "defense":      15,
        "speed":        10,
        "stamina":      120,
        "critchance":   0.10,
        "critmult":     2.0,
        "sprite":       "retro.png",
        "sprite_scale": 1.0,
    },
    {
        "name":         "Pixel",
        "class":        "Mage",
        "health":       90,
        "strength":     30,
        "defense":      5,
        "speed":        15,
        "stamina":      80,
        "critchance":   0.25,
        "critmult":     1.8,
        "sprite":       "pixel.png",
        "sprite_scale": 1.0,
    },
    {
        "name":         "Nova",
        "class":        "Archer",
        "health":       95,
        "strength":     22,
        "defense":      8,
        "speed":        18,
        "stamina":      90,
        "critchance":   0.15,
        "critmult":     1.6,
        "sprite":       "nova.png",
        "sprite_scale": 1.0,
    },
    {
        "name":         "Blaze",
        "class":        "Berserker",
        "health":       130,
        "strength":     28,
        "defense":      12,
        "speed":        8,
        "stamina":      150,
        "critchance":   0.05,
        "critmult":     2.2,
        "sprite":       "blaze.png",
        "sprite_scale": 1.0,
    },
]

# Build a Fighter List
fighters = [f.copy() for f in FIGHTERS]
for fighter in fighters:
    apply_class_modifiers(fighter)
df = pd.DataFrame(fighters)
df.to_csv(CSV_PATH, index=False)
print(f"Saved {len(fighters)} fighters to {CSV_PATH}")

# Jupyter-Notebook Preview (Optional)
def preview():
    import ipywidgets as widgets
    from IPython.display import display, clear_output

    names = [f["name"] for f in fighters]

    f1 = widgets.Dropdown(options=names, description="Fighter 1:")
    f2 = widgets.Dropdown(options=names, description="Fighter 2:")
    btn = widgets.Button(description="Show", button_style="info")
    out = widgets.Output()

    @out.capture(clear_output=True)
    def show(_):
        if f1.value == f2.value:
            print("Please select two different fighters.")
            return

        f1_data = next(f for f in fighters if f["name"] == f1.value)
        f2_data = next(f for f in fighters if f["name"] == f2.value)

        display(pd.DataFrame([f1_data, f2_data]))
#Main Function
    btn.on_click(show)
    display(widgets.HBox([f1, f2, btn]), out)

if "get_ipython" in globals():
    preview()
