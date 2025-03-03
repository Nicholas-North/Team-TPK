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
        self.team1 = team1
        self.team2 = team2
        self.original_stats = {p.name: {"hit_points": p.hit_points, "num_heals": p.num_heals} for p in team1 + team2}
        
        # Sort turn order by dexterity_score
        self.turn_order = sorted(team1 + team2, key=lambda p: p.dexterity_score, reverse=True)

    def reset_players(self):
        for player in self.team1 + self.team2:
            player.hit_points = self.original_stats[player.name]["hit_points"]
            player.num_heals = self.original_stats[player.name]["num_heals"]

    def run_round(self):
        self.reset_players()
        while any(p.hit_points > 0 for p in self.team1) and any(p.hit_points > 0 for p in self.team2):
            for player in self.turn_order:
                if player.hit_points > 0:
                    enemy_team = self.team2 if player in self.team1 else self.team1
                    if any(p.hit_points > 0 for p in enemy_team):
                        target = random.choice([p for p in enemy_team if p.hit_points > 0])
                        self.perform_actions(player, target)
                        if all(p.hit_points <= 0 for p in enemy_team):
                            return "Team 1 Wins" if enemy_team == self.team2 else "Team 2 Wins"

    def perform_actions(self, player, opponent):
        """Performs attacks based on multiattack and adds strength_score/2 to rolls and damage."""
        num_attacks = max(1, player.multi_attack)  # Ensure at least one attack
        for _ in range(num_attacks):
            attack_roll = self.roll_dice(1, 20) + ((player.main_score - 10) // 2)  # Use main ability modifier
            
            
            
            
            if attack_roll >= opponent.armor_class:
                damage = sum(self.roll_dice(1, player.dice_size) for _ in range(player.num_dice))  # Roll multiple dice
                damage += ((player.main_score - 10) // 2)  # Add main modifier to damage
                opponent.hit_points -= damage
                
                

        if player.can_heal and player.num_heals > 0 and player.hit_points < player.hit_point_max:
            heal_amount = self.roll_dice(1, 8)
            player.hit_points = min(player.hit_point_max, player.hit_points + heal_amount)
            player.num_heals -= 1
            print(f"{player.name} heals for {heal_amount} HP, now at {player.hit_points}/{player.hit_point_max} HP.")

    def roll_dice(self, num_dice, dice_size):
        return sum(random.randint(1, dice_size) for _ in range(num_dice))

monte_carlo = MonteCarloSimulation()
monte_carlo.run_simulation()
