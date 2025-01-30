import random
from enum import Enum
from typing import List, Tuple


class ActionType(Enum):
    Movement = 1
    Action = 2
    BonusAction = 3

class TemplateSlot:
    def __init__(self, name: str, range: str):
        self.name = name
        self.range = range

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

    ba_disengage = Template("Disengage (BA)", ActionType.BonusAction)
    ba_disengage.add_slot("Available BA disengage", "[0,1]")
    templates.append(ba_disengage)

    return templates

# Player class definition
class Player:
    def __init__(self, name="", player_class="", hit_points=0, hit_point_max = 0, armor_class=0, movement_speed=0, level=1, strength_score=10, dexterity_score=10, constitution_score=10, intelligence_score=10, wisdom_score=10, charisma_score=10, multi_attack=0, can_heal=0, num_heals=0):
        self.name = player_class  # Set the name to the class by default
        self.player_class = player_class
        self.hit_points = hit_points
        self.hit_point_max = hit_point_max
        self.armor_class = armor_class
        self.movement_speed = movement_speed
        self.level = level
        self.strength_score = strength_score
        self.dexterity_score = dexterity_score
        self.constitution_score = constitution_score
        self.intelligence_score = intelligence_score
        self.wisdom_score = wisdom_score
        self.charisma_score = charisma_score
        self.multi_attack = multi_attack 
        self.can_heal = can_heal
        self.num_heals = num_heals  
        self.melee_attack_dict = {
            "Melee Attack": (1, 6)  # Example melee attack with 1d6 damage
        }
        
        self.templates = []  # List of templates the player can use

    def add_template(self, template: Template):
        self.templates.append(template)

# Combat Simulation class definition
class Classes:
    def __init__(self):
        
        self.templates = initialize_templates()

        
        self.players = [Player(), Player(), Player(), Player(), Player()]
        
        
        
        self.players[0].name = "Fighter"
        self.players[0].player_class = "Fighter"
        self.players[0].hit_points = 18
        self.players[0].hit_point_max = 18
        self.players[0].armor_class = 15
        self.players[0].movement_speed = 6
        self.players[0].level = 1
        self.players[0].strength_score = 16
        self.players[0].dexterity_score = 12
        self.players[0].constitution_score = 14
        self.players[0].intelligence_score = 10
        self.players[0].wisdom_score = 8
        self.players[0].charisma_score = 10
        self.players[0].multi_attack = 0
        self.players[0].can_heal = 0
        
        
        
        self.players[1].name = "Wizard"
        self.players[1].player_class = "Wizard"
        self.players[1].hit_points = 10
        self.players[1].hit_point_max = 10
        self.players[1].armor_class = 12
        self.players[1].movement_speed = 5
        self.players[1].level = 1
        self.players[1].strength_score = 8
        self.players[1].dexterity_score = 14
        self.players[1].constitution_score = 10
        self.players[1].intelligence_score = 16
        self.players[1].wisdom_score = 12
        self.players[1].charisma_score = 10
        self.players[1].can_heal = 0
        
        
        
        
        self.players[2].name = "Cleric"
        self.players[2].player_class = "Cleric"
        self.players[2].hit_points = 14
        self.players[2].hit_point_max = 14
        self.players[2].armor_class = 12
        self.players[2].movement_speed = 5
        self.players[2].level = 1
        self.players[2].strength_score = 12
        self.players[2].dexterity_score = 10
        self.players[2].constitution_score = 10
        self.players[2].intelligence_score = 12
        self.players[2].wisdom_score = 12
        self.players[2].charisma_score = 16
        self.players[2].can_heal = 1
        self.players[2].num_heals = 2
        
        self.players[3].name = "Rogue"
        self.players[3].player_class = "Rogue"
        self.players[3].hit_points = 12
        self.players[3].hit_point_max = 12
        self.players[3].armor_class = 12
        self.players[3].movement_speed = 5
        self.players[3].level = 1
        self.players[3].strength_score = 10
        self.players[3].dexterity_score = 16
        self.players[3].constitution_score = 10
        self.players[3].intelligence_score = 12
        self.players[3].wisdom_score = 12
        self.players[3].charisma_score = 10
        self.players[3].can_heal = 0
        
        self.players[4].name = "Zombie"
        self.players[4].player_class = "Zombie"
        self.players[4].hit_points = 22
        self.players[4].hit_point_max = 22
        self.players[4].armor_class = 8
        self.players[4].movement_speed = 4
        self.players[4].level = 1
        self.players[4].strength_score = 12
        self.players[4].dexterity_score = 6
        self.players[4].constitution_score = 16
        self.players[4].intelligence_score = 2
        self.players[4].wisdom_score = 6
        self.players[4].charisma_score = 4
        self.players[4].can_heal = 0
        
def create_classes():
    players = []

    # Player 1 - Fighter
    players.append(Player("Fighter", "Fighter", 18, 18, 15, 6, 1, 16, 12, 14, 10, 8, 10, 0, 0, 0))

    # Player 2 - Wizard
    players.append(Player("Wizard", "Wizard", 10, 10, 12, 5, 1, 8, 14, 10, 16, 12, 10, 0, 0, 0))

    # Player 3 - Cleric
    players.append(Player("Cleric", "Cleric", 14, 14, 12, 5, 1, 12, 10, 10, 12, 12, 16, 0, 1, 2))

    # Player 4 - Rogue
    players.append(Player("Rogue", "Rogue", 12, 12, 12, 5, 1, 10, 16, 10, 12, 12, 10, 0, 0, 0))

    # Player 5 - Zombie
    players.append(Player("Zombie", "Zombie", 880, 880, 8, 4, 1, 12, 6, 16, 2, 6, 4, 0, 0, 0))

    return players