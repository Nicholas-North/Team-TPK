import random
import copy
from enum import Enum
from typing import List
from collections import defaultdict
from tqdm import tqdm
import pyodbc

def create_db_connection():
    DB_SERVER = 'database-1.c16m0yos4c9g.us-east-2.rds.amazonaws.com,1433'
    DB_NAME = 'teamTPK'
    DB_USER = 'admin'
    DB_PASSWORD = 'teamtpk4vr!'
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}'
    return pyodbc.connect(connection_string)

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
        self.db_connection = create_db_connection()
        self.player_abilities = self.fetch_all_player_abilities()
    
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
    
    def fetch_all_player_abilities(self):
        cursor = self.db_connection.cursor()
        abilities = {}
        for player in self.players:
            cursor.execute("""
                SELECT abilityID, abilityName, meleeRangedAOE, healTag, firstNumDice, firstDiceSize, firstDamageType
                FROM character.abilityModel
                WHERE abilityID IN (
                    SELECT abilityID FROM character.characterAbility WHERE characterID = ?
                )
            """, player.characterID)
            abilities[player.characterID] = cursor.fetchall()
        return abilities

    def run_simulation(self):
        for _ in tqdm(range(self.num_simulations), desc="Simulating Battles"):
            fresh_friends = copy.deepcopy(self.friends)
            fresh_foes = copy.deepcopy(self.foes)
            simulation = CombatSimulation(fresh_friends, fresh_foes, self.player_abilities)
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
    def __init__(self, friends, foes, player_abilities):
        self.friends = friends
        self.foes = foes
        self.player_abilities = player_abilities  # Use pre-fetched abilities
        self.original_stats = {p.characterName: {"hp": p.hp, "numHeals": p.numHeals} for p in friends + foes}
        
        # Sort turn order by dexScore
        self.turn_order = self.roll_initiative(friends + foes)

    def roll_initiative(self, players):
        initiative_rolls = []
        for player in players:
            roll = self.roll_dice(1, 20)  # Roll 1d20
            dex_modifier = (player.dexScore - 10) // 2  # Calculate Dexterity modifier
            initiative = roll + dex_modifier
            initiative_rolls.append((player, initiative))

        # Sort players by initiative in descending order
        sorted_players = sorted(initiative_rolls, key=lambda x: x[1], reverse=True)
        return [player for player, _ in sorted_players]

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
        """Allow the player to choose and perform an ability."""
        abilities = self.player_abilities.get(player.characterID, [])
        if not abilities:
            return

        # Choose a random ability (for simulation purposes)
        chosen_ability = random.choice(abilities)

        # Perform the chosen ability
        if chosen_ability.healTag == 1:
            self.perform_heal(player, chosen_ability)
        else:
            self.perform_attack(player, opponent, chosen_ability)

    def perform_attack(self, player, opponent, ability):
        """Perform an attack based on the chosen ability."""
        attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)  # Use main ability modifier
        
        if attack_roll >= opponent.ac:
            damage = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))  # Roll dice
            damage += ((player.mainScore - 10) // 2)  # Add main modifier to damage
            opponent.hp -= damage

    def perform_heal(self, player, ability):
        """Perform a heal based on the chosen ability."""
        if player.numHeals > 0:
            heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
            player.hp = min(player.hpMax, player.hp + heal_amount)
            player.numHeals -= 1

    def roll_dice(self, numDice, diceSize):
        return sum(random.randint(1, diceSize) for _ in range(numDice))