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
        # Automatically assigns players to Friends or Foes based on player.friendFoe (0 = Friend, 1 = Foe)
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
                SELECT abilityID, abilityName, meleeRangedAOE, healTag, firstNumDice, firstDiceSize, firstDamageType,
                       secondNumDice, secondDiceSize, secondDamageType, rangeOne, rangeTwo, radius, spellLevel, saveType, actionType
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

        # Return the win counts so you can send them back to the database
        return friends_wins, foes_wins

class CombatSimulation:
    def __init__(self, friends, foes, player_abilities):
        self.friends = friends
        self.foes = foes
        self.player_abilities = player_abilities  # Use pre-fetched abilities
        self.original_stats = {p.characterName: {"hp": p.hp, "numHeals": p.numHeals, "spellLevel1": p.spellLevel1, "spellLevel2": p.spellLevel2, "spellLevel3": p.spellLevel3, "spellLevel4": p.spellLevel4, "spellLevel5": p.spellLevel5} for p in friends + foes}
        
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
            player.spellLevel1 = self.original_stats[player.characterName]["spellLevel1"]
            player.spellLevel2 = self.original_stats[player.characterName]["spellLevel2"]
            player.spellLevel3 = self.original_stats[player.characterName]["spellLevel3"]
            player.spellLevel4 = self.original_stats[player.characterName]["spellLevel4"]
            player.spellLevel5 = self.original_stats[player.characterName]["spellLevel5"]

    def run_round(self):
        self.reset_players()
        while any(p.hp > 0 for p in self.friends) and any(p.hp > 0 for p in self.foes):
            for player in self.turn_order:
                if player.hp <= player.hpMax/2: # If Player is Bloodied, set flag
                    player.bloodied = 1
                if player.hp > 0: # If Player is Alive
                    enemy_team = self.foes if player in self.friends else self.friends
                    if any(p.hp > 0 for p in enemy_team):
                        bloodied_enemies = [p for p in enemy_team if p.hp > 0 and p.hp <= p.hpMax / 2] # Check if there are any bloodied enemies
                        if bloodied_enemies:
                            target = random.choice(bloodied_enemies)
                        else:
                            target = random.choice([p for p in enemy_team if p.hp > 0]) # If no bloodied enemies, choose a random target
                        self.perform_actions(player, target)
                        if all(p.hp <= 0 for p in enemy_team):
                            return "Friends Win" if enemy_team == self.foes else "Foes Win"

    def perform_actions(self, player, opponent):
        # Allow the player to choose and perform an ability
        abilities = self.player_abilities.get(player.characterID, [])
        if not abilities:
            return

        # Determine if there is a bloodied ally and if the player has a healing ability
        ally_team = self.friends if player in self.friends else self.foes
        bloodied_allies = [ally for ally in ally_team + [player] if ally.hp > 0 and ally.hp <= ally.hpMax / 2]
        healing_abilities = [ability for ability in abilities if ability.healTag == 1]
        attack_abilities = [ability for ability in abilities if ability.healTag == 0]

        # If there is a bloodied ally and a healing ability is available, prioritize healing
        if bloodied_allies and healing_abilities and (player.numHeals > 0):
            if player.hp <= player.hpMax / 2:
                for ability in healing_abilities:
                    if ability.abilityName.lower() == 'second wind':
                        self.perform_heal(player, ability)  # Use "Second Wind" to heal the player
                        break
            target_ally = random.choice(bloodied_allies)
            chosen_ability = random.choice(healing_abilities)
            self.perform_heal(target_ally, chosen_ability)
        else:
            # If no bloodied allies or no healing abilities, proceed with attacking the opponent
            if attack_abilities:
                usable_abilities = []
                for ability in attack_abilities:
                    if ability.spellLevel is None or ability.spellLevel == 0:
                        usable_abilities.append(ability)
                    elif ability.spellLevel is not None:
                        if self.has_spell_slot(player, ability.spellLevel):
                            usable_abilities.append(ability)

                if usable_abilities:
                    chosen_ability = random.choice(usable_abilities)
                    # Check if the ability requires a spell slot and expend it
                    if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                        self.expend_spell_slot(player, chosen_ability.spellLevel)
                    self.perform_attack(player, opponent, chosen_ability)

    def has_spell_slot(self, player, spell_level):
        # Check if the player has an available spell slot of the required level or higher
        for level in range(spell_level, 6):  # Check levels from spell_level up to 5
            if level == 1 and player.spellLevel1 is not None and player.spellLevel1 > 0:
                return True
            elif level == 2 and player.spellLevel2 is not None and player.spellLevel2 > 0:
                return True
            elif level == 3 and player.spellLevel3 is not None and player.spellLevel3 > 0:
                return True
            elif level == 4 and player.spellLevel4 is not None and player.spellLevel4 > 0:
                return True
            elif level == 5 and player.spellLevel5 is not None and player.spellLevel5 > 0:
                return True
        return False

    def expend_spell_slot(self, player, spell_level):
        # Expend the appropriate spell slot based on the spell level
        for level in range(spell_level, 6):  # Check levels from spell_level up to 5
            if self.has_spell_slot(player, level):
                if level == 1:
                    player.spellLevel1 -= 1
                elif level == 2:
                    player.spellLevel2 -= 1
                elif level == 3:
                    player.spellLevel3 -= 1
                elif level == 4:
                    player.spellLevel4 -= 1
                elif level == 5:
                    player.spellLevel5 -= 1
                return

    def perform_heal(self, player, ability):
        # Perform a heal based on the chosen ability
        heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
        player.hp = min(player.hpMax, player.hp + heal_amount)
        player.numHeals -= 1

    def perform_attack(self, player, opponent, ability):
        # Perform an attack based on the chosen ability
        attack_type = ability.meleeRangedAOE.lower()  # Get the attack type (melee, ranged, or AOE)

        if attack_type == 'melee':
            # Melee attack: single target, must be in melee range
            if ((abs(player.xloc) - opponent.xloc) <= 1 and abs(player.yloc - opponent.yloc) <= 1):
                attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)  # Use main ability modifier
                if attack_roll >= opponent.ac:
                    damage = self.calculate_damage(ability, player)
                    opponent.hp -= damage

        elif attack_type == 'ranged':
            # Ranged attack: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if distance <= ability.rangeOne:
                attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)  # Use main ability modifier
                if attack_roll >= opponent.ac:
                    damage = self.calculate_damage(ability, player)
                    opponent.hp -= damage

        elif attack_type == 'aoe':
            # AOE attack: targets enemies, but allies in the radius are also affected
            enemy_team = self.foes if player in self.friends else self.friends  # Determine enemy team
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team

            for enemy in enemy_team:
                if enemy.hp > 0:  # Only target alive enemies
                    distance = self.calculate_distance(player.xloc, player.yloc, enemy.xloc, enemy.yloc)
                    if distance <= ability.radius:
                        if ability.saveType:  # If the AOE requires a saving throw
                            # Determine the appropriate saving throw modifier based on ability.saveType
                            save_modifier = self.get_save_modifier(enemy, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier  # Enemy's saving throw
                            if save_roll >= ((player.mainScore - 10) // 2) + 10:  # Enemy succeeds on the save
                                damage = self.calculate_damage(ability, player) // 2  # Half damage on save
                            else:  # Enemy fails the save
                                damage = self.calculate_damage(ability, player)
                        else:  # No saving throw required
                            damage = self.calculate_damage(ability, player)
                        enemy.hp -= damage

            # Then, check for allies in the radius and apply effects if necessary
            for ally in ally_team:
                if ally.hp > 0:  # Only target alive allies
                    distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
                    if distance <= ability.radius:
                        if ability.saveType:  # If the AOE requires a saving throw
                            # Determine the appropriate saving throw modifier based on ability.saveType
                            save_modifier = self.get_save_modifier(ally, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier  # Ally's saving throw
                            if save_roll >= ((player.mainScore - 10) // 2) + 10:  # Ally succeeds on the save
                                damage = self.calculate_damage(ability, player) // 2  # Half damage on save
                            else:  # Ally fails the save
                                damage = self.calculate_damage(ability, player)
                        else:  # No saving throw required
                            damage = self.calculate_damage(ability, player)
                        ally.hp -= damage

        else:
            print(f"Unknown attack type: {attack_type}")

    def calculate_distance(self, x1, y1, x2, y2):
        # Calculate the distance between two points using Euclidean distance
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def calculate_damage(self, ability, player):
        # Calculate damage for an ability
        damage = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))  # Roll dice
        if ability.secondNumDice is not None:
            damage += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
        damage += ((player.mainScore - 10) // 2)  # Add main modifier to damage
        return damage

    def get_save_modifier(self, enemy, save_type):
        # Get the appropriate saving throw modifier based on save_type
        save_type = save_type.lower()
        if save_type == 'strength':
            return (enemy.strScore - 10) // 2
        elif save_type == 'dexterity':
            return (enemy.dexScore - 10) // 2
        elif save_type == 'constitution':
            return (enemy.conScore - 10) // 2
        elif save_type == 'intelligence':
            return (enemy.intScore - 10) // 2
        elif save_type == 'wisdom':
            return (enemy.wisScore- 10) // 2
        elif save_type == 'charisma':
            return (enemy.chaScore - 10) // 2
        else:
            return 0  # Default to no modifier if save_type is invalid

    def roll_dice(self, numDice, diceSize):
        return sum(random.randint(1, diceSize) for _ in range(numDice))