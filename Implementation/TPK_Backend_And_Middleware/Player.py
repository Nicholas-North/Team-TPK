class Player:
    def __init__(self):
        # Basic Attributes
        self.name = ""  # Player's given name
        self.player_class = ""  # Cleric, Fighter, Rogue, or Wizard
        self.hit_points = 0  # Max player hit points
        self.armor_class = 0  # Base player armor class
        self.movement_speed = 0  # Player's base movement speed
        self.level = 0  # Player level (1-5)

        # Ability Scores
        self.strength_score = 0
        self.dexterity_score = 0
        self.constitution_score = 0
        self.intelligence_score = 0
        self.wisdom_score = 0
        self.charisma_score = 0

        # Attack Dictionaries
        self.melee_attack_dict = {}  # Name -> (Number of Dice, Die Size)
        self.ranged_attack_dict = {}  # Name -> (Number of Dice, Die Size)
        self.ranged_spell_attack_dict = {}  # Name -> (Number of Dice, Die Size)
        self.aoe_spell_attack_dict = {}  # Name -> (Saving Throw, Number of Dice, Die Size)

        # Spells and Effects
        self.debuff_spell_dict = {}  # Name -> (Saving Throw, Number of Dice, Die Size)
        self.spell_heal_ally = 0  # Number of HP ally heals
        self.spell_self_heal = 0  # Number of HP player heals
        self.spell_slots = {}  # Spell level -> Available slots

        # Flags
        self.bloodied_flag = False  # Player at or above max health
        self.dead_flag = False  # Player health hits 0
        self.hidden_flag = False  # Player is hidden
        self.running_flag = False  # Player is retreating
        self.advantage_flag = False  # Player has advantage

        # Position
        self.x_coordinate = 0.0  # X position on battlemap
        self.y_coordinate = 0.0  # Y position on battlemap

        # State Vector
        self.state_vector = []  # Current state of the player
