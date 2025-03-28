import random
from enum import Enum
from collections import defaultdict
import pyodbc
from multiprocessing import Pool
import copy
from multiprocessing import Manager

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
    def __init__(self, num_simulations, players, encounter_id):
        self.num_simulations = num_simulations
        self.results = defaultdict(int)
        self.total_rounds = 0
        self.players = players
        self.friends, self.foes = self.select_players()  
        self.grid_xdim, self.grid_ydim = self.fetch_encounter_dimensions(encounter_id)

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
                "spellLevel5": p.spellLevel5,
                "deathSaves": {'success': 0, 'failure': 0}
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
    
    def fetch_encounter_dimensions(self, encounter_id):
        db_connection = None
        try:
            db_connection = create_db_connection()
            cursor = db_connection.cursor()
            
            query = "SELECT xdim, ydim FROM encounter.encounter WHERE encounterID = ?"
            cursor.execute(query, (encounter_id,))  # Note the comma for single-element tuple
            
            result = cursor.fetchone()
            if result:
                return result.xdim, result.ydim
            return 15, 15  # Default dimensions if no result found
            
        except Exception as e:
            print(f"Error fetching encounter dimensions: {str(e)}")
            return 15, 15  # Return defaults on error
        finally:
            if db_connection:
                db_connection.close()

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
        # Use a Manager to create thread-safe data structures
        manager = Manager()
        results = manager.list()  # Thread-safe list to store results
        round_counts = manager.list()

        # Prepare data for multiprocessing
        simulation_data = {
            "friends": self.friends,
            "foes": self.foes,
            "player_abilities": self.player_abilities,
            "original_stats": self.original_stats,
            "grid_xdim": self.grid_xdim,
            "grid_ydim": self.grid_ydim
        }

        # Use multiprocessing to parallelize simulations
        with Pool() as pool:
            pool.starmap(run_single_simulation, [(simulation_data, results, round_counts) for _ in range(self.num_simulations)])

        # Aggregate results
        for winner in results:
            self.results[winner] += 1

        if round_counts:
            self.total_rounds = sum(round_counts) / len(round_counts)
        self.display_results()

    def display_results(self):
        # Retrieve wins from the results dictionary (defaulting to 0 if not present)
        friends_wins = self.results.get("Friends Win", 0)
        foes_wins = self.results.get("Foes Win", 0)

        # Return the win counts so you can send them back to the database
        return friends_wins, foes_wins, self.total_rounds

def run_single_simulation(simulation_data, results, round_counts):
    # Deep copy the players to avoid data bleed
    friends = copy.deepcopy(simulation_data["friends"])
    foes = copy.deepcopy(simulation_data["foes"])
    player_abilities = simulation_data["player_abilities"]
    original_stats = simulation_data["original_stats"]
    grid_xdim = simulation_data.get("grid_xdim", 15)  # Default to 15 if not provided
    grid_ydim = simulation_data.get("grid_ydim", 15)  # Default to 15 if not provided

    # Reset players using the deep-copied data
    for player in friends + foes:
        player.hp = original_stats[player.characterName]["hp"]
        player.numHeals = original_stats[player.characterName]["numHeals"]
        player.spellLevel1 = original_stats[player.characterName]["spellLevel1"]
        player.spellLevel2 = original_stats[player.characterName]["spellLevel2"]
        player.spellLevel3 = original_stats[player.characterName]["spellLevel3"]
        player.spellLevel4 = original_stats[player.characterName]["spellLevel4"]
        player.spellLevel5 = original_stats[player.characterName]["spellLevel5"]
        player.deathSaves = {'success': 0, 'failure': 0}

    simulation = CombatSimulation(friends, foes, player_abilities, grid_xdim, grid_ydim)
    winner, numRounds = simulation.run_round()
    results.append(winner)
    round_counts.append(numRounds)

