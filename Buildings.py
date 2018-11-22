# # --- Buildings ---
# #
# # - Contains all the buildings to be built, in order
# #
# # --- --- --- ---

from Polity import *


class Building:
    def __init__(self, name, requirement, onBuild, onDestroy):
        self.name = name
        self.requirement = requirement
        self.onBuild = onBuild
        self.onDestroy = onDestroy

    def build(self, city):
        self.onBuild(city)

    def onDestroy(self, city):
        self.onDestroy(city)


# Building list

buildings = []


def build1Action(city):
    city.capacity *= 2
    city.farmEff += 0.01


def build1Destroy(city):
    city.capacity /= 2
    city.farmEff -= 0.01


buildings.append(Building('Simple Farm', 200, build1Action, build1Destroy))


def build2Action(city):
    city.capacity *= 2


def build2Destroy(city):
    city.capacity /= 2


buildings.append(Building('Huts', 300, build2Action, build2Destroy))


def build3Action(city):
    city.builderMax *= 4


def build3Destroy(city):
    city.builderMax /= 4


buildings.append(Building('Lumber Yard', 600, build3Action, build3Destroy))


def potteryAction(city):
    city.storageEff *= 1.5


def potteryDestroy(city):
    city.storageEff /= 1.5


buildings.append(Building('Pottery', 800, potteryAction, potteryDestroy))


def irrigAction(city):
    city.capacity *= 2
    city.farmEff += 0.02
    if city.cityLevel == 0:
        city.cityLevel = 1


def irrigDestroy(city):
    city.capacity /= 2
    city.farmEff -= 0.02


buildings.append(Building('Basic Irrigation', 1200, irrigAction, irrigDestroy))


def build5Action(city):
    city.builderMax *= 2.5


def build5Destroy(city):
    city.builderMax /= 2.5


buildings.append(Building('Quarry', 1600, build5Action, build5Destroy))


def build6Action(city):
    city.capacity *= 1.4


def build6Destroy(city):
    city.capacity /= 1.4


buildings.append(Building('Farmlands', 2000, build6Action, build6Destroy))


def siloAction(city):
    city.storageEff *= 1.8
    city.capacity *= 1.1


def siloDestroy(city):
    city.storageEff /= 1.8
    city.capacity /= 1.1


buildings.append(Building('Silos', 2200, siloAction, siloDestroy))


def build7Action(city):
    city.capacity *= 1.2
    if city.cityLevel == 1:
        city.cityLevel = 2
    city.garrisonMax = 50
    city.builderMax *= 1.5

    city.polity = Polity(city, city.polity)


def build7Destroy(city):
    city.capacity /= 1.2
    city.builderMax /= 1.5


buildings.append(Building('Fort', 400, build7Action, build7Destroy))


def housingAction(city):
    city.capacity *= 2
    city.builderMax *= 2


def housingDestroy(city):
    city.capacity /= 2
    city.builderMax /= 2


buildings.append(Building('Housing', 9000, housingAction, housingDestroy))


def raxAction(city):
    city.garrisonMax *= 3


def raxDestroy(city):
    city.garrisonMax /= 3


buildings.append(Building('Barracks', 12000, raxAction, raxDestroy))


def robotAction(city):
    city.capacity *= 1.4


def robotDestroy(city):
    city.capacity /= 1.4


buildings.append(Building('Giant Robot', 10000000, robotAction, robotDestroy))
