import random
import copy
from enum import Enum
from typing import List
from collections import defaultdict
from Classes import create_classes
from tqdm import tqdm

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

# Function to initialize default templates
def initialize_templates() -> List[Template]:
    templates = []
    melee_attack = Template("Melee Weapon Attack", ActionType.Action)
    melee_attack.add_slot("Enemy Within Movement", "[0,1]")
    templates.append(melee_attack)
    return templates

class Player:
    def __init__(self, name, player_class, hit_points, hit_point_max, armor_class, multi_attack, can_heal, num_heals):
        self.name = name
        self.player_class = player_class
        self.hit_points = hit_points
        self.hit_point_max = hit_point_max
        self.armor_class = armor_class
        self.multi_attack = multi_attack
        self.can_heal = can_heal
        self.num_heals = num_heals
        self.melee_attack_dict = {"Melee Attack": (1, 6)}

class MonteCarloSimulation:
    def __init__(self, num_simulations=10000):
        self.num_simulations = num_simulations
        self.results = defaultdict(int)
        self.players = create_classes()
        self.team1, self.team2 = self.select_players()
    
    def select_players(self):
        print("Available Players:")
        for i, player in enumerate(self.players):
            print(f"{i + 1}: {player.name} ({player.player_class})")
        
        while True:
            try:
                team1_indices = input("Select players for Team 1 (comma-separated numbers): ").split(',')
                team1_indices = [int(i.strip()) - 1 for i in team1_indices]
                
                team2_indices = input("Select players for Team 2 (comma-separated numbers): ").split(',')
                team2_indices = [int(i.strip()) - 1 for i in team2_indices]
                
                #if any(i in team1_indices for i in team2_indices):
                   # print("A player cannot be in both teams!")
                    #continue
                
                if all(0 <= i < len(self.players) for i in team1_indices + team2_indices):
                    team1 = [self.players[i] for i in team1_indices]
                    team2 = [self.players[i] for i in team2_indices]
                    return team1, team2
                else:
                    print("Invalid selection, please choose valid player numbers.")
            except ValueError:
                print("Invalid input. Please enter numbers only.")

    def run_simulation(self):
        for _ in tqdm(range(self.num_simulations), desc="Simulating Battles"):
            fresh_team1 = copy.deepcopy(self.team1)
            fresh_team2 = copy.deepcopy(self.team2)
            simulation = CombatSimulation(fresh_team1, fresh_team2)
            winner = simulation.run_round()
            self.results[winner] += 1
        self.display_results()

    def display_results(self):
        print("\nFinal Results:")
        for team, wins in self.results.items():
            print(f"{team}: {wins} wins")

class CombatSimulation:
    def __init__(self, team1, team2):
        self.templates = initialize_templates()
        self.team1 = team1
        self.team2 = team2
        self.original_stats = {p.name: {"hit_points": p.hit_points, "num_heals": p.num_heals} for p in team1 + team2}

    def reset_players(self):
        for player in self.team1 + self.team2:
            player.hit_points = self.original_stats[player.name]["hit_points"]
            player.num_heals = self.original_stats[player.name]["num_heals"]

    def run_round(self):
        self.reset_players()
        while any(p.hit_points > 0 for p in self.team1) and any(p.hit_points > 0 for p in self.team2):
            for player in self.team1:
                if player.hit_points > 0:
                    target = random.choice([p for p in self.team2 if p.hit_points > 0])
                    self.perform_actions(player, target)
                    if all(p.hit_points <= 0 for p in self.team2):
                        return "Team 1 Wins"
            for player in self.team2:
                if player.hit_points > 0:
                    target = random.choice([p for p in self.team1 if p.hit_points > 0])
                    self.perform_actions(player, target)
                    if all(p.hit_points <= 0 for p in self.team1):
                        return "Team 2 Wins"

    def perform_actions(self, player, opponent):
        attack_roll = self.roll_dice(1, 20) + 1
        if attack_roll >= opponent.armor_class:
            damage = self.roll_dice(1, 6)
            opponent.hit_points -= damage
        if player.multi_attack:
            damage = self.roll_dice(1, 6)
            opponent.hit_points -= damage
        if player.can_heal and player.num_heals > 0 and player.hit_points < player.hit_point_max:
            heal_amount = self.roll_dice(1, 8)
            player.hit_points += heal_amount
            player.num_heals -= 1

    def roll_dice(self, num_dice, die_size):
        return sum(random.randint(1, die_size) for _ in range(num_dice))

monte_carlo = MonteCarloSimulation()
monte_carlo.run_simulation()
