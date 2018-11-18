# # --- Polity ---
# #
# # - Political entities and their interactions
# #
# # --- --- --- ---

from Graphics import dist
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
        self.subjects = set()

        self.color = [self.culture.color[i] + randint(2, 8) * choice([1, -1])
                      for i in range(3)]
        for i in range(3):
            self.color[i] = min(255, max(0, self.color[i]))

        self.actionPoints = [0, 0, 0]
        # Expansion, Development, Research
        self.traits = [random() for i in range(3)]
        self.progress = 0

        Polity.polities.append(self)

    def superLiege(self):
        # Finds the ultimate ruler of this polity
        head = self
        while head.liege is not None:
            head = head.liege
        return head

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
                elif target.polity is None:
                    if self.influence(target) > 0.55:
                        self.territories.add(target)
                        target.polity = self
                        return

    def develop(self):
        # Develop in each territory in the polity based on influence
        for city in self.territories:
            city.infrastructure += self.influence(city) * city.population / \
                city.difficulty / 10

    def research(self):
        self.progress += self.capital.population

    def independence(self):
        # Declare independence from liege if stronger
        if self.liege:
            if self.liege.weightedPop < 2 * self.weightedPop:
                self.liege = None
                liege.subjects.discard(self)

    def tick(self):
        actions = [self.expand, self.develop, self.research]
        for i in range(len(self.actionPoints)):
            self.actionPoints[i] += 0.1

            if self.actionPoints[i] > self.traits[i]:
                self.actionPoints[i] -= self.traits[i]
                actions[i]()

        self.weightedPop = sum([c.population for c in self.territories]) + \
            sum([subject.weightedPop for subject in self.subjects]) / 2
