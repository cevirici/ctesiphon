# # --- Disaster ---
# #
# # - Disasters and their effects
# #
# # --- --- --- ---

from random import random, choice
from Buildings import buildings


class Disaster:
    def __init__(self, name, onTick, baseDuration):
        self.name = name
        self.onTick = onTick
        self.baseDuration = baseDuration

    def tick(self, city):
        self.onTick(city)


def fireTick(city):
    city.disasters['Fire'] -= 1
    if random() < city.wetness:
        city.disasters['Fire'] -= 1
    if random() > city.vegetation:
        city.disasters['Fire'] -= 1

    for culture in city.cultures:
        city.cultures[culture] *= 0.9

    city.population = sum([city.cultures[c] for c in city.cultures])

    city.progress -= city.currentBuilding.requirement / 10
    if city.progress < 0:
        if city.buildings:
            target = choice(list(city.buildings))
            for building in buildings:
                if building.name == target:
                    building.destroy(city)
            city.buildings.remove(target)
            city.progress = city.currentBuilding.requirement / 2
        else:
            city.progress = 0

    # Spread
    if random() > 0.85:
        targets = [n for n in city.neighbors if 'Fire' not in n.disasters and
                   n.temp > 0.4 and not n.isSea()]
        if targets:
            target = choice(targets)
            target.disasters['Fire'] = fire.baseDuration


def hurricaneTick(city):
    if city.disasters['Hurricane'] > 0:
        targets = [n for n in city.neighbors if 'Hurricane' not in n.disasters]
        if targets:
            target = choice(targets)
            target.disasters['Hurricane'] = -city.disasters['Hurricane'] + 1

        for culture in city.cultures:
            city.cultures[culture] *= 0.60

        city.population = sum([city.cultures[c] for c in city.cultures])

        city.progress -= city.currentBuilding.requirement / 2
        if city.progress < 0:
            if city.buildings:
                target = choice(list(city.buildings))
                for building in buildings:
                    if building.name == target:
                        building.destroy(city)
                city.buildings.remove(target)
                city.progress = city.currentBuilding.requirement / 2
            else:
                city.progress = 0
        city.disasters['Hurricane'] = 0
    elif city.disasters['Hurricane'] < 0:
        city.disasters['Hurricane'] = -city.disasters['Hurricane']


fire = Disaster('Fire', fireTick, 12)
hurricane = Disaster('Hurricane', hurricaneTick, 15)
disasters = [fire, hurricane]
