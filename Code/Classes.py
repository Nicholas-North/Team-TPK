import random
from enum import Enum
from typing import List, Tuple
import pyodbc


# Database connection details
DB_SERVER = 'database-1.c16m0yos4c9g.us-east-2.rds.amazonaws.com,1433'
DB_NAME = 'teamTPK'
DB_USER = 'admin'
DB_PASSWORD = 'teamtpk4vr!'


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
    def __init__(self, characterID, accountID, characterName, characterClass, ancestry, hp, hpMax, ac, movementSpeed, charLevel, mainScore,
                 strScore, dexScore, conScore, intScore, wisScore, chaScore, attackCount, canHeal, numHeals,
                 proficiencyBonus, strSaveProf, dexSaveProf, conSaveProf, intSaveProf, wisSaveProf, chaSaveProf,
                 spellLevel1, spellLevel2, spellLevel3, spellLevel4, spellLevel5, friendFoe, numDice, diceSize, xloc, yloc):
        self.characterID = characterID
        self.accountID = accountID
        self.characterName = characterName
        self.characterClass = characterClass
        self.ancestry = ancestry
        self.hp = hp
        self.hpMax = hpMax
        self.ac = ac
        self.movementSpeed = movementSpeed
        self.charLevel = charLevel
        self.mainScore = mainScore
        self.strScore = strScore
        self.dexScore = dexScore
        self.conScore = conScore
        self.intScore = intScore
        self.wisScore = wisScore
        self.chaScore = chaScore
        self.attackCount = attackCount
        self.canHeal = canHeal
        self.numHeals = numHeals
        self.proficiencyBonus = proficiencyBonus
        self.strSaveProf = strSaveProf
        self.dexSaveProf = dexSaveProf
        self.conSaveProf = conSaveProf
        self.intSaveProf = intSaveProf
        self.wisSaveProf = wisSaveProf
        self.chaSaveProf = chaSaveProf
        self.spellLevel1 = spellLevel1
        self.spellLevel2 = spellLevel2
        self.spellLevel3 = spellLevel3
        self.spellLevel4 = spellLevel4
        self.spellLevel5 = spellLevel5
        self.friendFoe = friendFoe
        self.numDice = numDice
        self.diceSize = diceSize
        self.xloc = xloc  # X-coordinate from encounterPosition
        self.yloc = yloc  # Y-coordinate from encounterPosition

        
        self.templates = []  # List of templates the player can use
        
    def __repr__(self):
        return (f"Player(characterID={self.characterID}, characterName={self.characterName}, "
                f"class={self.characterClass}, hp={self.hp}, hpMax={self.hpMax}, ac={self.ac}, "
                f"xloc={self.xloc}, yloc={self.yloc})")

    def add_template(self, template: Template):
        self.templates.append(template)

