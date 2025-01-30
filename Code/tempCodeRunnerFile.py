def perform_actions(self, player, opponent):
        print(f"\n{player.name}'s turn:")

    # Check if the opponent is still alive
        if opponent.hit_points <= 0:
            print(f"{opponent.name} is already defeated!")
        
        # Choose a new target if the opponent is dead
            if player == self.solo_player:
            # If the solo player is attacking and the current team player is dead, switch target
                new_target = self.team_players[0] if self.team_players[1].hit_points <= 0 else self.team_players[1]
                print(f"{player.name} will now attack {new_target.name}.")
                opponent = new_target
            else:
            # If team players are attacking and the solo player is dead, skip attack
                print(f"{player.name} has no valid opponent to attack.")
                return  # Skip the attack if no valid opponent

        action_choices = ["melee_attack", "heal_self"]
        action = random.choice(action_choices)

        if action == "melee_attack":
            melee_attack_template = self.templates[3]
            print(f"{player.name} chooses action: {melee_attack_template.name}")
            melee_attack_template.print_template()
            self.resolve_attack(player, opponent, "Melee Attack")

        elif action == "heal_self" and player.can_heal == 1 and player.num_heals > 0 and player.hit_points < player.hit_point_max:
            heal_template = self.templates[5]
            print(f"{player.name} chooses to heal!")
            heal_template.print_template()
            self.resolve_heal(player)
            print(f"{player.num_heals} heals left")

        elif action == "heal_self" and (player.can_heal == 0 or player.num_heals < 1 or player.hit_points == player.hit_point_max):
            melee_attack_template = self.templates[3]
            print(f"{player.name} chooses action: {melee_attack_template.name}")
            melee_attack_template.print_template()
            self.resolve_attack(player, opponent, "Melee Attack")

            if player.multi_attack == 1:
                print(f"{player.name} performs a second attack!")
                self.resolve_attack(player, opponent, "Melee Attack")