import random
import copy
from enum import Enum
from typing import List
from collections import defaultdict
from Classes import fetch_characters
from tqdm import tqdm

class ActionType(Enum):
    Movement = 1
    Action = 2
    BonusAction = 3

class MonteCarloSimulation:
    def __init__(self, num_simulations, players):
        self.num_simulations = num_simulations
        self.results = defaultdict(int)
        self.players = players
        self.friends, self.foes = self.select_players()
    
        print(f"Monte Carlo Simulation initialized with {len(self.players)} players.")
        for player in self.players:
            print(player)
            
    def select_players(self):
        """Automatically assigns players to Friends or Foes based on player.friendFoe (0 = Friend, 1 = Foe)."""
        friends = [player for player in self.players if player.friendFoe == 0]  # Friends
        foes = [player for player in self.players if player.friendFoe == 1]  # Foes

        # Display teams
        print("\n=== Friends ===")
        for player in friends:
            print(f"{player.characterName} ({player.characterClass})")

        print("\n=== Foes ===")
        for player in foes:
            print(f"{player.characterName} ({player.characterClass})")

        return friends, foes
    
    def run_simulation(self):
        for _ in tqdm(range(self.num_simulations), desc="Simulating Battles"):
            fresh_friends = copy.deepcopy(self.friends)
            fresh_foes = copy.deepcopy(self.foes)
            simulation = CombatSimulation(fresh_friends, fresh_foes)
            winner = simulation.run_round()
            self.results[winner] += 1
        self.display_results()

    def display_results(self):
    # Retrieve wins from the results dictionary (defaulting to 0 if not present)
        friends_wins = self.results.get("Friends Win", 0)
        foes_wins = self.results.get("Foes Win", 0)
    
        print("\nFinal Results:")
        print(f"Friends: {friends_wins} wins")
        print(f"Foes: {foes_wins} wins")
    
    # Return the win counts so you can send them back to the database
        return friends_wins, foes_wins
class CombatSimulation:
    def __init__(self, friends, foes):
        self.friends = friends
        self.foes = foes
        self.original_stats = {p.characterName: {"hp": p.hp, "numHeals": p.numHeals} for p in friends + foes}
        
        # Sort turn order by dexScore
        self.turn_order = sorted(friends + foes, key=lambda p: p.dexScore, reverse=True)

    def reset_players(self):
        for player in self.friends + self.foes:
            player.hp = self.original_stats[player.characterName]["hp"]
            player.numHeals = self.original_stats[player.characterName]["numHeals"]

    def run_round(self):
        self.reset_players()
        while any(p.hp > 0 for p in self.friends) and any(p.hp > 0 for p in self.foes):
            for player in self.turn_order:
                if player.hp > 0:
                    enemy_team = self.foes if player in self.friends else self.friends
                    if any(p.hp > 0 for p in enemy_team):
                        target = random.choice([p for p in enemy_team if p.hp > 0])
                        self.perform_actions(player, target)
                        if all(p.hp <= 0 for p in enemy_team):
                            return "Friends Win" if enemy_team == self.foes else "Foes Win"

    def perform_actions(self, player, opponent):
        """Performs attacks based on multiattack and adds strength_score/2 to rolls and damage."""
        num_attacks = max(1, player.attackCount)  # Ensure at least one attack
        for _ in range(num_attacks):
            attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)  # Use main ability modifier
            
            if attack_roll >= opponent.ac:
                damage = sum(self.roll_dice(1, player.diceSize) for _ in range(player.numDice))  # Roll multiple dice
                damage += ((player.mainScore - 10) // 2)  # Add main modifier to damage
                opponent.hp -= damage

        if player.canHeal and player.numHeals > 0 and player.hp < player.hpMax:
            heal_amount = self.roll_dice(1, 8)
            player.hp = min(player.hpMax, player.hp + heal_amount)
            player.numHeals -= 1

    def roll_dice(self, numDice, diceSize):
        return sum(random.randint(1, diceSize) for _ in range(numDice))

#monte_carlo = MonteCarloSimulation()
#monte_carlo.run_simulation()
