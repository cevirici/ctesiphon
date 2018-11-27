# # --- Polity ---
# #
# # - Political entities and their interactions
# #
# # --- --- --- ---

from Army import *
from Graphics import dist
from War import *
from random import *
from math import log


class Polity:
    polities = []

    def __init__(self, origin, liege=None):
        self.name = origin.name
        self.culture = origin.maxCulture
        self.capital = origin
        self.territories = {origin}
        self.weightedPop = 0

        self.liege = liege
        if liege:
            liege.subjects.add(self)
            liege.territories.discard(origin)
        self.subjects = set()

        self.color = [int(self.culture.color[i] + randint(10, 20) *
                          choice([1, -1]))
                      for i in range(3)]
        for i in range(3):
            self.color[i] = min(255, max(0, self.color[i]))

        self.actionPoints = [0, 0, 0]
        # Expansion, Development, Research
        self.traits = [random() for i in range(3)]
        self.militance = self.culture['MILITANCE']
        self.progress = 0

        self.relations = {}
        self.armies = set()
        self.wars = set()

        Polity.polities.append(self)

    def __hash__(self):
        return hash(self.capital)

    def superLiege(self):
        # Finds the ultimate ruler of this polity
        head = self
        while head.liege is not None:
            head = head.liege
        return head

    def isSubject(self, other):
        # Checks if self is a subject of the other polity
        if self.liege:
            if self.liege == other:
                return True
            else:
                return self.liege.isSubject(other)
        else:
            return False

    def armyCount(self):
        return sum([army.size for army in self.armies]) + \
            sum([subject.armyCount() for subject in self.subjects])

    def influence(self, city):
        # Calculates how much influence this polity has on a
        # certain city
        projection = log(self.capital.population) / 3

        if city.maxCulture is None or city.maxCulture == self.culture:
            cultureFactor = 1
        elif self.culture.isAncestor(city.maxCulture):
            cultureFactor = 0.7
        elif city.maxCulture.isAncestor(self.culture):
            cultureFactor = 0.5
        elif self.culture not in city.cultures:
            cultureFactor = 0.2
        else:
            cultureFactor = 0.2 + city.cultures[self.culture] / city.capacity

        distFactor = self.capital.radius / (dist(city.center,
                                                 self.capital.center) + 1)
        distFactor = min(1, distFactor)

        return (cultureFactor * distFactor) ** (1 / projection)

    def moveArmiesToCapital(self):
        for army in self.armies:
            if army.location != self.capital:
                if not army.instructions and not army.sleep:
                    path = army.pathfind(army.location, self.capital)
                    if path:
                        army.instructions = path
                    else:
                        army.sleep = True
            else:
                army.sleep = True

    def mergeArmies(self):
        idlers = {}
        for army in self.armies:
            if not army.instructions:
                if army.location in idlers:
                    idlers[army.location].add(army)
                else:
                    idlers[army.location] = {army}

        for city in idlers:
            if len(idlers[city]) > 1:
                newArmy = Army(city, self,
                               sum([a.size for a in idlers[city]]))
                self.armies.add(newArmy)
                city.armies.add(newArmy)
                for a in idlers[city]:
                    a.demobilize()

    # --- Individual Actions ---

    def expand(self):
        # From the center, attempt to influence a not-yet-influenced state
        queue = [self.capital]
        checked = set()

        while len(queue) > 0:
            target = queue.pop(0)
            if target not in checked:
                checked.add(target)
                if target in self.territories:
                    for n in target.neighbors:
                        if n not in checked and not n.isSea():
                            queue.append(n)
                elif self.influence(target) > 0.55:
                    if target.polity is None:
                        self.territories.add(target)
                        target.polity = self
                        return
                    else:
                        if target.polity.armyCount() < self.armyCount():
                            if not (self.isSubject(target.polity) or
                                    target.polity.isSubject(self)):
                                target.polity.demandedTerritory(target, self)
                                return

    def develop(self):
        # Develop in each territory in the polity based on influence
        for city in [self.capital]:
            city.progress += city.builders * 20 * (1 - city.vegetation) *\
                self.culture['INNOV']

    def research(self):
        self.progress += self.capital.population

    def mobilize(self, city):
        if city.polity:
            if city.garrison > 10:
                if city.polity == self or city.polity.liege == self:
                    for army in self.armies:
                        if army.location == city:
                            army.size += city.garrison
                            city.garrison = 0
                            return
                    newArmy = Army(city, city.polity, city.garrison)
                    self.armies.add(newArmy)
                    city.armies.add(newArmy)
                    city.garrison = 0
                else:
                    city.polity.requestedMobilization(city, self)

    def joinWar(self, war, side):
        if side == 0:
            war.attackers.append(self)
        else:
            war.defenders.append(self)
        war.belligerents.append(self)
        war.initialStates[self] = self.weightedPop
        self.wars.add(war)

    def generalMobilize(self):
        # Print some soldiers
        if self.armyCount() < self.weightedPop * self.militance:
            for territory in self.territories:
                self.mobilize(territory)

    # --- Interactions ---

    def shiftRelations(self, target, amount):
        if target in self.relations:
            self.relations[target] += amount
        else:
            self.relations[target] = amount
        self.relations[target] = min(1, max(-1, self.relations[target]))

    def declareWar(self, goal, enemy):
        # Check if already at war
        for activeWar in self.wars:
            if enemy in activeWar.belligerents:
                return
        newWar = War(goal)
        self.joinWar(newWar, 0)
        for subject in self.subjects:
            subject.requestedJoinWar(newWar, 0, self)

        enemy.joinWar(newWar, 1)
        for subject in enemy.subjects:
            subject.requestedJoinWar(newWar, 1, enemy)

    def independence(self):
        # Declare independence from liege if stronger
        if self.liege:
            if self.liege.armyCount() < 2 * self.armyCount():
                self.liege.subjects.discard(self)
                self.liege.declareWar(self.capital, self)
                self.liege = None

    def subjectDefected(self, subject, enemy):
        if self.armyCount() > 0.8 * enemy.armyCount():
            self.declareWar(subject.capital, enemy)

    def requestedMobilization(self, target, requester):
        # Mobilize if requested
        if requester not in self.relations or self.relations[requester] < 0.2:
            # Refuse
            requester.shiftRelations(self, -0.2)
        else:
            self.mobilize(target)
            requester.shiftRelations(self, 0.1)

    def requestedJoinWar(self, war, side, requester):
        if self not in war.belligerents:
            if requester == self.liege:
                self.joinWar(war, side)
                for subject in self.subjects:
                    subject.requestedJoinWar(war, side, self)

    def demandedTerritory(self, target, demander):
        # Count comparative strength
        if self.armyCount() > 0.8 * demander.armyCount():
            demander.declareWar(target, self)
        else:
            if target != self.capital:
                self.territories.discard(target)
                self.shiftRelations(demander, -0.8)
                demander.territories.add(target)
                target.polity = demander
            else:
                if self.liege:
                    if self.liege.armyCount() < 0.8 * demander.armyCount():
                        self.liege.subjects.remove(self)
                        self.liege.subjectDefected(self, demander)
                        self.liege = demander
                        demander.subjects.add(self)
                    else:
                        self.shiftRelations(demander, -0.8)
                else:
                    self.liege = demander
                    demander.subjects.add(self)

    def tick(self):
        actions = [self.expand, self.develop, self.research]
        for i in range(len(self.actionPoints)):
            self.actionPoints[i] += 0.1

            if self.actionPoints[i] > self.traits[i]:
                self.actionPoints[i] -= self.traits[i]
                actions[i]()

        if self.capital.maxCulture:
            self.culture = self.capital.maxCulture

        self.generalMobilize()
        if not self.wars:
            self.moveArmiesToCapital()
        self.independence()

        for army in self.armies:
            army.move()

        self.mergeArmies()

        self.weightedPop = sum([c.population for c in self.territories]) + \
            sum([subject.weightedPop for subject in self.subjects]) / 2