# Combat Simulation class definition
#class Classes:
    #def __init__(self):
        
      #self.templates = initialize_templates()

        
   #     self.players = [Player(), Player(), Player(), Player(), Player()]
        
        
        
    #    self.players[0].name = "Fighter"
     #   self.players[0].player_class = "Fighter"
      #  self.players[0].hit_points = 18
       # self.players[0].hit_point_max = 18
       # self.players[0].armor_class = 15
       # self.players[0].movement_speed = 6
       # self.players[0].level = 1
       # self.players[0].strength_score = 16
       # self.players[0].dexterity_score = 12
       # self.players[0].constitution_score = 14
       # self.players[0].intelligence_score = 10
       # self.players[0].wisdom_score = 8
       # self.players[0].charisma_score = 10
       # self.players[0].multi_attack = 0
       # self.players[0].can_heal = 0
        
        
        
        #self.players[1].name = "Wizard"
        #self.players[1].player_class = "Wizard"
        #self.players[1].hit_points = 10
        #self.players[1].hit_point_max = 10
        #self.players[1].armor_class = 12
        #self.players[1].movement_speed = 5
        #self.players[1].level = 1
        #self.players[1].strength_score = 8
        #self.players[1].dexterity_score = 14
        #self.players[1].constitution_score = 10
        #self.players[1].intelligence_score = 16
        #self.players[1].wisdom_score = 12
        #self.players[1].charisma_score = 10
        #self.players[1].can_heal = 0
        
        
        
        
        #self.players[2].name = "Cleric"
        #self.players[2].player_class = "Cleric"
        #self.players[2].hit_points = 14
        #self.players[2].hit_point_max = 14
        #self.players[2].armor_class = 12
        #self.players[2].movement_speed = 5
        #self.players[2].level = 1
        #self.players[2].strength_score = 12
        #self.players[2].dexterity_score = 10
        #self.players[2].constitution_score = 10
        #self.players[2].intelligence_score = 12
        #self.players[2].wisdom_score = 12
        #self.players[2].charisma_score = 16
        #self.players[2].can_heal = 1
        #self.players[2].num_heals = 2
        
        #self.players[3].name = "Rogue"
        #self.players[3].player_class = "Rogue"
        #self.players[3].hit_points = 12
        #self.players[3].hit_point_max = 12
        #self.players[3].armor_class = 12
        #self.players[3].movement_speed = 5
        #self.players[3].level = 1
        #self.players[3].strength_score = 10
        #self.players[3].dexterity_score = 16
        #self.players[3].constitution_score = 10
        #self.players[3].intelligence_score = 12
        #self.players[3].wisdom_score = 12
        #self.players[3].charisma_score = 10
        #self.players[3].can_heal = 0
        
        #self.players[4].name = "Zombie"
        #self.players[4].player_class = "Zombie"
        #self.players[4].hit_points = 22
        #self.players[4].hit_point_max = 22
        #self.players[4].armor_class = 8
        #self.players[4].movement_speed = 4
        #self.players[4].level = 1
        #self.players[4].strength_score = 12
        #self.players[4].dexterity_score = 6
        #self.players[4].constitution_score = 16
        #self.players[4].intelligence_score = 2
        #self.players[4].wisdom_score = 6
        #self.players[4].charisma_score = 4
        #self.players[4].can_heal = 0
        # 
        #  
# def create_classes():
#     players = []
    
#     # self, name="", player_class="", hit_points=0, hit_point_max = 0, armor_class=0, movement_speed=0, level=1, strength_score=10, dexterity_score=10, constitution_score=10, intelligence_score=10, wisdom_score=10, charisma_score=10, multi_attack=0, can_heal=0, num_heals=0, num_dice = 0, dice_size =0, main_score = 0, sneak_attack = 0, prof = 0, save_dc = 0, aoe_slots = 0, aoe_num_dice = 0, aoe_dice_size = 0)

#     # Player 1 - Fighter
#     players.append(Player("lvl 1 Fighter", "lvl 1 Fighter", 14, 14, 15, 6, 1, 16, 12, 14, 10, 8, 10, 0, 0, 0, 1, 10, 16, 0, 1, 0, 0, 0, 0))

#     # Player 2 - Wizard
#     players.append(Player("lvl 1 Wizard", "lvl 1 Wizard", 8, 8, 12, 5, 1, 8, 14, 10, 16, 12, 10, 0, 0, 0, 1, 10, 16, 0, 1, 0, 0, 0, 0))

#     # Player 3 - Cleric
#     players.append(Player("lvl 1 Cleric", "lvl 1 Cleric", 10, 10, 12, 5, 1, 12, 10, 10, 12, 12, 16, 0, 1, 2, 1, 8, 16, 0, 1, 0, 0, 0, 0))

#     # Player 4 - Rogue
#     players.append(Player("lvl 1 Rogue", "lvl 1 Rogue", 10, 10, 12, 5, 1, 10, 16, 10, 12, 12, 10, 0, 0, 0, 1, 4, 16, 1, 1, 0, 0, 0, 0))

#     # Player 5 - Zombie
#     players.append(Player("Zombie", "Zombie", 15, 15, 8, 4, 1, 14, 6, 16, 2, 6, 4, 1, 0, 0, 1, 8, 14, 0, 1, 0, 0, 0, 0))
    
