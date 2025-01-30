class Player:
    def __init__(self, name="", player_class="", hit_points=0, hit_point_max = 0, armor_class=0, movement_speed=0, level=1, strength_score=10, dexterity_score=10, constitution_score=10, intelligence_score=10, wisdom_score=10, charisma_score=10, multi_attack=0, can_heal=0, num_heals=0):
        self.name = player_class  # Set the name to the class by default
        self.player_class = player_class
        self.hit_points = hit_points
        self.hit_point_max = hit_point_max
        self.armor_class = armor_class
        self.movement_speed = movement_speed
        self.level = level
        self.strength_score = strength_score
        self.dexterity_score = dexterity_score
        self.constitution_score = constitution_score
        self.intelligence_score = intelligence_score
        self.wisdom_score = wisdom_score
        self.charisma_score = charisma_score
        self.multi_attack = multi_attack 
        self.can_heal = can_heal
        self.num_heals = num_heals  
        self.melee_attack_dict = {
            "Melee Attack": (1, 6)  # Example melee attack with 1d6 damage
        }