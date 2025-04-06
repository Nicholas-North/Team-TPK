import random
from enum import Enum
from collections import defaultdict
import pyodbc
from multiprocessing import Pool
import copy
from multiprocessing import Manager
import math

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
        self.grid_xdim, self.grid_ydim, self.randomPosition = self.fetch_encounter_dimensions(encounter_id)
        
        # Initialize MVP tracking
        self.mvp_points = defaultdict(int)  # Tracks total points across all simulations
        self.mvp_counts = defaultdict(int)  # Tracks how many times each player was MVP

        # Fetch all player abilities
        self.player_abilities = self.fetch_all_player_abilities()
        
        # Precompute original stats for resetting players
        self.original_stats = {}
        for p in self.friends + self.foes:
            numHeals = sum(1 for ability in self.player_abilities.get(p.characterID, []) if ability.healTag == 1)
            self.original_stats[p.characterName] = {
                "hp": p.hp, 
                "numHeals": numHeals,
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
            
            query = "SELECT xdim, ydim, randomPosition FROM encounter.encounter WHERE encounterID = ?"
            cursor.execute(query, (encounter_id,))  # Note the comma for single-element tuple
            
            result = cursor.fetchone()
            if result:
                return result.xdim, result.ydim, bool(result.randomPosition)
            return 15, 15, False  # Default dimensions if no result found
            
        except Exception as e:
            print(f"Error fetching encounter dimensions: {str(e)}")
            return 15, 15, False  # Return defaults on error
        finally:
            if db_connection:
                db_connection.close()

    def fetch_all_player_abilities(self):
        db_connection = create_db_connection()  # Create a temporary connection
        cursor = db_connection.cursor()
        abilities = {}
        cursor.execute("""
            SELECT ca.characterID, am.abilityID, am.abilityName, am.meleeRangedAOE, am.healTag, am.itemToHitBonus,
                am.firstNumDice, am.firstDiceSize, am.firstDamageType, am.secondNumDice, 
                am.secondDiceSize, am.secondDamageType, am.rangeOne, am.rangeTwo, 
                am.radius, am.coneLineSphere, am.spellLevel, am.saveType, am.actionType
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
        manager = Manager()
        results = manager.list()
        round_counts = manager.list()
        mvp_points_list = manager.list()

        simulation_data = {
            "friends": self.friends,
            "foes": self.foes,
            "player_abilities": self.player_abilities,
            "original_stats": self.original_stats,
            "grid_xdim": self.grid_xdim,
            "grid_ydim": self.grid_ydim,
            "randomPosition": self.randomPosition 
        }

        if (len(self.friends) + len(self.foes)) > (self.grid_xdim * self.grid_ydim):
            return 0, 0, 0, "Error: Not Enough Space!"

        with Pool() as pool:
            pool.starmap(run_single_simulation, 
                        [(simulation_data, results, round_counts, mvp_points_list) 
                         for _ in range(self.num_simulations)])

        # Aggregate results
        for winner in results:
            self.results[winner] += 1

        if round_counts:
            self.total_rounds = sum(round_counts) / len(round_counts)
            
        # Aggregate MVP points
        for mvp_dict in mvp_points_list:
            for player_name, points in mvp_dict.items():
                self.mvp_points[player_name] += points
                
        # Determine MVP for this batch of simulations
        if self.mvp_points:
            max_points = max(self.mvp_points.values())
            mvps = [name for name, points in self.mvp_points.items() if points == max_points]
            for mvp in mvps:
                self.mvp_counts[mvp] += 1

        print(f"Random Position value: {self.randomPosition}")        
        self.display_results()

    def display_results(self):
        # Retrieve wins from the results dictionary (defaulting to 0 if not present)
        friends_wins = self.results.get("Friends Win", 0)
        foes_wins = self.results.get("Foes Win", 0)

        # Determine overall MVP (player with most MVP counts)
        overall_mvp =  max(self.mvp_counts.items(), key=lambda x: x[1])[0] if self.mvp_counts else None

        # Return the win counts so you can send them back to the database
        return friends_wins, foes_wins, self.total_rounds, overall_mvp

def run_single_simulation(simulation_data, results, round_counts, mvp_points_list):
    # Deep copy the players to avoid data bleed
    friends = copy.deepcopy(simulation_data["friends"])
    foes = copy.deepcopy(simulation_data["foes"])
    player_abilities = simulation_data["player_abilities"]
    original_stats = simulation_data["original_stats"]
    grid_xdim = simulation_data.get("grid_xdim", 15)  # Default to 15 if not provided
    grid_ydim = simulation_data.get("grid_ydim", 15)  # Default to 15 if not provided
    randomPosition = simulation_data.get("randomPosition")

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

    simulation = CombatSimulation(friends, foes, player_abilities, grid_xdim, grid_ydim, randomPosition)
    result = simulation.run_round()
    if result is None:
        result = ("Stalemate", 0, {})
    winner, numRounds, mvp_points = result
    results.append(winner)
    round_counts.append(numRounds)
    mvp_points_list.append(mvp_points)

class CombatSimulation:
    def __init__(self, friends, foes, player_abilities, grid_xdim=15, grid_ydim=15, randomPosition=False):
        self.friends = friends
        self.foes = foes
        self.player_abilities = player_abilities
        self.grid_xdim = grid_xdim
        self.grid_ydim = grid_ydim
        self.mvp_points = defaultdict(int) 
        
        if randomPosition == True: 
            self.initialize_positions()
        self.turn_order, self.initiative_rolls = self.roll_initiative(friends + foes)
        self.print_initiative_order()

    def award_mvp_point(self, player):
        if player in self.friends:  # Only award to friendly players
            self.mvp_points[player.characterName] += 1

    def take_mvp_point(self, player):
        if player in self.friends:  # Only take from friendly players
            self.mvp_points[player.characterName] -= 1      

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
        # Randomly assign starting grid positions with minimum distance
        positions = set()
        min_distance = 2  # Minimum distance between characters
        
        for player in self.friends + self.foes:
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                x = random.randint(1, self.grid_xdim)
                y = random.randint(1, self.grid_ydim)
                
                # Check distance from all other positions
                valid_position = True
                for (px, py) in positions:
                    if self.calculate_distance(x, y, px, py) < min_distance:
                        valid_position = False
                        break
                
                if valid_position or not positions:  # First position is always valid
                    player.xloc, player.yloc = x, y
                    positions.add((x, y))
                    break
                    
                attempts += 1
            
            if attempts >= 50:
                # Fallback to any position if can't find valid one
                while True:
                    x = random.randint(1, self.grid_xdim)
                    y = random.randint(1, self.grid_ydim)
                    if (x, y) not in positions:
                        player.xloc, player.yloc = x, y
                        positions.add((x, y))
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
        max_iterations = 25  # Prevent infinite loops
        iteration = 0

        while any(p.hp > 0 for p in self.friends) and any(p.hp > 0 for p in self.foes):
            iteration += 1
            if iteration > max_iterations:
                print("Stalemate :/")
                return ("Stalemate", 0, dict(self.mvp_points))
            
            # Iterate through the turn_order list once per round
            for player in self.turn_order:
                if player.hp > 0:  # If Player is Alive
                    enemy_team = self.foes if player in self.friends else self.friends
                    alive_enemies = [p for p in enemy_team if p.hp > 0]
                    if alive_enemies:
                        # Get all enemies in range of any ability
                        enemies_in_range = []
                        abilities = self.player_abilities.get(player.characterID, [])
                        
                        for enemy in alive_enemies:
                            for ability in abilities:
                                if self.is_ability_in_range(player, enemy, ability):
                                    enemies_in_range.append(enemy)
                                    break  # Only need to find one ability that can reach
                        
                        # If no enemies in range, try to find closest enemy
                        if not enemies_in_range:
                            target = min(alive_enemies, key=lambda e: self.calculate_distance(player.xloc, player.yloc, e.xloc, e.yloc))
                        else:
                            # Prioritize enemies by: lowest HP -> bloodied -> random in range
                            lowest_hp = min(e.hp for e in enemies_in_range)
                            lowest_hp_enemies = [e for e in enemies_in_range if e.hp == lowest_hp]
                            
                            if len(lowest_hp_enemies) > 1:
                                # If multiple with same low HP, check for bloodied
                                bloodied = [e for e in lowest_hp_enemies if e.hp <= e.hpMax / 2]
                                if bloodied:
                                    target = random.choice(bloodied)
                                else:
                                    target = random.choice(lowest_hp_enemies)
                            else:
                                target = lowest_hp_enemies[0]

                        action_result = self.perform_actions(player, target)
                        if action_result in ["Friends Win", "Foes Win"]:
                            if action_result == "Friends Win": print("Friends Win! :D \n")
                            elif action_result == "Foes Win": print("Foes Win :( \n")
                            return action_result, iteration, dict(self.mvp_points)
                        elif all(p.hp <= 0 for p in enemy_team):
                            if enemy_team == self.foes:
                                print("Friends Win! :D \n")
                                return "Friends Win", iteration, dict(self.mvp_points)
                            else:
                                print("Foes Win! :( \n")
                                return "Foes Win", iteration, dict(self.mvp_points)
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
                            action_result = self.perform_actions(player, target)
                            if action_result in ["Friends Win", "Foes Win"]:
                                return action_result, iteration, dict(self.mvp_points)
                            elif all(p.hp <= 0 for p in enemy_team):
                                if enemy_team == self.foes:
                                    return "Friends Win", iteration, dict(self.mvp_points)
                                else:
                                    return "Foes Win", iteration, dict(self.mvp_points)
                else:
                    print(f"{player.characterName} is unconscious or dead and cannot take a turn.")
            # End of round
            print("End of round.\n")

        # Stalemate Handling
        print("Stalemate :/")
        return ("Stalemate", 0, dict(self.mvp_points))
                            
    def handle_death_saves(self, player):
        # Perform a death save
        death_save_roll = self.roll_dice(1, 20)
        if death_save_roll == 20:
            # Critical success: regain 1 HP
            self.award_mvp_point(player)
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
            # player.xloc = 10000
            # player.yloc = 10000
            print(f"{player.characterName} has died...")
        return False  # Indicate that the player cannot take their turn

    def perform_actions(self, player, opponent):
        
        target_enemy = opponent
        ally_team = self.friends if player in self.friends else self.foes
        enemy_team = self.foes if player in self.friends else self.friends
        abilities = self.player_abilities.get(player.characterID, [])
        
        if not abilities:
            return None

        # Precompute all usable abilities (considering spell slots)
        usable_abilities = []
        for ability in abilities:
            if ability.spellLevel is None or ability.spellLevel == 0:
                usable_abilities.append(ability)
            elif ability.spellLevel is not None and self.has_spell_slot(player, ability.spellLevel):
                usable_abilities.append(ability)

        if not usable_abilities:
            return None

        # Check for alive enemies
        alive_enemies = [e for e in enemy_team if e.hp > 0]
        if not alive_enemies:
            return None

        # Initialize action tracking
        action_used = False
        bonus_action_used = False
        movement_used = False

        # ===== HEALING PRIORITY LOGIC =====
        healing_abilities = [a for a in usable_abilities if a.healTag == 1]
        injured_allies = [ally for ally in ally_team if ((ally.hp <= ally.hpMax / 2) and (ally.hp >= 0))]  # Exclude dead allies

        # 1. Check for Second Wind self-heal (bonus action)
        if (player.hp <= player.hpMax / 2 and not bonus_action_used and player.numHeals > 0):
            second_wind = next((a for a in healing_abilities if a.abilityName.lower() == 'second wind'), None)
            if second_wind:
                self.perform_heal(player, player, second_wind)
                bonus_action_used = True
                player.numHeals -= 1

        # 2. Priority healing for allies
        if (healing_abilities and injured_allies and player.numHeals > 0 and not (action_used and bonus_action_used)):
            # Find all healable allies (in range of any healing ability)
            healable_allies = []
            for ally in injured_allies:
                for ability in healing_abilities:
                    if (ability.abilityName.lower() != 'second wind' and self.is_ability_in_range(player, ally, ability)):
                        healable_allies.append((ally, ability))
                        break  # Only need one valid ability per ally
            
            if healable_allies:
                # Sort by most wounded first
                healable_allies.sort(key=lambda x: x[0].hp)
                target_ally, healing_ability = healable_allies[0]
                
                # Determine action type
                if (healing_ability.actionType.lower() == "bonus" and not bonus_action_used):
                    if healing_ability.spellLevel is not None and healing_ability.spellLevel > 0:
                        self.expend_spell_slot(player, healing_ability.spellLevel)
                    self.perform_heal(player, target_ally, healing_ability)
                    bonus_action_used = True
                    
                elif (healing_ability.actionType.lower() == "action" and 
                    not action_used):
                    if healing_ability.spellLevel is not None and healing_ability.spellLevel > 0:
                        self.expend_spell_slot(player, healing_ability.spellLevel)
                    self.perform_heal(player, target_ally, healing_ability)
                    action_used = True

        # 3. Move toward injured allies if needed
        if (injured_allies and ([a for a in healing_abilities if a.abilityName.lower() != 'second wind']) and player.numHeals > 0 and not (action_used and bonus_action_used)):
            closest_injured = min(injured_allies, key=lambda a: self.calculate_distance(player.xloc, player.yloc, a.xloc, a.yloc))
            
            current_dist = self.calculate_distance(player.xloc, player.yloc, closest_injured.xloc, closest_injured.yloc)
            
            # Only move if not already adjacent and would get us closer
            if self.melee_range(player, ally, ability):
                old_pos = (player.xloc, player.yloc)
                self.move_towards(player, closest_injured, player.movementSpeed//5)
                if (player.xloc, player.yloc) != old_pos:
                    print(f"{player.characterName} moves toward injured ally {closest_injured.characterName}")

        # ===== OFFENSIVE ACTIONS =====
        # Get all offensive abilities
        offensive_abilities = []
        for a in usable_abilities:
            if a.healTag == 0 and a.actionType.lower() in ["action", "bonus"]:
                # Calculate damage potential (dice count * dice size)
                damage_potential = 0
                if a.firstNumDice is not None and a.firstDiceSize is not None:
                    damage_potential += a.firstNumDice * a.firstDiceSize
                if a.secondNumDice is not None and a.secondDiceSize is not None:
                    damage_potential += a.secondNumDice * a.secondDiceSize
                offensive_abilities.append((a, damage_potential))

        # Sort abilities by damage potential (highest first)
        offensive_abilities.sort(key=lambda x: x[1], reverse=True)
        offensive_abilities = [a[0] for a in offensive_abilities]  # Remove damage scores

        melee_count = sum(1 for ab in offensive_abilities if ab.meleeRangedAOE.lower() == 'melee')
        has_mostly_melee = (len(offensive_abilities) > 0 and melee_count > len(offensive_abilities) // 2)


        # Check if any offensive abilities are in range
        has_offensive_in_range = any(
            self.is_ability_in_range(player, target_enemy, ability)
            for ability in offensive_abilities
        )

        # Check range conditions for optimal positioning
        range_one_abilities = [a for a in offensive_abilities if a.rangeOne is not None and a.rangeOne > 0]
        range_two_abilities = [a for a in offensive_abilities if a.rangeTwo is not None and a.rangeTwo > 0]

        # Move to optimal range if needed
        if (range_one_abilities and 
            not any(self.is_ability_in_range(player, target_enemy, a) for a in range_one_abilities)):
            # Move to be within rangeOne of at least one ability
            old_pos = (player.xloc, player.yloc)
            current_dist = self.calculate_distance(player.xloc, player.yloc, target_enemy.xloc, target_enemy.yloc)
            max_range = max(a.rangeOne // 5 for a in range_one_abilities)
            spaces_to_close = max(0, current_dist - max_range)
            movement_amount = min(player.movementSpeed // 5, spaces_to_close)
            self.move_towards(player, target_enemy, movement_amount)
            if (player.xloc, player.yloc) != old_pos:
                movement_used = True
                # Check if we're now in range of any ability
                if any(self.is_ability_in_range(player, target_enemy, a) for a in range_one_abilities):
                    print(f"{player.characterName} moves into optimal attack range")

        # Default movement if no range conditions apply or we're out of range
        elif not has_offensive_in_range or (has_mostly_melee and not self.melee_range(player, target_enemy, ability)):
            old_pos = (player.xloc, player.yloc)
            move_result = self.move_character(player, target_enemy)
            if move_result in ["Friends Win", "Foes Win"]:
                return move_result
            if (player.xloc, player.yloc) != old_pos:
                movement_used = True

        # Try bonus actions first (prioritizing higher damage)
        if not bonus_action_used:
            bonus_actions = [a for a in offensive_abilities if a.actionType.lower() == "bonus"]
            
            valid_bonus_actions = []
            for ability in bonus_actions:
                if ability.abilityName.lower() == "hide":
                    # Keep Hide and dash as valid options but with lower priority
                    valid_bonus_actions.append((ability, 6 * player.charLevel))  # Sneak attack damage potential
                elif self.is_ability_in_range(player, target_enemy, ability):
                    # Calculate damage potential for sorting
                    damage_potential = 0
                    if ability.firstNumDice is not None and ability.firstDiceSize is not None:
                        damage_potential += ability.firstNumDice * ability.firstDiceSize
                    if ability.secondNumDice is not None and ability.secondDiceSize is not None:
                        damage_potential += ability.secondNumDice * ability.secondDiceSize
                    valid_bonus_actions.append((ability, damage_potential))
            
            if valid_bonus_actions:
                # Separate dash and hide from other bonus actions
                dash_ability = next((a for a in valid_bonus_actions if a[0].abilityName.lower() == 'dash'), None)
                hide_ability = next((a for a in valid_bonus_actions if a[0].abilityName.lower() == 'hide'), None)
                other_actions = [a for a in valid_bonus_actions if a[0].abilityName.lower() not in ['dash', 'hide']]

                # Decision logic
                if has_offensive_in_range:
                    # Prefer hide when in range of attacks
                    if hide_ability:
                        chosen_ability = hide_ability[0]
                        active_enemies = [e for e in enemy_team if e.hp > 0]
                        if active_enemies:
                            avg_perception = sum((e.wisScore - 10) // 2 + 10 for e in active_enemies) // len(active_enemies)
                            stealth_roll = self.roll_dice(1, 20) + ((player.dexScore - 10) // 2)
                            if stealth_roll > avg_perception:
                                player.hasAdvantage = True
                                print(f"{player.characterName} successfully hides (Stealth: {stealth_roll} vs Perception: {avg_perception}) and gains advantage!")
                            else:
                                print(f"{player.characterName} fails to hide (Stealth: {stealth_roll} vs Perception: {avg_perception})")
                    elif other_actions:
                        # Choose highest damage non-dash/hide ability
                        chosen_ability = max(other_actions, key=lambda x: x[1])[0]
                        if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                            self.expend_spell_slot(player, chosen_ability.spellLevel)
                        
                        if chosen_ability.meleeRangedAOE.lower() == 'melee' and self.check_flanking(player, target_enemy):
                            player.hasAdvantage = True
                            print(f"{player.characterName} gains advantage from flanking!")
                        
                        self.perform_attack(player, target_enemy, chosen_ability)
                else:
                    # Out of range - prefer dash to close distance
                    if dash_ability:
                        chosen_ability = dash_ability[0]
                        old_pos = (player.xloc, player.yloc)
                        move_result = self.move_character(player, target_enemy)
                        if move_result in ["Friends Win", "Foes Win"]:
                            return move_result
                        if (player.xloc, player.yloc) != old_pos:
                            print(f"{player.characterName} bonus action dashes toward enemy {target_enemy.characterName}")   
                
                bonus_action_used = True

        # Then standard actions (prioritizing higher damage)
        if not action_used:
            actions = []
            recharge_actions = []
            
            # Check for Multiattack feature and get count
            multiattack_count = 1  # Default to 1 attack
            for ability in offensive_abilities:
                if ability.abilityName.lower().startswith('multiattack'):
                    try:
                        multiattack_count = int(ability.abilityName.lower().split('multiattack')[-1].strip())
                        break
                    except (ValueError, IndexError):
                        multiattack_count = 2
                        break
            
            # Find all valid attack actions
            for ability in offensive_abilities:
                if (ability.actionType.lower() == "action" and (self.is_ability_in_range(player, target_enemy, ability) or self.melee_range(player, target_enemy, ability)) and not ability.abilityName.lower().startswith('multiattack')):
                    
                    # Skip spell attacks if using Multiattack
                    if multiattack_count > 1 and (ability.spellLevel is not None):
                        continue
                        
                    # Calculate damage potential
                    damage_potential = 0
                    if ability.firstNumDice is not None and ability.firstDiceSize is not None:
                        damage_potential += ability.firstNumDice * ability.firstDiceSize
                    if ability.secondNumDice is not None and ability.secondDiceSize is not None:
                        damage_potential += ability.secondNumDice * ability.secondDiceSize
                    
                    # Separate recharge abilities
                    if "recharge" in ability.abilityName.lower():
                        recharge_actions.append((ability, damage_potential))
                    else:
                        actions.append((ability, damage_potential))
            
            # Decide whether to use recharge ability or normal attacks
            if recharge_actions:
                # Sort recharge actions by damage potential
                recharge_actions.sort(key=lambda x: x[1], reverse=True)
                best_recharge = recharge_actions[0][0]
                
                # Roll for recharge (assuming 5-6 recharge like most abilities)
                recharge_roll = self.roll_dice(1, 6)
                if recharge_roll >= 5:  # Recharge succeeds
                    print(f"{player.characterName} recharges {best_recharge.abilityName} (rolled {recharge_roll})!")
                    if best_recharge.spellLevel is not None and best_recharge.spellLevel > 0:
                        self.expend_spell_slot(player, best_recharge.spellLevel)
                    
                    if best_recharge.meleeRangedAOE.lower() == 'melee' and self.check_flanking(player, target_enemy):
                        player.hasAdvantage = True
                        print(f"{player.characterName} gains advantage from flanking!")

                    self.perform_attack(player, target_enemy, best_recharge)
                    action_used = True
                else:
                    print(f"{player.characterName} fails to recharge {best_recharge.abilityName} (rolled {recharge_roll})")
                    # Fall through to normal attacks
            
            if not action_used and actions:
                # Sort by damage potential (highest first)
                actions.sort(key=lambda x: x[1], reverse=True)
                chosen_ability = actions[0][0]
                
                # Handle spell slots if needed (only relevant when not using Multiattack)
                if chosen_ability.spellLevel is not None and chosen_ability.spellLevel > 0:
                    self.expend_spell_slot(player, chosen_ability.spellLevel)
                
                # Execute attacks
                for attack_num in range(multiattack_count if chosen_ability.spellLevel is None else 1):
                    # Check flanking for melee attacks
                    if chosen_ability.meleeRangedAOE.lower() == 'melee' and self.check_flanking(player, target_enemy):
                        player.hasAdvantage = True
                        print(f"{player.characterName} gains advantage from flanking!")

                    if target_enemy.hp <= 0:  # Stop if target dies
                        break

                    self.perform_attack(player, target_enemy, chosen_ability)
                    player.hasAdvantage = False
                
                action_used = True
            elif not action_used:
                if self.melee_range(player, target_enemy, ability):
                    print(f"{player.characterName} has no valid actions against {target_enemy.characterName} (in melee range)")
                else:
                    print(f"{player.characterName} has no valid actions against {target_enemy.characterName} (out of range)")
                    
        # Final fallback movement if nothing else worked
        if not action_used and not movement_used:
            old_pos = (player.xloc, player.yloc)
            move_result = self.move_character(player, opponent)
            if move_result in ["Friends Win", "Foes Win"]:
                return move_result
            if (player.xloc, player.yloc) != old_pos:
                movement_used = True

        # Reset temporary advantage/disadvantage
        player.hasAdvantage = False
        player.hasDisadvantage = False

        print(f"End {player.characterName} turn.")

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


    # ===== PLAYER HEALING LOGIC =====
    def perform_heal(self, player, ally, ability):

        modifier = self.get_ability_modifier(player)

        # Perform a heal based on the chosen ability
        if ability.meleeRangedAOE.lower() is not None:
            heal_type = ability.meleeRangedAOE.lower()

        if heal_type == 'melee':
            # Melee heal: single target, must be in melee range
            distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if self.melee_range(player, ally, ability):
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += modifier
                oldHp = ally.hp
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                if ally.hp > 0 and ally.deathSaves:  # Reset death saves if healed
                    ally.deathSaves = {'success': 0, 'failure': 0}
                if oldHp == 0:
                    self.award_mvp_point(player)
                print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 
                player.numHeals -= 1

        elif heal_type == 'ranged':
            # Ranged heal: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if distance <= (ability.rangeOne // 5):
                heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))
                if ability.secondNumDice is not None:
                    heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                heal_amount += modifier
                oldHp = ally.hp
                ally.hp = min(ally.hpMax, ally.hp + heal_amount)
                if ally.hp > 0 and ally.deathSaves:  # Reset death saves if healed
                    ally.deathSaves = {'success': 0, 'failure': 0}
                if oldHp == 0:
                    self.award_mvp_point(player)
                print(f"{player.characterName} heals {ally.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}") 
                player.numHeals -= 1

        elif heal_type == 'aoe':
            # AOE heal: heals allies within the given radius
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team
            if ability.coneLineSphere is not None:
                aoe_shape = getattr(ability, 'coneLineSphere', 'Sphere').lower()
            
            # Check if target opponent is within range
            target_distance = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
            if target_distance > (ability.rangeOne // 5):
                print(f"{ally.characterName} is out of range for {ability.abilityName}!")
                return
            
            if aoe_shape == 'sphere':
                center_x, center_y = ally.xloc, ally.yloc

            for friend in ally_team:
                distance_to_player = self.calculate_distance(player.xloc, player.yloc, friend.xloc, friend.yloc)
                in_aoe = False
                    
                if aoe_shape == 'sphere':
                    distance_to_center = self.calculate_distance(center_x, center_y, ally.xloc, ally.yloc)
                    if distance_to_center <= (ability.radius // 5):
                        in_aoe = True
                            
                elif aoe_shape == 'cone':
                    if distance_to_player <= (ability.rangeOne // 5):
                        angle = self.calculate_angle(player.xloc, player.yloc, ally.xloc, ally.yloc, friend.xloc, friend.yloc)
                        if abs(angle) <= 60:
                            in_aoe = True
                                
                elif aoe_shape == 'line':
                    if distance_to_player <= (ability.rangeOne // 5):
                        if self.is_in_line(player.xloc, player.yloc, ally.xloc, ally.yloc, friend.xloc, friend.yloc):
                            in_aoe = True
                    
                if in_aoe:
                    heal_amount = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1)) 
                    if ability.secondNumDice is not None:
                        heal_amount += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
                    heal_amount += modifier
                    oldHp = friend.hp
                    friend.hp = min(friend.hpMax, friend.hp + heal_amount)
                    if friend.hp > 0 and friend.deathSaves:  # Reset death saves if healed
                        friend.deathSaves = {'success': 0, 'failure': 0}
                    if oldHp == 0:
                        self.award_mvp_point(player)
                    print(f"{player.characterName} heals {friend.characterName} for {heal_amount} using {ability.abilityName}! Health goes from {oldHp} to {friend.hp}") 
                    player.numHeals -= 1
        else:
            print(f"Unknown heal type: {heal_type}")


    # ===== ATTACK LOGIC =====
    def perform_attack(self, player, opponent, ability):

        modifier = self.get_ability_modifier(player)

        # Perform an attack based on the chosen ability
        if ability.meleeRangedAOE.lower() is not None:
            attack_type = ability.meleeRangedAOE.lower() 
        is_critical = False

        if attack_type == 'melee':
            # Melee attack: single target, must be in melee range
            distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if self.melee_range(player, opponent, ability):
                if player.hasAdvantage and not player.hasDisadvantage:
                    attack_roll = self.roll_with_advantage()
                elif player.hasDisadvantage and not player.hasAdvantage:
                    attack_roll = self.roll_with_disadvantage()
                else:  # Normal roll or both advantage and disadvantage cancel out
                    attack_roll = self.roll_dice(1, 20) 

                if attack_roll == 20:
                    is_critical = True
                
                attack_roll += modifier + player.proficiencyBonus + ability.itemToHitBonus

                if attack_roll >= opponent.ac:
                    if is_critical == True:
                        damage = self.calculate_crit(ability, player)
                        print(f"Wowza!! {player.characterName} lands a critical attack!!")
                    else:
                        damage = self.calculate_damage(ability, player)
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and (player.hasAdvantage or self.is_ally_adjacent_to_enemy(player, opponent))):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        if is_critical: sneak_damage += self.roll_dice(sneak_attack_dice, 6) # Sneak attack damage also doubled on a crit
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    if opponent.hp == 0:
                        self.award_mvp_point(player)
                        # opponent.xloc = 10000
                        # opponent.yloc = 10000
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName}!") 

        elif attack_type == 'ranged':
            # Ranged attack: single target, must be within range
            distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if distance <= (ability.rangeOne // 5):
                if abs(player.xloc - opponent.xloc) <= 1 and abs(player.yloc - opponent.yloc) <= 1: # If target is in direct melee range, ranged attacks are at disadvantage 
                    player.hasDisadvantage = True # Attacks at long range with disadvantage
                    print(f"Too close! {player.characterName} is attacking at disadvantage!")

                if player.hasAdvantage and not player.hasDisadvantage:
                    attack_roll = self.roll_with_advantage()
                elif player.hasDisadvantage and not player.hasAdvantage:
                    attack_roll = self.roll_with_disadvantage()
                else:  # Normal roll or both advantage and disadvantage cancel out
                    attack_roll = self.roll_dice(1, 20) 

                if attack_roll == 20:
                    is_critical = True

                attack_roll += modifier + player.proficiencyBonus + ability.itemToHitBonus

                if attack_roll >= opponent.ac:
                    if is_critical == True:
                        damage = self.calculate_crit(ability, player) + player.proficiencyBonus
                        print(f"Wowza!! {player.characterName} lands a critical attack!!")
                    else:
                        damage = self.calculate_damage(ability, player) + player.proficiencyBonus
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and ((player.hasAdvantage and not player.hasDisadvantage) or self.is_ally_adjacent_to_enemy(player, opponent))):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        if is_critical: sneak_damage += self.roll_dice(sneak_attack_dice, 6) # Sneak attack damage also doubled on a crit
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                        
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    if opponent.hp == 0:
                        self.award_mvp_point(player)
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName}!")

            elif ability.rangeTwo is not None and (distance <= (ability.rangeTwo // 5)):
                player.hasDisadvantage = True
                if player.hasAdvantage:
                    attack_roll = self.roll_dice(1, 20) # If player has advantage, cancels out
                else:
                    attack_roll = self.roll_with_disadvantage() 

                if attack_roll == 20:
                    is_critical = True

                attack_roll += modifier + player.proficiencyBonus + ability.itemToHitBonus

                if attack_roll >= opponent.ac:
                    if is_critical == True:
                        damage = self.calculate_crit(ability, player) + player.proficiencyBonus
                        print(f"Wowza!! {player.characterName} lands a critical attack!!")
                    else:
                        damage = self.calculate_damage(ability, player) + player.proficiencyBonus
                    # Checks to see if the player has sneak attack
                    if (self.has_sneak_attack(player) and self.is_ally_adjacent_to_enemy(player, opponent)):
                        sneak_attack_dice = max(1, (player.charLevel) // 2)  # Ensure at least 1 die
                        sneak_damage = self.roll_dice(sneak_attack_dice, 6)
                        if is_critical: sneak_damage += self.roll_dice(sneak_attack_dice, 6) # Sneak attack damage also doubled on a crit
                        damage += sneak_damage
                        print(f"{player.characterName} lands a Sneak Attack for an additional {sneak_damage} damage!")
                        
                    oldHp = opponent.hp
                    opponent.hp -= damage
                    if opponent.hp < 0: opponent.hp = 0
                    if opponent.hp == 0:
                        self.award_mvp_point(player)
                    print(f"{player.characterName} attacks {opponent.characterName} for {damage} using {ability.abilityName} at long range! Health goes from {oldHp} to {opponent.hp}")
                else:
                    print(f"{player.characterName} misses {opponent.characterName} using {ability.abilityName} at long range!")

        elif attack_type == 'aoe':
            # AOE attack: targets enemies, but allies in the radius are also affected
            enemy_team = self.foes if player in self.friends else self.friends  # Determine enemy team
            ally_team = self.friends if player in self.friends else self.foes  # Determine ally team
            base_damage = self.calculate_damage(ability, player)
            
            # Get AOE shape if specified (default to sphere if not specified)
            if ability.coneLineSphere is not None:
                aoe_shape = getattr(ability, 'coneLineSphere', 'Sphere').lower()
            
            # Check if target opponent is within range
            target_distance = self.calculate_distance(player.xloc, player.yloc, opponent.xloc, opponent.yloc)
            if target_distance > (ability.rangeOne // 5):
                print(f"{opponent.characterName} is out of range for {ability.abilityName}!")
                return
            
            if aoe_shape == 'sphere':
                center_x, center_y = opponent.xloc, opponent.yloc
            
            # Process enemies
            for enemy in enemy_team:
                if enemy.hp > 0:  # Only target alive enemies
                    distance_to_player = self.calculate_distance(player.xloc, player.yloc, enemy.xloc, enemy.yloc)
                    in_aoe = False
                    
                    if aoe_shape == 'sphere':
                        # Sphere centered on target opponent
                        distance_to_center = self.calculate_distance(center_x, center_y, opponent.xloc, opponent.yloc)
                        if distance_to_center <= (ability.radius // 5):
                            in_aoe = True
                            
                    elif aoe_shape == 'cone':
                        # Cone originating from player towards target opponent
                        if distance_to_player <= (ability.rangeOne // 5):
                            # Calculate angle between player->target and player->enemy
                            angle = self.calculate_angle(player.xloc, player.yloc, opponent.xloc, opponent.yloc, enemy.xloc, enemy.yloc)
                            if abs(angle) <= 60:  # 60 degree cone (30 degrees on each side)
                                in_aoe = True
                                
                    elif aoe_shape == 'line':
                        # Line from player through target opponent
                        if distance_to_player <= (ability.rangeOne // 5):
                            # Check if enemy is in the line between player and target (with some width)
                            if self.is_in_line(player.xloc, player.yloc, opponent.xloc, opponent.yloc, enemy.xloc, enemy.yloc):
                                in_aoe = True
                    
                    if in_aoe:
                        if ability.saveType: 
                            save_modifier = self.get_save_modifier(enemy, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier
                            if save_roll >= modifier + 10:
                                damage = base_damage // 2
                            else:
                                damage = base_damage
                        else:
                            damage = base_damage
                        oldHp = enemy.hp
                        enemy.hp -= damage
                        if enemy.hp < 0: enemy.hp = 0
                        if enemy.hp == 0:
                            self.award_mvp_point(player)
                        print(f"{player.characterName} attacks {enemy.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {enemy.hp}") 

            # Process allies (similar logic but with different targeting)
            for ally in ally_team:
                if ally.hp > 0 and ally != player:  # Only target alive allies
                    distance_to_player = self.calculate_distance(player.xloc, player.yloc, ally.xloc, ally.yloc)
                    in_aoe = False
                    
                    if aoe_shape == 'sphere':
                        distance_to_center = self.calculate_distance(center_x, center_y, ally.xloc, ally.yloc)
                        if distance_to_center <= (ability.radius // 5):
                            in_aoe = True
                            
                    elif aoe_shape == 'cone':
                        if distance_to_player <= (ability.rangeOne // 5):
                            angle = self.calculate_angle(player.xloc, player.yloc, opponent.xloc, opponent.yloc,ally.xloc, ally.yloc)
                            if abs(angle) <= 60:
                                in_aoe = True
                                
                    elif aoe_shape == 'line':
                        if distance_to_player <= (ability.rangeOne // 5):
                            if self.is_in_line(player.xloc, player.yloc, opponent.xloc, opponent.yloc, ally.xloc, ally.yloc):
                                in_aoe = True
                    
                    if in_aoe:
                        if ability.saveType:
                            save_modifier = self.get_save_modifier(ally, ability.saveType)
                            save_roll = self.roll_dice(1, 20) + save_modifier
                            if save_roll >= modifier + 10:
                                damage = base_damage // 2
                            else:
                                damage = base_damage
                        else:
                            damage = base_damage
                        oldHp = ally.hp
                        ally.hp -= damage
                        if ally.hp < 0: ally.hp = 0
                        if ally.hp == 0:
                            self.take_mvp_point(player)
                        print(f"Oops! {player.characterName} attacks {ally.characterName} for {damage} using {ability.abilityName}! Health goes from {oldHp} to {ally.hp}")

        else:
            print(f"Unknown attack type: {attack_type}")


    # ===== DISTANCE AND RANGE FUNCTIONS =====
    def calculate_distance(self, x1, y1, x2, y2):
        # Manhattan distance for grid-based movement
        return abs(x2 - x1) + abs(y2 - y1)
    
    def calculate_angle(self, origin_x, origin_y, target_x, target_y, point_x, point_y):
        vec1_x = target_x - origin_x
        vec1_y = target_y - origin_y
        vec2_x = point_x - origin_x
        vec2_y = point_y - origin_y
        
        dot_product = vec1_x * vec2_x + vec1_y * vec2_y
        magnitude1 = (vec1_x**2 + vec1_y**2)**0.5
        magnitude2 = (vec2_x**2 + vec2_y**2)**0.5
        
        if magnitude1 * magnitude2 == 0:
            return 0
        cos_angle = dot_product / (magnitude1 * magnitude2)
        angle = math.degrees(math.acos(max(-1, min(1, cos_angle))))  # Clamp to avoid floating point errors
        return angle

    def is_in_line(self, start_x, start_y, end_x, end_y, point_x, point_y, line_width=1.0):
        # Vector from start to end
        line_vec_x = end_x - start_x
        line_vec_y = end_y - start_y
        
        # Vector from start to point
        point_vec_x = point_x - start_x
        point_vec_y = point_y - start_y
        
        # Calculate projection of point_vec onto line_vec
        line_length_sq = line_vec_x**2 + line_vec_y**2
        if line_length_sq == 0:
            return False  # Line has no length
            
        projection = (point_vec_x * line_vec_x + point_vec_y * line_vec_y) / line_length_sq
        
        # If projection is outside [0,1], point is not within the line segment
        if projection < 0 or projection > 1:
            return False
        
        # Calculate closest point on line to the point
        closest_x = start_x + projection * line_vec_x
        closest_y = start_y + projection * line_vec_y
        
        # Calculate distance from point to line
        distance = self.calculate_distance(point_x, point_y, closest_x, closest_y)
        
        return distance <= line_width
    
    def find_closest_enemy(self, player, enemy_team):
        alive_enemies = [enemy for enemy in enemy_team if enemy.hp > 0]
        if not alive_enemies:
            return None
        return min(alive_enemies, key=lambda enemy: self.calculate_distance(player.xloc, player.yloc, enemy.xloc, enemy.yloc))
    
    def is_ability_in_range(self, player, target, ability):
        distance = self.calculate_distance(player.xloc, player.yloc, target.xloc, target.yloc)
        if ability.meleeRangedAOE is not None:
            attack_type = ability.meleeRangedAOE.lower()
        else: 
            return False
        if ability.coneLineSphere is not None:
            aoe_shape = getattr(ability, 'coneLineSphere', 'sphere').lower()

        if attack_type == 'melee':
            return self.melee_range(player, target, ability)

        range_one = ability.rangeOne // 5 if ability.rangeOne else 0
        range_two = ability.rangeTwo // 5 if ability.rangeTwo else 0
        
        if ability.meleeRangedAOE.lower() == 'ranged':
            return distance <= range_one or (range_two and distance <= range_two)
        
        if attack_type == 'aoe':
            range_one = ability.rangeOne // 5 if ability.rangeOne is not None else 0
            
            # Check if within maximum range
            if distance > range_one:
                return False
                
            # Sphere AOE (radius around caster)
            if aoe_shape == 'sphere':
                radius = ability.radius // 5 if ability.radius is not None else 0
                return distance <= radius
                
            # Cone AOE (60 degree arc)
            elif aoe_shape == 'cone':
                angle = self.calculate_angle(
                    player.xloc, player.yloc,
                    player.xloc + 1, player.yloc,  # Reference direction (east)
                    target.xloc, target.yloc
                )
                return abs(angle) <= 30  # 30 degrees each side
                
            # Line AOE (straight path)
            elif aoe_shape == 'line':
                return self.is_in_line(
                    player.xloc, player.yloc,
                    player.xloc + (target.xloc - player.xloc) * 2,  # Extend line
                    player.yloc + (target.yloc - player.yloc) * 2,
                    target.xloc, target.yloc
                )
            
    def melee_range(self, attacker, enemy, ability):
        if ability.rangeOne is None or ability.rangeOne == 0:
            ability.rangeOne = 5

        # Checks if attacker is in melee range
        dx = abs(attacker.xloc - enemy.xloc)
        dy = abs(attacker.yloc - enemy.yloc)
        return dx <= ability.rangeOne // 5 and dy <= ability.rangeOne // 5

    def is_ally_adjacent_to_enemy(self, player, opponent):
        ally_team = self.friends if player in self.friends else self.foes
        for ally in ally_team:
            if ally != player and ally.hp > 0:  # Don't count yourself and only alive allies
                if abs(ally.xloc - opponent.xloc) <= 1 and abs(ally.yloc - opponent.yloc) <= 1:
                    return True
        return False

    def check_flanking(self, player, opponent):
        if player.hasDisadvantage:
            return False
        
        # Verify melee range
        if abs(player.xloc - opponent.xloc) > 1 or abs(player.yloc - opponent.yloc) > 1:
            return False
        
        ally_team = self.friends if player in self.friends else self.foes
        
        # Find all living allies in melee range of opponent
        potential_flankers = [
            ally for ally in ally_team 
            if ally != player and ally.hp > 0 and abs(ally.xloc - opponent.xloc) <= 1 and abs(ally.yloc - opponent.yloc) <= 1
        ]

        if not potential_flankers:
            return False
        
        # Check for strict opposite positioning
        for ally in potential_flankers:
            # Get grid deltas (relative positions to enemy)
            player_dx = player.xloc - opponent.xloc
            player_dy = player.yloc - opponent.yloc
            ally_dx = ally.xloc - opponent.xloc
            ally_dy = ally.yloc - opponent.yloc
            
            # Check if positions are directly opposite
            if (player_dx == -ally_dx and player_dy == -ally_dy):
                return True
            
            # For diagonal positions, check if they form a line through the enemy
            if (abs(player_dx) == 1 and abs(player_dy) == 1 and 
                abs(ally_dx) == 1 and abs(ally_dy) == 1):
                # Check if the vectors point in opposite directions
                if (player_dx == -ally_dx and player_dy == -ally_dy):
                    return True
        
        return False


    # ===== MOVEMENT FUNCTIONS =====
    def move_character(self, player, target_enemy):
        ally_team = self.friends if player in self.friends else self.foes
        
        # Check if player is the last conscious member of their team
        conscious_allies = [ally for ally in ally_team if ally != player and ally.hp > 0]
        
        # If no target enemy (shouldn't happen but defensive programming)
        if not target_enemy:
            return None
        
        old_x, old_y = player.xloc, player.yloc
        distance = self.calculate_distance(player.xloc, player.yloc, target_enemy.xloc, target_enemy.yloc)
        max_movement = player.movementSpeed // 5  # Speed in feet, grid is 5 ft per square
        
        # Determine movement strategy
        if not conscious_allies and player in self.friends and player.hp <= player.hpMax / 3:
            # Last conscious friend - 50/50 chance to flee or fight
            if random.random() < 0.5:  # Flee
                print(f"{player.characterName} chooses to flee from combat!")
                player.hp = 0  # Mark as dead/fled
                return "Foes Win" if player in self.friends else "Friends Win"
            else:  # Fight to the end
                self.move_towards(player, target_enemy, max_movement)
        elif player.hp > 0 and player.hp < player.hpMax / 4 and player in self.friends and distance <= 5:  # Very low health and close up
            self.move_away(player, target_enemy, max_movement)
        else:  # Normal behavior
            self.move_towards(player, target_enemy, max_movement)
        
        return None

    def move_towards(self, mover, target, max_movement):
        """Moves the unit as close to the target as possible using greedy distance minimization."""
        # If Target is within melee range
        dx = abs(mover.xloc - target.xloc)
        dy = abs(mover.yloc - target.yloc)
        if dx <= 1 and dy <= 1:
            return False

        occupied = self.get_occupied_positions()
        move_pos = self.find_best_step_towards(mover, target, max_movement, occupied)

        if move_pos and self.validate_movement(mover, move_pos[0], move_pos[1]):
            old_pos = (mover.xloc, mover.yloc)
            mover.xloc, mover.yloc = move_pos
            if (mover.xloc, mover.yloc) != old_pos:
                print(f"{mover.characterName} moves to {move_pos}")
                return True

        return False

    def find_best_step_towards(self, mover, target, max_movement, occupied):
        """Greedy search: chooses the best tile within range (including diagonals) to move closer to the target."""
        best_tile = None
        best_distance = float('inf')

        for dx in range(-max_movement, max_movement + 1):
            for dy in range(-max_movement, max_movement + 1):
                # Use Chebyshev distance for diagonals
                steps = max(abs(dx), abs(dy))
                if steps == 0 or steps > max_movement:
                    continue

                new_x, new_y = mover.xloc + dx, mover.yloc + dy

                if not (1 <= new_x <= self.grid_xdim and 1 <= new_y <= self.grid_ydim):
                    continue
                if (new_x, new_y) in occupied:
                    continue
                if not self.validate_movement(mover, new_x, new_y):
                    continue

                # Use Euclidean or Manhattan distance as heuristic — your call
                distance = abs(new_x - target.xloc) + abs(new_y - target.yloc)
                if distance < best_distance:
                    best_distance = distance
                    best_tile = (new_x, new_y)

        return best_tile

    def validate_movement(self, player, new_x, new_y):
        """Validates if a movement is safe and doesn't trap the character."""
        if not (1 <= new_x <= self.grid_xdim and 1 <= new_y <= self.grid_ydim):
            return False

        if (new_x, new_y) in self.get_occupied_positions():
            return False

        # Check for at least 2 possible exits (including diagonals now)
        exits = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nx, ny = new_x + dx, new_y + dy
            if (1 <= nx <= self.grid_xdim and
                1 <= ny <= self.grid_ydim and
                (nx, ny) not in self.get_occupied_positions()):
                exits += 1

        return exits >= 2

    def get_occupied_positions(self):
        """Returns  set  of  all  occupied  positions  on  the  grid"""
        return  {(p.xloc,  p.yloc)  for  p  in  self.friends  +  self.foes  if  p.hp  >  0  and  (p.xloc,  p.yloc)  !=  (None,  None)}

    def move_away(self, player, target, max_movement):
        occupied_positions = {(p.xloc, p.yloc) for p in self.friends + self.foes if p != player}
        original_position = (player.xloc, player.yloc)
        moved = False
        
        for _ in range(max_movement):
            # Calculate direction away from target
            dx = player.xloc - target.xloc
            dy = player.yloc - target.yloc
            
            # Determine primary movement direction (prioritize larger axis)
            if abs(dx) > abs(dy):
                step_x = 1 if dx > 0 else -1
                step_y = 0
            elif abs(dy) > abs(dx):
                step_x = 0
                step_y = 1 if dy > 0 else -1
            else:  # Equal distance, move diagonally
                step_x = 1 if dx > 0 else -1
                step_y = 1 if dy > 0 else -1
            
            # Calculate new position
            new_x = player.xloc + step_x
            new_y = player.yloc + step_y
            
            # Boundary checking
            new_x = max(1, min(new_x, self.grid_xdim))
            new_y = max(1, min(new_y, self.grid_ydim))
            
            # Check if position is occupied
            if (new_x, new_y) in occupied_positions:
                # Try alternative directions if primary is blocked
                possible_steps = [
                    (1, 0), (-1, 0), (0, 1), (0, -1),  # Orthogonal
                    (1, 1), (1, -1), (-1, 1), (-1, -1)  # Diagonal
                ]
                
                # Shuffle to randomize direction selection
                random.shuffle(possible_steps)
                
                for sx, sy in possible_steps:
                    temp_x = player.xloc + sx
                    temp_y = player.yloc + sy
                    
                    # Boundary check
                    temp_x = max(1, min(temp_x, self.grid_xdim))
                    temp_y = max(1, min(temp_y, self.grid_ydim))
                    
                    if (temp_x, temp_y) not in occupied_positions:
                        # Verify we're actually moving away
                        old_dist = self.calculate_distance(player.xloc, player.yloc,
                                                        target.xloc, target.yloc)
                        new_dist = self.calculate_distance(temp_x, temp_y,
                                                        target.xloc, target.yloc)
                        
                        if new_dist > old_dist:
                            new_x, new_y = temp_x, temp_y
                            break
                else:
                    break  # All directions blocked
            
            # Only update position if it changed
            if (new_x, new_y) != (player.xloc, player.yloc):
                player.xloc, player.yloc = new_x, new_y
                moved = True
                print(f"{player.characterName} moves away from {target.characterName}. Now at ({player.xloc}, {player.yloc})")
            else:
                break  # No valid movement

        return moved


    # ===== DAMAGE CALCULATION AND DICE ROLLING FUNCTIONS =====
    def calculate_damage(self, ability, player):
        # Calculate damage for an ability
        damage = sum(self.roll_dice(ability.firstNumDice, ability.firstDiceSize) for _ in range(1))  # Roll dice
        max_possible = ability.firstNumDice * ability.firstDiceSize
        total_num_dice = ability.firstNumDice

        if ability.secondNumDice is not None:
            damage += sum(self.roll_dice(ability.secondNumDice, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
            max_possible += ability.secondNumDice * ability.secondDiceSize
            total_num_dice += ability.secondNumDice

        modifier = self.get_ability_modifier(player)
        damage += modifier # Add main modifier to damage

        # Award MVP Point for a high damage roll
        if total_num_dice >= 2 and max_possible > 0:
            threshold = int(max_possible * 0.75)
            if (damage - modifier) >= threshold:
                self.award_mvp_point(player)

        return damage
    
    def calculate_crit(self, ability, player):
        damage = sum(self.roll_dice(ability.firstNumDice * 2, ability.firstDiceSize) for _ in range(1))  # Roll dice
        if ability.secondNumDice is not None:
            damage += sum(self.roll_dice(ability.secondNumDice * 2, ability.secondDiceSize) for _ in range(1))  # Roll additional dice
        modifier = self.get_ability_modifier(player)
        damage += modifier  # Add main modifier to damage
        return damage

    def get_ability_modifier(self, player):
        ability_scores = {
            'STR': player.strScore,
            'DEX': player.dexScore,
            'CON': player.conScore,
            'INT': player.intScore,
            'WIS': player.wisScore,
            'CHA': player.chaScore
        }
        score = ability_scores.get(player.mainScore, 10)  # Default to 10 if mainScore is invalid
        return (score - 10) // 2

    def get_save_modifier(self, enemy, save_type):
        # Get the appropriate saving throw modifier based on save_type
        save_type = save_type.lower()
        modifier = 0
        
        # Calculate base ability modifier and add proficiency if applicable
        if save_type == 'strength':
            modifier = (enemy.strScore - 10) // 2
            if hasattr(enemy, 'strSaveProf') and enemy.strSaveProf:
                modifier += enemy.proficiencyBonus
        elif save_type == 'dexterity':
            modifier = (enemy.dexScore - 10) // 2
            if hasattr(enemy, 'dexSaveProf') and enemy.dexSaveProf:
                modifier += enemy.proficiencyBonus
        elif save_type == 'constitution':
            modifier = (enemy.conScore - 10) // 2
            if hasattr(enemy, 'conSaveProf') and enemy.conSaveProf:
                modifier += enemy.proficiencyBonus
        elif save_type == 'intelligence':
            modifier = (enemy.intScore - 10) // 2
            if hasattr(enemy, 'intSaveProf') and enemy.intSaveProf:
                modifier += enemy.proficiencyBonus
        elif save_type == 'wisdom':
            modifier = (enemy.wisScore - 10) // 2
            if hasattr(enemy, 'wisSaveProf') and enemy.wisSaveProf:
                modifier += enemy.proficiencyBonus
        elif save_type == 'charisma':
            modifier = (enemy.chaScore - 10) // 2
            if hasattr(enemy, 'chaSaveProf') and enemy.chaSaveProf:
                modifier += enemy.proficiencyBonus
        
        return modifier

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