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
    BIRTHRATE = Trait('Birth Rate', 'BIRTHS', 0.04, 0.10, 0.01)
    MIGRATORY = Trait('Nomadic', 'MIGRATE', 0.1, 0.4, 0.05)
    EXPLORATIVE = Trait('Explorative', 'EXPLORE', 0.3, 0.8, 0.07)
    HARDINESS = Trait('Adaptible', 'HARDINESS', 0, 0.5, 0.05)
    TOLERANT = Trait('Tolerant', 'TOLERANCE', 0.6, 1, 0.05)
    INNOVATION = Trait('Innovative', 'INNOV', 0.4, 1, 0.1)
    MILITANCE = Trait('Militant', 'MILITANCE', 0.05, 0.65, 0.05)

    def __init__(self, origin, lang=None, subLanguages=None):
        self.origin = origin
        self.language = lang if lang else Language()
        self.subLanguages = subLanguages if subLanguages else []
        self.name = self.language['PEOPLE']
        self.color = [randint(0, 255) for i in range(3)]

        self.idealTemp = origin.temp
        self.idealAltitude = origin.altitude
        self.coastal = 1 if origin.coastal else 0

        self.traits = {}

        self.traits[Culture.AGRICULTURALIST] = origin.fertility
        for trait in [Culture.BIRTHRATE, Culture.MIGRATORY,
                      Culture.EXPLORATIVE, Culture.HARDINESS,
                      Culture.TOLERANT, Culture.INNOVATION,
                      Culture.MILITANCE]:
            self.traits[trait] = trait.randomize()

        self.subCultures = {}

        Culture.cultures.add(self)

    def __repr__(self):
        return printWord(self.name).capitalize()

    def __getitem__(self, item):
        for trait in self.traits:
            if trait.formal == item:
                return self.traits[trait]

    def __setitem__(self, item, value):
        for trait in self.traits:
            if trait.formal == item:
                self.traits[trait] = value

    def isAncestor(self, other):
        # Checks if 'other' is a descendant of this culture
        for parent in self.subCultures:
            if other in self.subCultures[parent]:
                return True
            else:
                for culture in self.subCultures[parent]:
                    if culture.isAncestor(other):
                        return True
        return False

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
        prefixes = ['OF', 'ORIGIN']
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

        def choosePrefix():
            prefix = choice(prefixes)
            prefixes.remove(prefix)
            if prefix != 'ORIGIN':
                prefix = self.language[prefix]
            else:
                prefix = origin.name
            return mergeWords(prefix, self.name)

        child.name = choosePrefix()
        while prefixes and child.name in allNames:
            child.name = choosePrefix()

        if not prefixes:
            child.name = self.language.generateWord()

        if self in self.subCultures:
            self.subCultures[self].append(child)
        else:
            self.subCultures[self] = [child]
        return child

    def merge(self, other, origin):
        # Generate a child culture with another culture
        child = Culture(origin, self.language, self.subLanguages)
        child.color = [(self.color[i] + other.color[i]) / 3 for i in range(3)]
        for i in range(3):
            child.color[i] = min(255, max(0, child.color[i]))

        for trait in self.traits:
            child.traits[trait] = (self.traits[trait] +
                                   other.traits[trait]) / 2
            child['TOLERANCE'] += random() * 0.1
            child.traits[trait] = trait.jiggle(child.traits[trait])

        child.name = mergeWords(self.name, other.name)

        if other in self.subCultures:
            self.subCultures[other].append(child)
            other.subCultures[self].append(child)
        else:
            self.subCultures[other] = [child]
            other.subCultures[self] = [child]
        return child

    def reform(self, origin):
        # Adapt the culture to be closer to the origin of the reform
        self.idealTemp = (self.idealTemp + origin.temp) / 2
        self.idealAltitude = (self.idealAltitude + origin.altitude) / 2
        self['AGRI'] = (self['AGRI'] + origin.fertility) / 2
