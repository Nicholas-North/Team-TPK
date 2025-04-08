from enum import Enum
from typing import List, Tuple


# Enumeration for action types
class ActionType(Enum):
    Movement = 1
    Action = 2
    BonusAction = 3


# Class for template slots
class TemplateSlot:
    def __init__(self, name: str, range: str):
        self.name = name
        self.range = range


# Class representing a single template
class Template:
    def __init__(self, name: str, action_type: ActionType):
        self.name = name
        self.type = action_type
        self.slots = []

    def add_slot(self, name: str, range: str):
        self.slots.append(TemplateSlot(name, range))

    def print_template(self):
        print(f"- {self.name}")
        if self.slots:
            print("  Slots: { ", end="")
            for i, slot in enumerate(self.slots):
                print(f"{slot.name}{slot.range}", end="")
                if i < len(self.slots) - 1:
                    print(", ", end="")
            print(" }")


# Function to initialize default templates
def initialize_templates() -> List[Template]:
    templates = []

    # Movement Templates
    move_towards_enemy = Template("Move Towards Nearest Enemy", ActionType.Movement)
    move_towards_enemy.add_slot("Enemy Within Movement", "[0,1]")
    move_towards_enemy.add_slot("Current Health", "[0.0-1.0]")
    move_towards_enemy.add_slot("Num Allies Unconsious", "[0.0-1.0]")
    move_towards_enemy.add_slot("Num Allies Retreated", "[0.0-1.0]")
    templates.append(move_towards_enemy)

    move_towards_ally = Template("Move Towards Nearest Ally", ActionType.Movement)
    move_towards_ally.add_slot("Ally Within Movement", "[0,1]")
    move_towards_ally.add_slot("Current Health", "[0.0-1.0]")
    move_towards_ally.add_slot("Num Allies Unconsious", "[0.0-1.0]")
    move_towards_ally.add_slot("Num Allies Retreated", "[0.0-1.0]")
    templates.append(move_towards_ally)

    move_away_from_enemy = Template("Move Away From Enemy", ActionType.Movement)
    move_away_from_enemy.add_slot("Within Enemy Reach", "[0,1]")
    move_away_from_enemy.add_slot("Current Health", "[0.0-1.0]")
    move_away_from_enemy.add_slot("Num Allies Unconsious", "[0.0-1.0]")
    move_away_from_enemy.add_slot("Num Allies Retreated", "[0.0-1.0]")
    move_away_from_enemy.add_slot("Avg. Monster Condition", "[0.0-1.0]")
    templates.append(move_away_from_enemy)

    # Action Templates
    melee_attack = Template("Melee Weapon Attack", ActionType.Action)
    melee_attack.add_slot("Enemy Within Movement", "[0,1]")
    melee_attack.add_slot("Melee Attack Exists", "[0,1]")
    melee_attack.add_slot("Multi-Attack", "[0,1]")
    templates.append(melee_attack)

    ranged_attack = Template("Ranged Weapon Attack", ActionType.Action)
    ranged_attack.add_slot("Ranged Attack Exists", "[0,1]")
    ranged_attack.add_slot("Enemy Within Range", "[0,1]")
    ranged_attack.add_slot("Multi-Attack", "[0,1]")
    templates.append(ranged_attack)

    self_heal = Template("Self Target Heal", ActionType.Action)
    self_heal.add_slot("Available Self Target Heal", "[0,1]")
    self_heal.add_slot("Current Health", "[0.0-1.0]")
    templates.append(self_heal)

    # Bonus Action Templates
    ba_self_heal = Template("Self Target Heal (BA)", ActionType.BonusAction)
    ba_self_heal.add_slot("Available BA Self Target Heal", "[0,1]")
    ba_self_heal.add_slot("Current Health", "[0.0-1.0]")
    templates.append(ba_self_heal)

    ba_dash = Template("Dash (BA)", ActionType.BonusAction)
    ba_dash.add_slot("Available BA movement", "[0,1]")
    ba_dash.add_slot("Enemy Within Double Movement", "[0,1]")
    ba_dash.add_slot("Enemy Within Movement", "[0,1]")
    templates.append(ba_dash)

    return templates


# Uncomment below to print templates
# templates = initialize_templates()
# for t in templates:
#     t.print_template()
#     print()
