# # --- City ---
# #
# # - Contains the City class, and helper functions
# #
# # --- --- --- ---

from Biome import *
from CityCulture import *
from Graphics import *
from Geometry import dist
from Polity import *
from random import random, choice

DEFAULT_NAME = "Uninhabited"


class City:
    def __init__(self, center, vertices):
        self.center = center
        self.vertices = vertices
        self.neighbors = set()
        self.radius = max([dist(self.center, v) for v in self.vertices])

        self.name = DEFAULT_NAME

        self.altitude = 0
        self.onRiver = False
        self.downstream = None
        self.biome = 'Lake'

        self.cultures = {}
        self.maxCulture = None
        self.population = 0
        self.divergencePressure = 0
        self.mergePressures = {}
        self.immigrants = []
        self.immigrantPop = 0

        self.infrastructure = 0
        self.progress = 0
        self.difficulty = 200
        self.cityLevel = 0

        self.polity = None

    def __hash__(self):
        return hash(self.center)

    def __repr__(self):
        return printWord(self.name).capitalize()

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
        coastFactor = self.wetness if self.coastal else (1 - self.wetness)
        return altitudeFactor * tempFactor * farmFactor * coastFactor

    def value(self, culture):
        # Returns the value of some province to a culture
        # from a certain orign province
        altitudeFactor = 1 - abs(self.altitude - culture.idealAltitude)
        tempFactor = 1 - abs(self.temp - culture.idealTemp)
        farmFactor = self.fertility * culture['AGRI']
        forestFactor = -max(0.5, abs(self.vegetation))
        coastFactor = self.wetness if self.coastal else (1 - self.wetness)
        return altitudeFactor + tempFactor + farmFactor + \
            forestFactor + coastFactor

    # ----- Runtime Functions -----

    def births(self):
        for culture in self.cultures:
            factor = self.suitability(culture) * \
                (1 - culture['HARDINESS']) + \
                culture['HARDINESS']
            realRate = 1 + culture['BIRTHS'] * factor
            self.cultures[culture] *= realRate

        self.population = sum([self.cultures[c] for c in self.cultures])

    # --- Infrastructure ---

    def build(self):
        # Build infrastructue
        if self.maxCulture:
            diff = (self.population - self.difficulty) / self.difficulty
            if diff > 0:
                boost = self.maxCulture['INNOV'] * diff * (1 - self.vegetation)
                self.progress += boost
                if self.progress > 1:
                    self.infrastructure += 0.1
                    self.progress -= 1
            else:
                self.infrastructure *= 0.9

    def setCityLevel(self):
        thresholds = [380, 1000, 2500, 10000, 100000, 1000000]
        self.difficulty = thresholds[self.cityLevel] / 2
        if self.population > thresholds[self.cityLevel + 1]:
            self.cityLevel += 1
            if self.cityLevel == 2:
                if self.polity:
                    self.polity.territories.discard(self)
                self.polity = Polity(self, liege=self.polity)

    # --- Migration ---

    def emigrate(self, culture, amount):
        # Decrease the population of a culture here by a
        # certain amount
        if culture in self.cultures:
            self.cultures[culture] -= amount
        else:
            self.cultures[culture] = -amount

    def distribute(self, population, culture, targetList, overflow=True,
                   hardCap=True):
        # Distributes from this city to the cities on targetList
        remainder = population
        # hardCap means you respect the true capacity, non-hardCap
        # means they respect the migration capacity
        if hardCap:
            spaces = [n.capacity - n.population - n.immigrantPop
                      for n in targetList]
        else:
            factor = 1 - culture['MIGRATE']
            spaces = [min(n.capacity - n.population,
                          n.capacity * factor - n.cultures[culture]
                          if culture in n.cultures else 0) -
                      n.immigrantPop for n in targetList]

        def transfer(target, amount):
            nonlocal remainder
            self.emigrate(culture, amount)
            target.immigrants.append((culture, amount))
            target.immigrantPop += amount
            remainder -= amount

        for i in range(len(targetList)):
            if remainder <= 0:
                break
            target = targetList[i]
            amount = max(0, min(spaces[i], remainder))
            spaces[i] -= amount
            transfer(target, amount)

        if remainder > 0 and overflow:
            for i in range(len(targetList)):
                if remainder <= 0:
                    break
                target = targetList[i]
                amount = remainder / 2
                transfer(target, amount)
            transfer(targetList[0], remainder)
            return 0
        else:
            return remainder

    def migration(self):
        # Emigration from between the migration cap and the hard cap
        for culture in self.cultures:
            factor = 1 - culture['MIGRATE']
            if culture != self.maxCulture and self.maxCulture:
                factor *= self.maxCulture['TOLERANCE']
            migExcess = self.cultures[culture] - self.capacity * factor

            if migExcess > 0:
                destinations = [n for n in self.neighbors if not n.isSea()]
                if destinations:
                    destinations.sort(key=lambda n: n.value(culture),
                                      reverse=True)
                    migExcess = self.distribute(migExcess, culture,
                                                destinations, overflow=False,
                                                hardCap=False)

                destinations = [n for n in self.neighbors if not n.isSea() and
                                n.value(culture) > self.value(culture)]
                if destinations:
                    destinations.sort(key=lambda n: n.value(culture),
                                      reverse=True)
                    self.distribute(migExcess, culture, destinations)

        self.population = sum(self.cultures.values())

    def exploration(self):
        # Send out explorer parties
        mc = self.maxCulture
        if mc in self.cultures:
            excess = self.cultures[mc] - (1 - mc['EXPLORE']) * self.capacity
            if excess > 0:
                destinations = [n for n in self.neighbors if not n.isSea() and
                                mc not in n.cultures]
                if destinations:
                    target = choice(destinations)
                    self.emigrate(mc, excess)
                    target.immigrants.append((mc, excess))
                    target.immigrantPop += excess

    def takeover(self, oldMax):
        # Takeover events
        self.divergencePressure = 0
        self.mergePressures = {}
        if self.maxCulture is None:
            self.name = 'Uninhabited'
        else:
            smcl = self.maxCulture.language
            if oldMax is None:
                self.name = smcl.generateWord()
            else:
                self.name = smcl.transliterate(self.name)

    def rescale(self):
        # Rescale cultures to fit within capacity
        total = sum(self.cultures.values())
        newCultures = {}
        oldMax = self.maxCulture
        self.maxCulture = None

        if total > 0:
            factor = min(1, self.capacity / total)
            for culture in self.cultures:
                newAmount = factor * self.cultures[culture]
                if newAmount >= 1:
                    newCultures[culture] = newAmount
            if newCultures:
                self.maxCulture = sorted(newCultures,
                                         key=lambda x: newCultures[x])[-1]
            else:
                self.maxCulture = None

        self.cultures = newCultures
        if self.maxCulture != oldMax:
            self.takeover(oldMax)

    def immigrate(self):
        # Executes on the immigrants entering
        for culture, amount in self.immigrants:
            self.emigrate(culture, -amount)
        self.immigrantPop = 0
        self.immigrants.clear()

    def recalculate(self):
        # Recalculate some things
        self.population = sum(self.cultures.values())
        self.capacity = self.fertility * (1 + self.infrastructure) * 250

        sc = self.cultures
        if self.maxCulture in sc:
            # Calculate divergence pressure
            change = (0.8 - self.suitability(self.maxCulture) ** 0.5) * \
                sc[self.maxCulture] / self.capacity
            self.divergencePressure = max(0, self.divergencePressure + change)

            # Calculate merger pressure
            mp = self.mergePressures
            for culture in sc:
                if culture != self.maxCulture:
                    pressure = sc[culture] / sc[self.maxCulture] - \
                        1 + self.maxCulture['TOLERANCE']
                    if culture in mp:
                        mp[culture] += pressure
                    else:
                        mp[culture] = pressure
                    mp[culture] = max(0, mp[culture])

        newMP = {}
        for culture in self.mergePressures:
            if culture in sc:
                newMP[culture] = self.mergePressures[culture]
        self.mergePressures = newMP

    # --- Ticks ---

    def tick(self):
        # Births
        self.births()
        self.migration()
        self.exploration()

    def midTick(self):
        self.immigrate()
        self.build()
        self.setCityLevel()
        if self.divergencePressure > DIVERGENCE_THRESHOLD:
            if random() > 0.25 + self.maxCulture['HARDINESS']:
                diverge(self)
            else:
                reform(self)

        for culture in self.mergePressures:
            if self.mergePressures[culture] > MERGE_THRESHOLD:
                merge(self, culture)
        assimilate(self)

    def postTick(self):
        self.rescale()
        self.recalculate()

    # --- Drawing Functions ---

    def draw(self, canvas, data):
        sVertices = [scale(vertex, data) for vertex in self.vertices]
        baseColor = biomes[self.biome].getColor(self)

        if data.drawMode == 0 or self.biome in ['Lake', 'Ocean']:
            color = baseColor
        elif data.drawMode == 1:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.wetness)
        elif data.drawMode == 2:
            color = mixColors(COLD_COLOR, HOT_COLOR, (self.temp + 1) / 2)
        elif data.drawMode == 3:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.fertility)
        elif data.drawMode == 4:
            color = mixColors(GRASS_COLOR, FOREST_COLOR, self.vegetation)
        elif data.drawMode == 5:
            if self.maxCulture:
                saturation = 0.95
                color = mixColors(baseColor, self.maxCulture.color, saturation)
            else:
                color = baseColor
        elif data.drawMode == 6:
            if self.polity:
                saturation = 0.95
                color = mixColors(baseColor, self.polity.superLiege().color,
                                  saturation)
            else:
                color = baseColor
        canvas.create_polygon(sVertices,
                              fill=rgbToColor(color),
                              outline='')

    def drawDecorations(self, canvas, data):
        if self.cityLevel > 0:
            circleR = self.cityLevel
            if circleR >= 1:
                circlepts = [[self.center[0] - circleR,
                              self.center[1] - circleR],
                             [self.center[0] + circleR,
                              self.center[1] + circleR]]
                circlepts = [scale(pt, data) for pt in circlepts]
                canvas.create_oval(circlepts)