class CombatSimulation:
    def __init__(self, friends, foes, player_abilities, grid_xdim=15, grid_ydim=15):
        self.friends = friends
        self.foes = foes
        self.player_abilities = player_abilities
        self.grid_xdim = grid_xdim
        self.grid_ydim = grid_ydim
        
        self.initialize_positions()
        self.turn_order, self.initiative_rolls = self.roll_initiative(friends + foes)
        self.print_initiative_order()

    def roll_initiative(self, players):
        initiative_rolls = {}
        for player in players:
            roll = self.roll_dice(1, 20)  # Roll 1d20
            dex_modifier = (player.dexScore - 10) // 2  # Calculate Dexterity modifier
            initiative = roll + dex_modifier
            initiative_rolls[player] = initiative

        # Sort players by initiative in descending order
        sorted_players = sorted(initiative_rolls.keys(), key=lambda x: initiative_rolls[x], reverse=True)
        return sorted_players, initiative_rolls
   
    def initialize_positions(self):
        # Randomly assign starting grid positions
        occupied = set()
        for player in self.friends + self.foes:
            while True:
                x = random.randint(1, self.grid_xdim)
                y = random.randint(1, self.grid_ydim)
                if (x, y) not in occupied:
                    player.xloc, player.yloc = x, y
                    occupied.add((x, y))
                    break
    
    def print_initiative_order(self):
        print("Initiative Order:")
        for i, player in enumerate(self.turn_order):
            # Safely get positions with boundary checking
            x = max(0, min(getattr(player, 'xloc', 0), self.grid_xdim))
            y = max(0, min(getattr(player, 'yloc', 0), self.grid_ydim))
            print(f"{i + 1}. {player.characterName} (Initiative: {self.initiative_rolls[player]}) - Position: ({x}, {y})")
        print("\n")
    
    def run_round(self):
        max_iterations = 50  # Prevent infinite loops
        iteration = 0
        while any(p.hp > 0 for p in self.friends) and any(p.hp > 0 for p in self.foes):
            iteration += 1
            if iteration > max_iterations:
                return "Stalemate", 0
            
            # Iterate through the turn_order list once per round
            for player in self.turn_order:
                if player.hp > 0:  # If Player is Alive
                    enemy_team = self.foes if player in self.friends else self.friends
                    alive_enemies = [p for p in enemy_team if p.hp > 0]
                    if alive_enemies:
                        bloodied_enemies = [p for p in alive_enemies if p.hp <= p.hpMax / 2]
                        target = random.choice(bloodied_enemies) if bloodied_enemies else random.choice(alive_enemies)
                        self.perform_actions(player, target)
                        if all(p.hp <= 0 for p in enemy_team):
                            if enemy_team == self.foes:
                                print("Friends Win! :D\n")
                                return "Friends Win", iteration
                            else:
                                print("Foes Win :(\n")
                                return "Foes Win", iteration
                    else:
                        print(f"No alive enemies for {player.characterName} to target.")
                elif player.hp == 0 and player in self.friends:  # If Player is Unconscious (only for friends)
                    can_take_turn = self.handle_death_saves(player)
                    if can_take_turn:
                        # Allow the player to take their turn
                        enemy_team = self.foes if player in self.friends else self.friends
                        alive_enemies = [p for p in enemy_team if p.hp > 0]
                        if alive_enemies:
                            bloodied_enemies = [p for p in alive_enemies if p.hp <= p.hpMax / 2]
                            target = random.choice(bloodied_enemies) if bloodied_enemies else random.choice(alive_enemies)
                            self.perform_actions(player, target)
                            if all(p.hp <= 0 for p in enemy_team):
                                if enemy_team == self.foes:
                                    print("Friends Win! :D\n")
                                    return "Friends Win", iteration
                                else:
                                    print("Foes Win :(\n")
                                    return "Foes Win", iteration
                else:
                    print(f"{player.characterName} is unconscious or dead and cannot take a turn.")
            # End of round
            print("End of round.\n")
                            
    def handle_death_saves(self, player):
        # Perform a death save
        death_save_roll = self.roll_dice(1, 20)
        if death_save_roll == 20:
            # Critical success: regain 1 HP
            player.hp = 1
            player.deathSaves = {'success': 0, 'failure': 0}
            print(f"{player.characterName} critically succeeds on a death save and regains 1 HP!")
            return True  # Indicate that the player can take their turn
        elif death_save_roll >= 10:
            # Success
            player.deathSaves['success'] += 1
            print(f"{player.characterName} succeeds on a death save! (Successes: {player.deathSaves['success']}, Failures: {player.deathSaves['failure']})")
        elif death_save_roll == 1:
            # Critical failure: count as two failures
            player.deathSaves['failure'] += 2
            print(f"{player.characterName} critically fails on a death save! (Successes: {player.deathSaves['success']}, Failures: {player.deathSaves['failure']})")
        else:
            # Failure
            player.deathSaves['failure'] += 1
            print(f"{player.characterName} fails on a death save! (Successes: {player.deathSaves['success']}, Failures: {player.deathSaves['failure']})")

        # Check if the player has stabilized or died
        if player.deathSaves['success'] >= 3:
            player.hp = 1  # Stabilized
            player.deathSaves = {'success': 0, 'failure': 0}
            print(f"{player.characterName} has stabilized!")
        elif player.deathSaves['failure'] >= 3:
            player.hp = -1  # Dead
            print(f"{player.characterName} has died...")
        return False  # Indicate that the player cannot take their turn

    def perform_actions(self, player, opponent):

        # Move the current player
        self.move_character(player)

        # Check if the player is flanking and give advantage if so
        if (not player.hasAdvantage and not player.hasDisadvantage and self.check_flanking(player, opponent)):
            player.hasAdvantage = True
            print(f"{player.characterName} gains advantage from flanking {opponent.characterName}!")

        abilities = self.player_abilities.get(player.characterID, [])
        if not abilities:
            return
        
        action_used = False
        bonus_action_used = False

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
        bloodied_allies = [ally for ally in ally_team + [player] if ally.hp >= 0 and ally.hp <= ally.hpMax / 2]
        healing_abilities = [ability for ability in usable_abilities if ability.healTag == 1]
        attack_abilities = [ability for ability in usable_abilities if ability.healTag == 0]

        # Seperate usable abilities into action and bonus actions
        action_abilities = [ability for ability in attack_abilities if ability.actionType.lower() == "action"]
        bonus_action_abilities = [ability for ability in attack_abilities if ability.actionType.lower() == "bonus"]

        # Prioritize "Second Wind" for self-healing
        if player.hp <= player.hpMax / 2:
            second_wind = next((ability for ability in healing_abilities if ability.abilityName.lower() == 'second wind'), None)
            if second_wind and player.numHeals > 0 and not bonus_action_used:
                self.perform_heal(player, player, second_wind)
                bonus_action_used = True
                player.numHeals -= 1  

        # If there are bloodied allies and healing abilities available, prioritize healing them
        if (bloodied_allies or any(ally.hp <= 0 for ally in ally_team)) and healing_abilities and (player.numHeals > 0):
            # Filter out "Second Wind" from healing abilities to prevent it from being used on allies
            healing_abilities = [ability for ability in healing_abilities if ability.abilityName.lower() != 'second wind']
            if healing_abilities:
                # Find all potential targets (alive bloodied or unconscious allies)
                potential_targets = [ally for ally in ally_team if (ally.hp <= ally.hpMax / 2 or ally.hp <= 0) and ally.hp > -1]
                if potential_targets:
                    # Find the minimum HP among potential targets
                    min_hp = min(ally.hp for ally in potential_targets)
                    lowest_hp_allies = [ally for ally in potential_targets if ally.hp == min_hp]
                    target_ally = random.choice(lowest_hp_allies)
                    chosen_ability = random.choice(healing_abilities)
                    
                    # Perform heal with appropriate action type
                    if chosen_ability.actionType.lower() == "bonus" and not bonus_action_used:
                        if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                            self.expend_spell_slot(player, chosen_ability.spellLevel)
                        self.perform_heal(player, target_ally, chosen_ability)
                        bonus_action_used = True

                    elif chosen_ability.actionType.lower() == "action" and not action_used:
                        if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                            self.expend_spell_slot(player, chosen_ability.spellLevel)
                        self.perform_heal(player, target_ally, chosen_ability)
                        action_used = True

        # If no bloodied allies or no healing abilities, proceed with attacking the opponent
        if bonus_action_abilities and not bonus_action_used:
            chosen_ability = random.choice(bonus_action_abilities)

            if chosen_ability.abilityName.lower() == "hide":
                # Calculate average enemy perception (passive Perception)
                active_enemies = [e for e in (self.foes if player in self.friends else self.friends) if e.hp > 0]
                if active_enemies:
                    avg_perception = sum((e.wisScore - 10) // 2 + 10 for e in active_enemies) / len(active_enemies)
                    stealth_roll = self.roll_dice(1, 20) + ((player.dexScore - 10) // 2)  # Dexterity (Stealth) check
                    
                    if stealth_roll > avg_perception:
                        player.hasAdvantage = True
                        print(f"{player.characterName} successfully hides (Stealth: {stealth_roll} vs Perception: {avg_perception:.1f}) and gains advantage!")
                    else:
                        print(f"{player.characterName} fails to hide (Stealth: {stealth_roll} vs Perception: {avg_perception:.1f})")
            else:
                # Check if the ability requires a spell slot and expend it
                if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                    self.expend_spell_slot(player, chosen_ability.spellLevel)
                self.perform_attack(player, opponent, chosen_ability)
            bonus_action_used = True

        if action_abilities and not action_used:
            chosen_ability = random.choice(action_abilities)
            # Check if the ability requires a spell slot and expend it
            if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                self.expend_spell_slot(player, chosen_ability.spellLevel)
            self.perform_attack(player, opponent, chosen_ability)
            action_used = True

        # Reset temporary advantage/disadvantage at end of turn
        if player.hasAdvantage:
            player.hasAdvantage = False
        if player.hasDisadvantage:
            player.hasDisadvantage = False

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
    
    def has_sneak_attack(self, player):
        abilities = self.player_abilities.get(player.characterID, [])
        return any(ability.abilityName.lower() == 'sneak attack' for ability in abilities)

    def perform_heal(self, player, ally, ability):
        # Perform a heal based on the chosen ability
        heal_type = ability.meleeRangedAOE.lower()

        if heal_type == 'melee':
            # Melee heal: single target, must be in melee range
            distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if distance <= 1.5:
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += ((player.mainScore - 10) // 2)
                oldHp = ally.hp
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                if ally.hp > 0 and ally.deathSaves:  # Reset death saves if healed
                    ally.deathSaves = {'success': 0, 'failure': 0}
                print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 
                player.numHeals -= 1

        elif heal_type == 'ranged':
            # Ranged heal: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if distance <= (ability.rangeOne // 5):
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += ((player.mainScore - 10) // 2)
                oldHp = ally.hp
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                if ally.hp > 0 and ally.deathSaves:  # Reset death saves if healed
                    ally.deathSaves = {'success': 0, 'failure': 0}
                print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 
                player.numHeals -= 1

        elif heal_type == 'aoe':
            # AOE heal: heals allies within the given radius
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team
            for ally in ally_team:
                distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
                if distance <= (ability.radius // 5):
                    heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1)) 
                    if ability.secondNumDice is not None:
                        heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                    heal_amount += ((player.mainScore - 10) // 2)
                    oldHp = ally.hp
                    ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                    if ally.hp > 0 and ally.deathSaves:  # Reset death saves if healed
                        ally.deathSaves = {'success': 0, 'failure': 0}
                    print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 
                    player.numHeals -= 1
        else:
            print(f"Unknown heal type: {heal_type}")
                  
            
    def move_character(self, player):
        
        enemy_team = self.foes if player in self.friends else self.friends
        target = self.find_closest_enemy(player, enemy_team)
        
        if not target:
            return  # No enemies left
        
        distance = self.calculate_distance(player.xloc, player.yloc, target.xloc, target.yloc)
        max_movement = player.movementSpeed // 5  # Speed in feet, grid is 5 ft per square
        if player in self.friends:
            if player.hp >= 0 and player.hp <= player.hpMax / 2:
                if distance < 5:  
                    self.move_away(player, target, max_movement)
                else:
                    print(f"{player.characterName} stays at range.")
            else:  
                self.move_towards(player, target, max_movement)
        # Men go in        
        elif player in self.foes:
            self.move_towards(player, target, max_movement)



    def perform_attack(self, player, opponent, ability):
        # Perform an attack based on the chosen ability
        attack_type = ability.meleeRangedAOE.lower() 

        if attack_type == 'melee':
            # Melee attack: single target, must be in melee range
            distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if distance <= 1.5:
                if player.hasAdvantage and not player.hasDisadvantage:
                    attack_roll = self.roll_with_advantage() + ((player.mainScore - 10) // 2)
                elif player.hasDisadvantage and not player.hasAdvantage:
                    attack_roll = self.roll_with_disadvantage() + ((player.mainScore - 10) // 2)
                else:  # Normal roll or both advantage and disadvantage cancel out
                    attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)

                if attack_roll >= opponent.ac:
                    damage = self.calculate_damage(ability, player)
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and (player.hasAdvantage or self.is_ally_adjacent_to_enemy(player, opponent))):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName}!") 

        elif attack_type == 'ranged':
            # Ranged attack: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if distance <= (ability.rangeOne // 5):
                if player.hasAdvantage and not player.hasDisadvantage:
                    attack_roll = self.roll_with_advantage() + ((player.mainScore - 10) // 2)
                elif player.hasDisadvantage and not player.hasAdvantage:
                    attack_roll = self.roll_with_disadvantage() + ((player.mainScore - 10) // 2)
                else:  # Normal roll or both advantage and disadvantage cancel out
                    attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2)

                if attack_roll >= opponent.ac:
                    damage = self.calculate_damage(ability, player)
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and (player.hasAdvantage or self.is_ally_adjacent_to_enemy(player, opponent))):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                        
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName}!")

            elif ability.rangeTwo is not None and (distance <= (ability.rangeTwo // 5)):
                player.hasDisadvantage = True
                if player.hasAdvantage:
                    attack_roll = self.roll_dice(1, 20) + ((player.mainScore - 10) // 2) # If player has advantage, cancels out
                else:
                    attack_roll = self.roll_with_disadvantage() + ((player.mainScore - 10) // 2) # Attacks at long range with disadvantage

                if attack_roll >= opponent.ac:
                    damage = self.calculate_damage(ability, player)
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and self.is_ally_adjacent_to_enemy(player, opponent)):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                        
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName} at long range! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName} at long range!")

        elif attack_type == 'aoe':
            # AOE attack: targets enemies, but allies in the radius are also affected
            enemy_team = self.foes if player in self.friends else self.friends  # Determine enemy team
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team

            base_damage = self.calculate_damage(ability, player)

            for enemy in enemy_team:
                if enemy.hp > 0:  # Only target alive enemies
                    distance = self.calculate_distance(player.xloc, player.yloc, enemy.xloc, enemy.yloc)
                    if distance <= (ability.radius // 5):
                        if ability.saveType: 
                            save_modifier = self.get_save_modifier(enemy, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier  # Enemy's saving throw
                            if save_roll >= ((player.mainScore - 10) // 2) + 10:  # Enemy succeeds on the save
                                damage = base_damage // 2  # Half damage on save
                            else:  # Enemy fails the save
                                damage = base_damage
                        else:  # No saving throw required
                            damage = base_damage
                        oldHp = enemy.hp
                        enemy.hp -= damage
                        if enemy.hp < 0: enemy.hp = 0
                        print(f"{player.characterName} attacks {enemy.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {enemy.hp}") 

            # Then, check for allies in the radius and apply effects if necessary
            for ally in ally_team:
                if ally.hp > 0 and ally != player:  # Only target alive allies
                    distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
                    if distance <= ability.radius:
                        if ability.saveType:  # If the AOE requires a saving throw
                            # Determine the appropriate saving throw modifier based on ability.saveType
                            save_modifier = self.get_save_modifier(ally, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier  # Ally's saving throw
                            if save_roll >= ((player.mainScore - 10) // 2) + 10:  # Ally succeeds on the save
                                damage = base_damage // 2  # Half damage on save
                            else:  # Ally fails the save
                                damage = base_damage
                        else:  # No saving throw required
                            damage = base_damage
                        oldHp = ally.hp
                        ally.hp -= damage
                        if ally.hp < 0: ally.hp = 0
                        print(f"Oops! {player.characterName} attacks {ally.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 

        else:
            print(f"Unknown attack type: {attack_type}")

    def calculate_distance(self, x1, y1, x2, y2):
        # Calculate the distance between two points using Euclidean distance
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    
    def find_closest_enemy(self, player, enemy_team):
        alive_enemies = [enemy for enemy in enemy_team if enemy.hp > 0]
        if not alive_enemies:
            return None
        return min(alive_enemies, key=lambda enemy: self.calculate_distance(player.xloc, player.yloc, enemy.xloc, enemy.yloc))
    
    def move_towards(self, player, target, max_movement):
        occupied_positions = {(p.xloc, p.yloc) for p in self.friends + self.foes if p != player}
        dx = target.xloc - player.xloc
        dy = target.yloc - player.yloc
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        for _ in range(max_movement):
            new_x = player.xloc + step_x
            new_y = player.yloc + step_y
            
            # Ensure new position stays within bounds
            new_x = max(1, min(new_x, self.grid_xdim))
            new_y = max(1, min(new_y, self.grid_ydim))

            if (new_x, new_y) in occupied_positions:
                break 
            
            # Only move if we're getting closer
            old_dist = self.calculate_distance(player.xloc, player.yloc, target.xloc, target.yloc)
            new_dist = self.calculate_distance(new_x, new_y, target.xloc, target.yloc)
            
            if new_dist < old_dist:
                player.xloc = new_x
                player.yloc = new_y
            else:
                break
        
        print(f"{player.characterName} moves towards {target.characterName}. Now at ({player.xloc}, {player.yloc}).")

    def move_away(self, player, target, max_movement):
        occupied_positions = {(p.xloc, p.yloc) for p in self.friends + self.foes if p != player}
        dx = player.xloc - target.xloc
        dy = player.yloc - target.yloc
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        for _ in range(max_movement):
            new_x = player.xloc + step_x
            new_y = player.yloc + step_y
            
            # Ensure new position stays within bounds
            new_x = max(1, min(new_x, self.grid_xdim ))
            new_y = max(1, min(new_y, self.grid_ydim))

            if (new_x, new_y) in occupied_positions:
                break 
            
            # Only move if we're actually moving away (not hitting boundaries)
            if (new_x != player.xloc) or (new_y != player.yloc):
                player.xloc = new_x
                player.yloc = new_y
        
        print(f"{player.characterName} moves away from {target.characterName}. Now at ({player.xloc}, {player.yloc}).")

    def is_ally_adjacent_to_enemy(self, player, opponent):
        ally_team = self.friends if player in self.friends else self.foes
        for ally in ally_team:
            if ally != player and ally.hp > 0:  # Don't count yourself and only alive allies
                distance = self.calculate_distance(ally.xloc, ally.yloc, opponent.xloc, opponent.yloc)
                if 0 < distance <= 1.5:  # Adjacent but not same space (1.5 covers diagonal distances)
                    return True
        return False

    def check_flanking(self, player, opponent):
        if player.hasDisadvantage:
            return False  # Disadvantage cancels flanking advantage
        
        ally_team = self.friends if player in self.friends else self.foes
        
        # Find all living allies in melee range of opponent
        potential_flankers = [
            ally for ally in ally_team 
            if ally != player and ally.hp > 0 and 
            abs(ally.xloc - opponent.xloc) <= 1 and 
            abs(ally.yloc - opponent.yloc) <= 1
        ]
        
        for ally in potential_flankers:
            # Calculate relative positions
            player_dx = player.xloc - opponent.xloc
            player_dy = player.yloc - opponent.yloc
            ally_dx = ally.xloc - opponent.xloc
            ally_dy = ally.yloc - opponent.yloc
            
            # Check if player and ally are on opposite sides
            # Either x-axis opposite or y-axis opposite
            if ((player_dx * ally_dx < 0 and abs(player_dy) <= 1 and abs(ally_dy) <= 1) or   # Opposite x
                (player_dy * ally_dy < 0 and abs(player_dx) <= 1 and abs(ally_dx) <= 1) or   # Opposite y
                (player_dx * ally_dx < 0 and player_dy * ally_dy < 0)):                      # Opposite diagonal
                return True
        
        return False

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
    
    def roll_with_advantage(self):
        roll1 = self.roll_dice(1, 20)
        roll2 = self.roll_dice(1, 20)
        return max(roll1, roll2)

    def roll_with_disadvantage(self):
        roll1 = self.roll_dice(1, 20)
        roll2 = self.roll_dice(1, 20)
        return min(roll1, roll2)