#     players.append(Player("Tarrasque", "Tarrasque", 697, 697, 25, 12, 30, 30, 12, 30, 4, 12, 12, 3, 0, 0, 4, 8, 30, 0, 5, 20, 0, 0, 0))
    
#     players.append(Player("Owlbear", "Owlbear", 59, 59, 13, 8, 3, 20, 12, 17, 3, 12, 7, 1, 0, 0, 2, 8, 20, 0, 3, 0, 0, 0, 0))
    
#     players.append(Player("lvl 3 Fighter", "lvl 3 Fighter", 26, 26, 15, 6, 3, 16, 12, 14, 10, 8, 10, 0, 0, 0, 2, 6, 16, 0, 2, 0, 0, 0, 0))
    
    

#     return players


# Function to fetch all characters and their positions for a specific encounterID
def fetch_characters(encounter_id):
    try:
        # Establish a connection
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
        )
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        query = """
            SELECT c.characterID, c.accountID, c.characterName, c.characterClass, c.ancestry, c.hp, c.hpMax, c.ac, c.movementSpeed, c.charLevel, c.mainScore,
                   c.strScore, c.dexScore, c.conScore, c.intScore, c.wisScore, c.chaScore, c.attackCount, c.canHeal, c.numHeals,
                   c.proficiencyBonus, c.strSaveProf, c.dexSaveProf, c.conSaveProf, c.intSaveProf, c.wisSaveProf, c.chaSaveProf,
                   c.spellLevel1, c.spellLevel2, c.spellLevel3, c.spellLevel4, c.spellLevel5, c.friendFoe, c.numDice, c.diceSize,
                   ep.xloc, ep.yloc
            FROM character.character c
            INNER JOIN encounter.encounterPosition ep ON c.characterID = ep.characterID
            WHERE ep.encounterID = ?
        """
        cursor.execute(query, (encounter_id,))
        rows = cursor.fetchall()

        # Create a list of Player objects
        players = []
        for row in rows:
            player = Player(
                characterID=row.characterID,
                accountID=row.accountID,
                characterName=row.characterName,
                characterClass=row.characterClass,
                ancestry=row.ancestry,
                hp=row.hp,
                hpMax=row.hpMax,
                ac=row.ac,
                movementSpeed=row.movementSpeed,
                charLevel=row.charLevel,
                mainScore=row.mainScore,
                strScore=row.strScore,
                dexScore=row.dexScore,
                conScore=row.conScore,
                intScore=row.intScore,
                wisScore=row.wisScore,
                chaScore=row.chaScore,
                attackCount=row.attackCount,
                canHeal=row.canHeal,
                numHeals=row.numHeals,
                proficiencyBonus=row.proficiencyBonus,
                strSaveProf=row.strSaveProf,
                dexSaveProf=row.dexSaveProf,
                conSaveProf=row.conSaveProf,
                intSaveProf=row.intSaveProf,
                wisSaveProf=row.wisSaveProf,
                chaSaveProf=row.chaSaveProf,
                spellLevel1=row.spellLevel1,
                spellLevel2=row.spellLevel2,
                spellLevel3=row.spellLevel3,
                spellLevel4=row.spellLevel4,
                spellLevel5=row.spellLevel5,
                friendFoe=row.friendFoe,
                numDice=row.numDice,
                diceSize=row.diceSize,
                xloc=row.xloc,  # X-coordinate from encounterPosition
                yloc=row.yloc   # Y-coordinate from encounterPosition
            )
            players.append(player)

        return players

    except pyodbc.Error as e:
        print(f"Database error occurred: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

# Test the function
# encounter_id = 1000  # Replace with the encounterID you want to fetch
# players = fetch_characters(encounter_id)

# if players:
#     print(f"Fetched {len(players)} characters with positions for encounterID: {encounter_id}")
#     for player in players:
#         print(player)
# else:
#     print(f"No characters found for encounterID: {encounter_id}")

