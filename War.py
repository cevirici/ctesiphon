# # --- War ---
# #
# # - Contains the War class, which handles instances of war.
# #
# # --- --- --- ---


class War:
    def __init__(self, wargoal):
        self.attackers = []
        self.defenders = []
        self.belligerents = []
        self.warGoal = wargoal
        self.warscore = 0

    def tick(self):
        if self.warGoal.polity in self.attackers:
            self.warscore += 1
        if self.warGoal.polity in self.defenders:
            self.warscore -= 1
