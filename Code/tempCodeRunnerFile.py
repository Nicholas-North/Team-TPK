def run_simulation(self):
        for i in range(self.num_simulations):
            fresh_players = copy.deepcopy(self.selected_players)  # Ensure players are fresh each run
            simulation = CombatSimulation(fresh_players)  # Pass fresh copies
            winner = simulation.run_round()
            self.results[winner] += 1
            print(f"Simulation {i + 1}: Winner - {winner}")

        self.display_results()