import random
import copy
from enum import Enum
from typing import List
from collections import defaultdict
from tqdm import tqdm
import pyodbc
from multiprocessing import Pool

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
        
        # Fetch all player abilities before starting multiprocessing
        self.player_abilities = self.fetch_all_player_abilities()
        
        # Precompute original stats for resetting players
        self.original_stats = {}
        for p in self.friends + self.foes:
            # Calculate numHeals based on abilities with healTag == 1
            numHeals = sum(1 for ability in self.player_abilities.get(p.characterID, []) if ability.healTag == 1)
            
            self.original_stats[p.characterName] = {
                "hp": p.hp, 
                "numHeals": numHeals,  # Updated to be calculated based on healTag
                "spellLevel1": p.spellLevel1, 
                "spellLevel2": p.spellLevel2, 
                "spellLevel3": p.spellLevel3, 
                "spellLevel4": p.spellLevel4, 
                "spellLevel5": p.spellLevel5
            }

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
        db_connection = create_db_connection()  # Create a temporary connection
        cursor = db_connection.cursor()
        abilities = {}
        cursor.execute("""
            SELECT ca.characterID, am.abilityID, am.abilityName, am.meleeRangedAOE, am.healTag, 
                am.firstNumDice, am.firstDiceSize, am.firstDamageType, am.secondNumDice, 
                am.secondDiceSize, am.secondDamageType, am.rangeOne, am.rangeTwo, 
                am.radius, am.spellLevel, am.saveType, am.actionType
            FROM character.abilityModel am
            JOIN character.characterAbility ca ON am.abilityID = ca.abilityID
        """)
        for row in cursor.fetchall():
            characterID = row.characterID
            if characterID not in abilities:
                abilities[characterID] = []
            abilities[characterID].append(row)
        db_connection.close()  # Close the connection after fetching data
        return abilities

    def run_simulation(self):
        # Prepare data for multiprocessing
        simulation_data = {
            "friends": self.friends,
            "foes": self.foes,
            "player_abilities": self.player_abilities,
            "original_stats": self.original_stats
        }

        # Use multiprocessing to parallelize simulations
        with Pool() as pool:
            results = pool.map(run_single_simulation, [simulation_data] * self.num_simulations)
        
        for winner in results:
            self.results[winner] += 1
        self.display_results()

    def display_results(self):
        # Retrieve wins from the results dictionary (defaulting to 0 if not present)
        friends_wins = self.results.get("Friends Win", 0)
        foes_wins = self.results.get("Foes Win", 0)

        # Return the win counts so you can send them back to the database
        return friends_wins, foes_wins

def run_single_simulation(simulation_data):
    friends = simulation_data["friends"]
    foes = simulation_data["foes"]
    player_abilities = simulation_data["player_abilities"]
    original_stats = simulation_data["original_stats"]

    # Reset players
    for player in friends + foes:
        player.hp = original_stats[player.characterName]["hp"]
        player.numHeals = original_stats[player.characterName]["numHeals"]
        player.spellLevel1 = original_stats[player.characterName]["spellLevel1"]
        player.spellLevel2 = original_stats[player.characterName]["spellLevel2"]
        player.spellLevel3 = original_stats[player.characterName]["spellLevel3"]
        player.spellLevel4 = original_stats[player.characterName]["spellLevel4"]
        player.spellLevel5 = original_stats[player.characterName]["spellLevel5"]

    simulation = CombatSimulation(friends, foes, player_abilities)
    return simulation.run_round()
    
