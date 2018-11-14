# # --- Culture ---
# #
# # - Cultures, and manipulations of culture
# #
# # --- --- --- ---


from Language import *
from random import randint
from copy import copy


class Culture:
    def __init__(self, origin, lang=None, subLanguages=None):
        self.language = lang if lang else Language()
        self.subLanguages = subLanguages if subLanguages else []
        self.name = self.language['PEOPLE']
        self.color = [randint(0, 255) for i in range(3)]

        self.idealTemp = origin.temp
        self.idealAltitude = origin.altitude

        self.agriculturalist = origin.fertility
        self.birthRate = 0.05 + 0.05 * random()  # Rate - 1
        self.migratory = random() * 0.3 + 0.1
        self.explorative = random()
        self.hardiness = random()
        self.tolerance = random()

    def diverge(self, origin):
        pass
