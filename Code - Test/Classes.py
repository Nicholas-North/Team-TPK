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
                 spellLevel1, spellLevel2, spellLevel3, spellLevel4, spellLevel5, friendFoe, numDice, diceSize, xloc, yloc, bloodied, deathSaves):
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
        self.bloodied = bloodied
        self.deathSaves = deathSaves

        
        self.templates = []  # List of templates the player can use
        
    def __repr__(self):
        return (f"Player(characterID={self.characterID}, characterName={self.characterName}, "
                f"class={self.characterClass}, hp={self.hp}, hpMax={self.hpMax}, ac={self.ac}, "
                f"xloc={self.xloc}, yloc={self.yloc})")

    def add_template(self, template: Template):
        self.templates.append(template)

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
                yloc=row.yloc,   # Y-coordinate from encounterPosition
                bloodied=0,
                deathSaves=0
            )
            players.append(player)

        return players

    except pyodbc.Error as e:
        print(f"Database error occurred: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

