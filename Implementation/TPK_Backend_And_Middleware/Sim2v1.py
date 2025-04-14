import random
from enum import Enum
from typing import List, Tuple
from Classes import create_classes

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
import random

class CombatSimulation:
    def __init__(self):
        self.templates = initialize_templates()
        self.players = create_classes()

        if not isinstance(self.players, list):
            raise TypeError("create_classes() did not return a list of players.")
        
        self.selected_players = self.select_players(self.players)
        
        # Debug print statement
        print(f"Selected players: {len(self.selected_players)} players")

        # Check if the list has exactly 3 players
        if len(self.selected_players) != 3:
            print("Error: The selected players list does not have exactly 3 players.")
            return
        
        self.team_players = self.selected_players[:2]  # The two team members
        self.solo_player = self.selected_players[2]   # The solo player

        # Assign individual team players
        self.p1, self.p2 = self.team_players

        # Give players some templates
        self.players[0].add_template(self.templates[7])  # Dash (BA)
        self.players[0].add_template(self.templates[3])  # Melee Weapon Attack
        self.players[1].add_template(self.templates[7])  # Dash (BA)
        self.players[1].add_template(self.templates[8])  # Dash (change to disengage later) (BA)
        self.players[1].add_template(self.templates[4])  # Ranged Weapon Attack
        
        
    def select_players(self, all_players):
        """Allow the user to select two players from the available options, with one solo player."""
        print("Available Players:")
        for i, player in enumerate(all_players):
            print(f"{i + 1}: {player.name} ({player.player_class})")

        while True:
            try:
                team_indices = input("Select two players for the team (enter two numbers separated by a comma): ").split(',')
                team_indices = [int(i.strip()) - 1 for i in team_indices]  # Convert to zero-index

                if len(team_indices) != 2 or len(set(team_indices)) != 2:
                    print("You must select two different players!")
                    continue

                solo_index = int(input("Select one solo player (enter a number): ")) - 1

                # Ensure no overlap between team and solo player
                if solo_index in team_indices:
                    print("Solo player cannot be part of the team!")
                    continue

                if all(0 <= i < len(all_players) for i in team_indices + [solo_index]):
                    self.team_players = [all_players[i] for i in team_indices]  # Team players list
                    self.solo_player = all_players[solo_index]  # Solo player
                    return self.team_players  # Return only team players list (self.solo_player will be used directly)

                else:
                    print("Invalid selection, please choose valid player numbers.")
            except ValueError:
                print("Invalid input. Please enter numbers only.")

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
        heal_amount = self.roll_dice(1,8) + player.charisma_score 
        player.hit_points += heal_amount
        player.num_heals = player.num_heals - 1
        print(f"{player.name} heals for {heal_amount} HP! New HP: {player.hit_points}")            

    # Function to roll a number of dice
    def roll_dice(self, num_dice, die_size):
        return sum(random.randint(1, die_size) for _ in range(num_dice))

    def run_round(self):
        print(f"\n=== COMBAT START: Team vs {self.solo_player.name} ===")
    
        # Loop until the solo player has 0 or less health
        while self.solo_player.hit_points > 0:
            # Simulate both team players' actions against the solo player
            for player in self.team_players:
                self.perform_actions(player, self.solo_player)
                self.perform_Bactions(player, self.solo_player)
                if self.solo_player.hit_points <= 0:
                    print(f"{self.solo_player.name} has been defeated!")
                    break

            if self.solo_player.hit_points <= 0:
                break

            # Solo player retaliates
            self.perform_actions(self.solo_player, self.team_players[0])
            self.perform_Bactions(self.solo_player, self.team_players[0])

            if self.team_players[0].hit_points <= 0 and self.team_players[1].hit_points <= 0:
                print("Both team members have been defeated!")
                break

    def perform_actions(self, player, opponent):
        print(f"\n{player.name}'s turn:")

    # Check if the opponent is still alive
        if opponent.hit_points <= 0:
            print(f"{opponent.name} is already defeated!")
        
        # Choose a new target if the opponent is dead
            if player == self.solo_player:
            # If the solo player is attacking and the current team player is dead, switch target
                new_target = self.team_players[0] if self.team_players[1].hit_points <= 0 else self.team_players[1]
                print(f"{player.name} will now attack {new_target.name}.")
                opponent = new_target
            else:
            # If team players are attacking and the solo player is dead, skip attack
                print(f"{player.name} has no valid opponent to attack.")
                return  # Skip the attack if no valid opponent

        action_choices = ["melee_attack", "heal_self"]
        action = random.choice(action_choices)

        if action == "melee_attack":
            melee_attack_template = self.templates[3]
            print(f"{player.name} chooses action: {melee_attack_template.name}")
            melee_attack_template.print_template()
            self.resolve_attack(player, opponent, "Melee Attack")

        elif action == "heal_self" and player.can_heal == 1 and player.num_heals > 0 and player.hit_points < player.hit_point_max:
            heal_template = self.templates[5]
            print(f"{player.name} chooses to heal!")
            heal_template.print_template()
            self.resolve_heal(player)
            print(f"{player.num_heals} heals left")

        elif action == "heal_self" and (player.can_heal == 0 or player.num_heals < 1 or player.hit_points == player.hit_point_max):
            melee_attack_template = self.templates[3]
            print(f"{player.name} chooses action: {melee_attack_template.name}")
            melee_attack_template.print_template()
            self.resolve_attack(player, opponent, "Melee Attack")

            if player.multi_attack == 1:
                print(f"{player.name} performs a second attack!")
                self.resolve_attack(player, opponent, "Melee Attack")

    def perform_Bactions(self, player, opponent):
        # Randomly select between dodge, heal self, or heal other
        action_choices = ["dodge", "heal_self"]
        action = random.choice(action_choices)

        if action == "dodge":
            print(f"{player.name} chooses to dodge!")

        elif action == "heal_self" and player.can_heal == 1 and player.num_heals > 0 and player.hit_points < player.hit_point_max:
            heal_template = self.templates[5]
            print(f"{player.name} chooses to heal!")
            heal_template.print_template()
            self.resolve_heal(player)
            print(f"{player.num_heals} heals left")

# Run the simulation
simulation = CombatSimulation()
simulation.run_round()