class CombatSimulation:
    def __init__(self, friends, foes, player_abilities):
        self.friends = friends
        self.foes = foes
        self.player_abilities = player_abilities  # Use pre-fetched abilities
        
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

    def run_round(self):
        max_iterations = 1000  # Prevent infinite loops
        iteration = 0
        while any(p.hp > 0 for p in self.friends) and any(p.hp > 0 for p in self.foes):
            iteration += 1
            if iteration > max_iterations:
                return "Stalemate"
            for player in self.turn_order:
                if player.hp > 0:  # If Player is Alive
                    enemy_team = self.foes if player in self.friends else self.friends
                    alive_enemies = [p for p in enemy_team if p.hp > 0]
                    if alive_enemies:
                        bloodied_enemies = [p for p in alive_enemies if p.hp <= p.hpMax / 2]
                        target = random.choice(bloodied_enemies) if bloodied_enemies else random.choice(alive_enemies)
                        self.perform_actions(player, target)
                        if all(p.hp <= 0 for p in enemy_team):
                            return "Friends Win" if enemy_team == self.foes else "Foes Win"

    def perform_actions(self, player, opponent):
        abilities = self.player_abilities.get(player.characterID, [])
        if not abilities:
            return

        # Precompute usable abilities
        usable_abilities = []
        for ability in abilities:
            if ability.spellLevel is None or ability.spellLevel == 0:
                usable_abilities.append(ability)
            elif ability.spellLevel is not None and self.has_spell_slot(player, ability.spellLevel):
                usable_abilities.append(ability)

        if not usable_abilities:
            return

        # Determine if there is a bloodied ally and if the player has a healing ability
        ally_team = self.friends if player in self.friends else self.foes
        bloodied_allies = [ally for ally in ally_team + [player] if ally.hp > 0 and ally.hp <= ally.hpMax / 2]
        healing_abilities = [ability for ability in usable_abilities if ability.healTag == 1]

        # Prioritize "Second Wind" for self-healing
        if player.hp <= player.hpMax / 2:
            second_wind = next((ability for ability in healing_abilities if ability.abilityName.lower() == 'second wind'), None)
            if second_wind and player.numHeals > 0:
                self.perform_heal(player, player, second_wind)
                return  

        # If there are bloodied allies and healing abilities available, prioritize healing them
        if bloodied_allies and healing_abilities and (player.numHeals > 0):
            # Filter out "Second Wind" from healing abilities to prevent it from being used on allies
            healing_abilities = [ability for ability in healing_abilities if ability.abilityName.lower() != 'second wind']
            if healing_abilities:
                target_ally = random.choice(bloodied_allies)
                chosen_ability = random.choice(healing_abilities)
                # Check if the ability requires a spell slot and expend it
                if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                    self.expend_spell_slot(player, chosen_ability.spellLevel)
                self.perform_heal(player, target_ally, chosen_ability)
                return 

        # If no bloodied allies or no healing abilities, proceed with attacking the opponent
        attack_abilities = [ability for ability in usable_abilities if ability.healTag == 0]
        if attack_abilities:
            chosen_ability = random.choice(attack_abilities)
            # Check if the ability requires a spell slot and expend it
            if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                self.expend_spell_slot(player, chosen_ability.spellLevel)
            self.perform_attack(player, opponent, chosen_ability)

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

    def perform_heal(self, player, ally, ability):
        # Perform a heal based on the chosen ability
        heal_type = ability.meleeRangedAOE.lower()

        if heal_type == 'melee':
            # Melee heal: single target, must be in melee range
            if ((abs(player.xloc) - ally.xloc) <= 1 and abs(player.yloc - ally.yloc) <= 1):
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += ((player.mainScore - 10) // 2)
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                ''' print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}!") '''
                player.numHeals -= 1

        elif heal_type == 'ranged':
            # Ranged heal: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if distance <= ability.rangeOne:
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += ((player.mainScore - 10) // 2)
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                ''' print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}!") '''
                player.numHeals -= 1

        elif heal_type == 'aoe':
            # AOE heal: heals allies within the given radius
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team
            for ally in ally_team:
                distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
                if distance <= ability.radius:
                    heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1)) 
                    if ability.secondNumDice is not None:
                        heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                    heal_amount += ((player.mainScore - 10) // 2)
                    ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                    ''' print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}!") '''
                    player.numHeals -= 1
        else:
            print(f"Unknown heal type: {heal_type}")

    def perform_attack(self, player, opponent, ability):
        # Perform an attack based on the chosen ability
        attack_type = ability.meleeRangedAOE.lower() 

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
                        if ability.saveType: 
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