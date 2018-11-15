# # --- City ---
# #
# # - Contains the City class, and helper functions
# #
# # --- --- --- ---

from Graphics import *
from Geometry import dist
from math import ceil
from random import random

DEFAULT_NAME = "Uninhabited"
DIVERGENCE_THRESHOLD = 15


class City:
    def __init__(self, center, vertices):
        self.center = center
        self.vertices = vertices
        self.neighbors = set()
        self.radius = max([dist(self.center, v) for v in self.vertices])
        self.emigrants = []
        self.immigrants = []

        self.name = DEFAULT_NAME

        self.altitude = 0
        self.onRiver = False

        self.cultures = {}
        self.maxCulture = None
        self.population = 0
        self.divergencePressure = 0

        self.infrastructure = 0

    def __hash__(self):
        return hash(self.center)

    # --- Geography Functions ---

    def visible(self, data):
        # Returns if any part of this city is visible onscreen
        xMin = data.viewPos[0] - self.radius
        xMax = data.viewPos[0] + data.viewSize[0] / data.zoom + self.radius
        yMin = data.viewPos[1] - self.radius
        yMax = data.viewPos[1] + data.viewSize[1] / data.zoom + self.radius
        return xMin < self.center[0] < xMax and \
            yMin < self.center[1] < yMax

    def isCoastal(self):
        if self.altitude > 0:
            for neighbor in self.neighbors:
                if neighbor.altitude <= 0:
                    return True
        return False

    def isSea(self):
        return self.altitude <= 0

    def suitability(self, culture):
        # Returns the suitability of a province to a culture (affects
        # birth rate)
        altitudeFactor = 1 - abs(self.altitude - culture.idealAltitude)
        tempFactor = 1 - abs(self.temp - culture.idealTemp)
        farmFactor = 0.5 + (self.fertility - 0.5) * culture['AGRI']
        return altitudeFactor * tempFactor * farmFactor

    def attractiveness(self, culture):
        # Returns the attractiveness of some province to a culture
        altitudeFactor = 1 - abs(self.altitude - culture.idealAltitude)
        tempFactor = 1 - abs(self.temp - culture.idealTemp)
        farmFactor = self.fertility * culture['AGRI']
        if culture in self.cultures:
            popFraction = self.cultures[culture] / self.capacity
        else:
            popFraction = 0
        popFactor = popFraction * (1 - 2 * culture['EXPLORE'])
        return altitudeFactor + tempFactor + farmFactor + popFactor

    # --- Runtime Functions

    def emigrate(self):
        # Calculate emigration from this province and queues them up
        total = sum(self.cultures.values())

        # Emigrants
        if total > 0:
            for culture in self.cultures:
                # Tolerance of main culture
                if culture == self.maxCulture:
                    effCap = self.capacity
                else:
                    effCap = self.capacity * self.maxCulture['TOLERANCE']

                excess = max(total - effCap * (1 - culture['MIGRATE']), 0)
                emigrantNum = excess * self.cultures[culture] / total
                remainder = emigrantNum

                candidates = [n for n in self.neighbors if not n.isSea()]
                candidates.sort(key=lambda x: x.attractiveness(culture),
                                reverse=True)

                # Fist sweep - fill up to capacity
                for destination in candidates:
                    if remainder <= 0:
                        break
                    space = destination.capacity - destination.population
                    amount = max(0, min(space, remainder))
                    remainder -= amount
                    self.emigrants.append((culture, amount))
                    destination.immigrants.append((culture, amount))

                # Second sweep - force emigration
                i = 0
                while remainder > 0 and i < len(candidates):
                    self.emigrants.append((culture, remainder // 2))
                    candidates[i].immigrants.append((culture, remainder // 2))
                    remainder -= remainder // 2
                    i += 1

                self.emigrants.append((culture, remainder))
                candidates[0].immigrants.append((culture, remainder))

    def tick(self):
        # Births
        for culture in self.cultures:
            factor = self.suitability(culture) * (1 - culture['HARDINESS']) + \
                culture['HARDINESS']
            realRate = 1 + culture['BIRTHS'] * factor
            self.cultures[culture] *= realRate

        self.emigrate()

    def transfer(self):
        while len(self.emigrants) > 0:
            culture, amount = self.emigrants.pop()
            if culture in self.cultures:
                self.cultures[culture] -= amount
                if self.cultures[culture] < 0:
                    del self.cultures[culture]

        total = sum(self.cultures.values())
        while len(self.immigrants) > 0:
            culture, amount = self.immigrants.pop()
            if culture == self.maxCulture or total < self.capacity:
                if culture in self.cultures:
                    self.cultures[culture] += amount
                else:
                    self.cultures[culture] = amount
                total += amount

    def recalculate(self):
        # Recalculate some things
        self.population = sum(self.cultures.values())
        self.capacity = self.fertility * (1 + self.infrastructure) * 250
        if self.maxCulture:
            dpChange = (0.8 - self.suitability(self.maxCulture) ** 0.5) * \
                self.cultures[self.maxCulture] / self.capacity
            self.divergencePressure += max(0, dpChange)

    def rescale(self):
        # Rescale cultures to fit within capacity
        total = sum(self.cultures.values())
        newCultures = {}
        oldMax = self.maxCulture

        if total > 0:
            factor = min(1, self.capacity / total)
            for culture in self.cultures:
                newAmount = factor * self.cultures[culture]
                fraction = newAmount - int(newAmount)
                newAmount = int(newAmount) + (1 if random() > fraction else 0)
                if newAmount > 0:
                    newCultures[culture] = newAmount
            if newCultures:
                self.maxCulture = sorted(newCultures,
                                         key=lambda x: self.cultures[x])[-1]
            else:
                self.maxCulture = None

        self.cultures = newCultures
        if self.maxCulture != oldMax:
            self.divergencePressure = 0

    def diverge(self):
        self.divergencePressure = 0
        oldMax = self.maxCulture
        # Try a subculture, if not, make a new one
        if oldMax.subCultures:
            candidates = sorted(oldMax.subCultures,
                                key=lambda c: self.suitability(c))
            if self.suitability(candidates[-1]) > self.suitability(oldMax):
                newCulture = candidates[-1]
            else:
                newCulture = oldMax.diverge(self)
        else:
            newCulture = oldMax.diverge(self)

        self.cultures[newCulture] = self.cultures[oldMax]
        del self.cultures[oldMax]
        self.maxCulture = newCulture

        queue = [n for n in self.neighbors]
        checked = set([self])
        while len(queue) > 0:
            city = queue.pop(0)
            if city not in checked:
                checked.add(city)
                if city.maxCulture == oldMax:
                    if city.suitability(oldMax) < city.suitability(newCulture):
                        cc = city.cultures
                        cc[newCulture] = cc[oldMax]
                        del cc[oldMax]

                        for n in city.neighbors:
                            if n not in checked:
                                queue.append(n)

                    city.divergencePressure = 0

    def reform(self):
        # Adaptible cultures can 'reform' instead of diverging
        self.divergencePressure = 0
        queue = [n for n in self.neighbors]
        checked = set([self])
        while len(queue) > 0:
            city = queue.pop(0)
            if city not in checked:
                checked.add(city)
                if city.maxCulture == self.maxCulture:
                    city.divergencePressure = 0
                    for n in city.neighbors:
                        if n not in checked:
                            queue.append(n)
        self.maxCulture.reform(self)

    def postTick(self):
        self.rescale()
        self.recalculate()
        if self.divergencePressure > DIVERGENCE_THRESHOLD:
            if random() > 0.5 + self.maxCulture['HARDINESS']:
                self.diverge()
            else:
                self.reform()

    # --- Drawing Functions ---

    def draw(self, canvas, data):
        sVertices = [scale(vertex, data) for vertex in self.vertices]
        if self.altitude > 0:
            if self.vegetation > 0.6:
                baseColor = mixColors(DARK_GRASS, FOREST_COLOR,
                                      self.vegetation)
            else:
                baseColor = mixColors(DARK_GRASS, GRASS_COLOR, self.altitude)
        else:
            baseColor = mixColors(DARK_OCEAN, OCEAN_COLOR, -self.altitude)

        if data.drawMode == 0:
            color = baseColor
        elif data.drawMode == 1:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.wetness)
        elif data.drawMode == 2:
            color = mixColors(COLD_COLOR, HOT_COLOR, (self.temp + 1) / 2)
        elif data.drawMode == 3:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.fertility)
        elif data.drawMode == 4:
            color = mixColors(GRASS_COLOR, FOREST_COLOR, self.vegetation)
        else:
            if self.maxCulture:
                saturation = 0.9 + self.population / self.capacity / 12
                color = mixColors(baseColor, self.maxCulture.color, saturation)
            else:
                color = baseColor
        canvas.create_polygon(sVertices,
                              fill=rgbToColor(color),
                              outline='')
