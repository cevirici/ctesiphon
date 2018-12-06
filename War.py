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

    def leaveWar(self, polity):
        self.belligerents.remove(polity)
        if polity in self.attackers:
            self.attackers.remove(polity)
        else:
            self.defenders.remove(polity)
        polity.wars.remove(self)

    def checkExits(self):
        for p in self.belligerents:
            if p.weightedPop < 0.6 * self.initialStates[p]:
                self.leaveWar(p)
