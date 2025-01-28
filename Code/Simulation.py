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
    def __init__(self, name="", player_class="", hit_points=0, armor_class=0, movement_speed=0, level=1, strength_score=10, dexterity_score=10, constitution_score=10, intelligence_score=10, wisdom_score=10, charisma_score=10, multi_attack=0, can_heal=0, num_heals=0):
        self.name = name
        self.player_class = player_class
        self.hit_points = hit_points
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
class CombatSimulation:
    def __init__(self):
        
        self.templates = initialize_templates()

        
        self.players = [Player(), Player()]
        
        
        self.players[0].name = "Player 1"
        self.players[0].player_class = "Fighter"
        self.players[0].hit_points = 100
        self.players[0].armor_class = 15
        self.players[0].movement_speed = 6
        self.players[0].level = 1
        self.players[0].strength_score = 16
        self.players[0].dexterity_score = 12
        self.players[0].constitution_score = 14
        self.players[0].intelligence_score = 10
        self.players[0].wisdom_score = 8
        self.players[0].charisma_score = 10
        self.players[0].multi_attack = 1
        self.players[0].can_heal = 1
        
        
        
        self.players[1].name = "Player 2"
        self.players[1].player_class = "Wizard"
        self.players[1].hit_points = 25
        self.players[1].armor_class = 12
        self.players[1].movement_speed = 5
        self.players[1].level = 1
        self.players[1].strength_score = 8
        self.players[1].dexterity_score = 14
        self.players[1].constitution_score = 10
        self.players[1].intelligence_score = 16
        self.players[1].wisdom_score = 12
        self.players[1].charisma_score = 10
        self.players[1].charisma_score = 0
        self.players[1].can_heal = 1
        self.players[1].num_heals = 3
        
        # Give players some templates
        self.players[0].add_template(self.templates[7])  # Dash (BA)
        self.players[0].add_template(self.templates[3])  # Melee Weapon Attack
        self.players[1].add_template(self.templates[7])  # Dash (BA)
        self.players[1].add_template(self.templates[8])  # Dash (change to disengage later) (BA)
        self.players[1].add_template(self.templates[4])  # Ranged Weapon Attack

    # Function to simulate a player's attack
    def resolve_attack(self, attacker, defender, attack_type):
        if attack_type in attacker.melee_attack_dict:
            num_dice, die_size = attacker.melee_attack_dict[attack_type]
            # Roll to hit (d20)
            attack_roll = self.roll_dice(1, 20) + 1 + ((attacker.strength_score - 10) / 2) #Prof. and attack bonus
            print(f"{attacker.name} attacks {defender.name} with {attack_type} (Roll: {attack_roll})")

            if attack_roll >= defender.armor_class:
                damage = self.roll_dice(num_dice, die_size) + ((attacker.strength_score - 10) / 2) # Roll damage (1d6)
                defender.hit_points -= damage
                print(f"{defender.name} takes {damage} damage! HP: {defender.hit_points}")
            else:
                print("Attack missed!")
                
    def resolve_heal(self, player):
        heal_amount = 10  
        player.hit_points += heal_amount
        player.num_heals = player.num_heals - 1
        print(f"{player.name} heals for {heal_amount} HP! New HP: {player.hit_points}")            

    # Function to roll a number of dice
    def roll_dice(self, num_dice, die_size):
        return sum(random.randint(1, die_size) for _ in range(num_dice))


    
    def run_round(self):
        print("=== COMBAT START ===")
    
        # Loop until one player has 0 or less health
        while all(player.hit_points > 0 for player in self.players):
            # Simulate player 1's actions
            self.perform_actions(self.players[0], self.players[1])

            # Check if Player 2 is still alive
            if self.players[1].hit_points <= 0:
                print(f"{self.players[1].name} has been defeated!")
                break
        
            
            self.perform_actions(self.players[1], self.players[0])

            # Check if Player 1 is still alive
            if self.players[0].hit_points <= 0:
                print(f"{self.players[0].name} has been defeated!")
                break

    def perform_actions(self, player, opponent):
        print(f"\n{player.name}'s turn:")

        
        dash_template = self.templates[7]  
        print(f" chooses bonus action: {dash_template.name}")
        dash_template.print_template()

        # Move into range 
        print(f"{player.name} moves into range of {opponent.name}")

       
        melee_attack_template = self.templates[3]  
        print(f" chooses action: {melee_attack_template.name}")
        melee_attack_template.print_template()
        self.resolve_attack(player, opponent, "Melee Attack")

        # If multi-attack is enabled, perform an additional attack
        if player.multi_attack == 1:
            print(f"{player.name} performs a second attack!")
            self.resolve_attack(player, opponent, "Melee Attack")

        
        if player.can_heal == 1 & player.num_heals > 0:
            heal_template = self.templates[5]  
            print(f"{player.name} chooses to heal!")
            
            heal_template.print_template()
            self.resolve_heal(player)
        
        
        if opponent.hit_points <= 0:
            return  # Exit the turn if the opponent is defeated

# Run the simulation
simulation = CombatSimulation()
simulation.run_round()
