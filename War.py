# # --- War ---
# #
# # - Contains the War class, which handles instances of war.
# #
# # --- --- --- ---


class War:
    wars = set()

    def __init__(self, wargoal):
        self.attackers = []
        self.defenders = []
        self.belligerents = []
        self.warGoal = wargoal
        self.warscore = 0
        self.initialStates = {}

        War.wars.add(self)
