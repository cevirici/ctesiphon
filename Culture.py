# # --- Culture ---
# #
# # - Cultures, and manipulations of culture
# #
# # --- --- --- ---


from Language import *
from random import randint


class Trait:
    # Traits govern how Cultures behave.
    def __init__(self, name, formal, tMin, tMax, tVar):
        self.name = name
        self.formal = formal
        self.range = [tMin, tMax]
        self.variance = tVar

    def __hash__(self):
        return hash(self.name)

    def cap(self, value):
        # Caps a value within the range of this trait
        return max(self.range[0], min(self.range[1], value))

    def randomize(self):
        # Generate a random value for this trait
        return self.range[0] + random() * (self.range[1] - self.range[0])

    def jiggle(self, value):
        # Given an initial value, "jiggle" it a bit
        return self.cap((2 * random() - 1) * self.variance + value)


class Culture:
    cultures = set()
    AGRICULTURALIST = Trait('Agriculturalist', 'AGRI', 0, 1, 0.1)
    BIRTHRATE = Trait('Birth Rate', 'BIRTHS', 0.03, 0.15, 0.02)
    MIGRATORY = Trait('Nomadic', 'MIGRATE', 0.1, 0.4, 0.05)
    EXPLORATIVE = Trait('Explorative', 'EXPLORE', 0.2, 0.8, 0.07)
    HARDINESS = Trait('Adaptible', 'HARDINESS', 0, 0.5, 0.05)
    TOLERANT = Trait('Tolerant', 'TOLERANCE', 0, 1, 0.1)

    def __init__(self, origin, lang=None, subLanguages=None):
        self.origin = origin
        self.language = lang if lang else Language()
        self.subLanguages = subLanguages if subLanguages else []
        self.name = self.language['PEOPLE']
        self.color = [randint(0, 255) for i in range(3)]

        self.idealTemp = origin.temp
        self.idealAltitude = origin.altitude

        self.traits = {}

        self.traits[Culture.AGRICULTURALIST] = origin.fertility
        self.traits[Culture.BIRTHRATE] = Culture.BIRTHRATE.randomize()
        self.traits[Culture.MIGRATORY] = Culture.MIGRATORY.randomize()
        self.traits[Culture.EXPLORATIVE] = Culture.EXPLORATIVE.randomize()
        self.traits[Culture.HARDINESS] = Culture.HARDINESS.randomize()
        self.traits[Culture.TOLERANT] = Culture.TOLERANT.randomize()

        self.subCultures = []

        Culture.cultures.add(self)

    def __getitem__(self, item):
        for trait in self.traits:
            if trait.formal == item:
                return self.traits[trait]

    def __setitem__(self, item, value):
        for trait in self.traits:
            if trait.formal == item:
                self.traits[trait] = value

    def diverge(self, origin):
        # Generate a child culture centered around another province
        child = Culture(origin, self.language, self.subLanguages)
        child.color = [self.color[i] + randint(14, 18) * choice([1, -1])
                       for i in range(3)]
        for i in range(3):
            child.color[i] = min(255, max(0, child.color[i]))

        for trait in self.traits:
            child.traits[trait] = trait.jiggle(self.traits[trait])

        # Come up with possible names
        prefixes = ['OF']
        if origin.temp < self.idealTemp:
            prefixes.append('ICE')
        if origin.temp > self.idealTemp:
            prefixes.append('DESERT')
        if origin.altitude > self.idealAltitude:
            prefixes.extend(['MOUNTAIN', 'HILL'])
        if origin.altitude < self.idealAltitude:
            prefixes.append('GRASS')
        if origin.center[0] > self.origin.center[0]:
            prefixes.append('EAST')
        if origin.center[0] < self.origin.center[0]:
            prefixes.append('WEST')
        if origin.center[1] > self.origin.center[1]:
            prefixes.append('SOUTH')
        if origin.center[1] < self.origin.center[1]:
            prefixes.append('NORTH')

        allNames = [c.name for c in Culture.cultures]
        prefix = choice(prefixes)
        child.name = mergeWords(self.language[prefix], self.name)
        while prefixes and child.name in allNames:
            prefixes.remove(prefix)
            prefix = choice(prefixes)
            child.name = mergeWords(self.language[prefix], self.name)

        if not prefixes:
            child.name = self.language.generateWord()

        self.subCultures.append(child)
        return child

    def reform(self, origin):
        # Adapt the culture to be closer to the origin of the reform
        self.idealTemp = (self.idealTemp + origin.temp) / 2
        self.idealAltitude = (self.idealAltitude + origin.altitude) / 2
        self['AGRI'] = (self['AGRI'] + origin.fertility) / 2
