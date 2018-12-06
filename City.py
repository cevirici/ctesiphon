# # --- City ---
# #
# # - Contains the City class, and helper functions
# #
# # --- --- --- ---

from Biome import *
from Buildings import *
from CityCulture import *
from Disaster import *
from Graphics import *
from Geometry import dist
from Language import printWord
from random import random, choice
from copy import copy

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

        self.maxCulture = None
        self.cultures = {}
        self.population = 0
        self.immigrants = []
        self.immigrantPop = 0

        self.divergencePressure = 0
        self.mergePressures = {}

        self.armies = set()
        self.garrison = 0
        self.garrisonMax = 0
        self.builders = 0
        self.builderMax = 10

        self.currentBuilding = buildings[0]
        self.progress = 0
        self.cityLevel = 0
        self.buildings = set()

        self.supplies = 0
        self.storageEff = 1
        self.farmEff = 0.03

        self.polity = None

        self.disasters = {}

    # def __hash__(self):
    #     return hash(self.center)

    def __repr__(self):
        return self.name

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
        coastFactor = 0.5 + self.wetness * (culture.coastal - 0.5)
        return altitudeFactor * tempFactor * farmFactor * coastFactor

    def value(self, culture):
        # Returns the value of some province to a culture
        # from a certain orign province
        altitudeFactor = 1 - abs(self.altitude - culture.idealAltitude)
        tempFactor = 1 - abs(self.temp - culture.idealTemp)
        farmFactor = self.fertility * culture['AGRI']
        forestFactor = -max(0.5, abs(self.vegetation))
        coastFactor = 0.5 + self.wetness * (culture.coastal - 0.5)
        return altitudeFactor + tempFactor + farmFactor + \
            forestFactor + coastFactor

    # ----- Runtime Functions -----

    def births(self):
        for culture in self.cultures:
            factor = self.suitability(culture) * \
                (1 - culture['HARDINESS']) + \
                culture['HARDINESS']
            if self.polity:
                if culture == self.polity.culture:
                    factor *= 2
            realRate = 1 + culture['BIRTHS'] * factor
            self.cultures[culture] *= realRate

        self.population = sum([self.cultures[c] for c in self.cultures])

    # --- Infrastructure ---

    def farm(self):
        # Generate supplies
        for culture in self.cultures:
            self.supplies += self.cultures[culture] * (1 + culture['AGRI'] *
                                                       self.fertility *
                                                       self.farmEff)
        self.supplies = min(self.capacity * self.storageEff, self.supplies)

    def employ(self):
        # Turn 'spare' people into builders / soldiers
        if self.maxCulture:
            self.production = self.population * (self.maxCulture['AGRI'] *
                                                 self.fertility *
                                                 self.farmEff)
            factor = 1
            if self.supplies > self.capacity * self.storageEff:
                factor = 1.1
            excess = factor * self.production - self.builders - \
                sum([army.size for army in self.armies])
            # Proportion of excess to conscript
            ratio = self.maxCulture['MILITANCE']
            if excess > 0:
                conscripts = min(ratio * excess,
                                 self.garrisonMax - self.garrison)
                self.garrison += conscripts
                excess -= conscripts

                newBuilders = min(excess, self.builderMax - self.builders)
                self.builders += newBuilders
            elif excess < 0:
                self.builders *= 0.9
                self.garrison *= 0.9

    def build(self):
        # Make progress towards the next building
        if self.maxCulture:
            boost = self.maxCulture['INNOV'] * self.builders * \
                (1 - self.vegetation)
            self.progress += boost
            if self.progress > self.currentBuilding.requirement:
                self.progress -= self.currentBuilding.requirement
                self.currentBuilding.build(self)
                self.buildings.add(self.currentBuilding.name)
                for b in buildings:
                    if b.name not in self.buildings:
                        self.currentBuilding = b
                        break

    def disasterTick(self):
        # Disaster spawning and ticking
        newDisasters = {}
        if 'Fire' not in self.disasters:
            if not self.isSea():
                if random() < (self.temp - 0.63) ** 3:
                    self.disasters['Fire'] = fire.baseDuration

        if 'Hurricane' not in self.disasters:
            if self.isSea():
                if random() < (max(0, self.temp - 0.53)) ** 2:
                    self.disasters['Hurricane'] = hurricane.baseDuration

        for dName in self.disasters:
            for disaster in disasters:
                if disaster.name == dName:
                    disaster.tick(self)
                    if self.disasters[dName] > 0:
                        newDisasters[dName] = self.disasters[dName]
                    break

        self.disasters = newDisasters

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
            if amount > 20:
                spaces[i] -= amount
                transfer(target, amount)

        if remainder > 0 and overflow:
            for i in range(len(targetList)):
                if remainder <= 0:
                    break
                target = targetList[i]
                amount = remainder / 2
                if amount > 20:
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

            if migExcess > 20:
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
            if excess > 20:
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

    def consume(self):
        # Consume supplies, die off if there's not enough
        # Garrison
        if self.supplies < self.garrison:
            self.garrison = self.supplies
            self.supplies = 0
            return
        else:
            self.supplies -= self.garrison

        # Civilians
        popMax = min(self.capacity, self.supplies)
        if popMax < self.population:
            ratio = popMax / self.population
            for culture in self.cultures:
                self.cultures[culture] *= ratio
            self.supplies -= self.population * ratio
            return
        else:
            self.supplies -= self.population

        # Armies
        soldierPop = sum([army.size for army in self.armies])
        if self.supplies < soldierPop:
            ratio = self.supplies / soldierPop
            for army in self.armies:
                army.size *= ratio
            self.supplies = 0
            return
        else:
            self.supplies -= self.garrison

        # Builders
        builderCap = min(self.supplies, self.builderMax)
        if builderCap < self.builders:
            self.builders = builderCap
            self.supplies = 0
        else:
            self.supplies -= self.builders

    def rescale(self):
        # Cap each population below their respective maxima
        oldMax = self.maxCulture
        # Population
        newCultures = {}
        # Make sure we don't have mermaids
        if not self.isSea():
            for culture in self.cultures:
                if self.cultures[culture] >= 1:
                    newCultures[culture] = self.cultures[culture]

            if newCultures:
                self.maxCulture = sorted(newCultures,
                                         key=lambda x: newCultures[x])[-1]
            else:
                self.maxCulture = None

            if self.maxCulture != oldMax:
                self.takeover(oldMax)

            self.cultures = newCultures

            # Armies
            newArmies = copy(self.armies)
            for army in newArmies:
                if army.size < 1:
                    army.demobilize()

    def immigrate(self):
        # Executes on the immigrants entering
        for culture, amount in self.immigrants:
            self.emigrate(culture, -amount)
        self.immigrantPop = 0
        self.immigrants.clear()

    def recalculate(self):
        # Recalculate some things
        self.population = sum(self.cultures.values())

        # If there's too many soldiers, kick them out
        if self.polity:
            garrisonCap = self.polity.militance * self.capacity
            if self.garrison > garrisonCap:
                self.garrison = garrisonCap

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
        self.farm()
        self.births()
        self.employ()
        self.migration()
        self.exploration()

    def midTick(self):
        self.immigrate()
        self.build()
        if self.divergencePressure > DIVERGENCE_THRESHOLD:
            if random() > 0.25 + self.maxCulture['HARDINESS']:
                diverge(self)
            else:
                reform(self)

        for culture in self.mergePressures:
            if self.mergePressures[culture] > MERGE_THRESHOLD:
                merge(self, culture)

        self.disasterTick()
        assimilate(self)

    def postTick(self):
        self.consume()
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
            color = baseColor
            saturation = 0.95
            if self.polity:
                color = mixColors(baseColor,
                                  self.polity.superLiege().color,
                                  saturation)
                if data.activeCity:
                    if data.activeCity.polity:
                        for subject in data.activeCity.polity.subjects:
                            if self.polity == subject or \
                                    self.polity.isSubject(subject):
                                color = mixColors(baseColor,
                                                  subject.color,
                                                  saturation)
                                break
                        if self.polity == data.activeCity.polity:
                            color = mixColors(baseColor,
                                              data.activeCity.polity.color,
                                              saturation)

        elif data.drawMode == 7:
            if self.population:
                factor = log(self.population, 10) / 6
            else:
                factor = 0
            color = mixColors((255, 80, 80), (0, 255, 0), factor)
        canvas.create_polygon(sVertices,
                              fill=rgbToColor(color),
                              outline='',
                              tag='map')

    def getToolTip(self, data):
        # Returns the appropriate tooltip for the current mapmode
        if data.drawMode == 0:
            return printWord(self.name).capitalize()
        elif data.drawMode == 1:
            return 'Hydration: {:.2f}'.format(self.wetness)
        elif data.drawMode == 2:
            return 'Temperature: {:.2f}'.format(self.temp)
        elif data.drawMode == 3:
            return 'Fertility: {:.2f}'.format(self.fertility)
        elif data.drawMode == 4:
            return 'Vegetation: {:.2f}'.format(self.vegetation)
        elif data.drawMode == 5:
            if self.maxCulture:
                return printWord(self.maxCulture.name).capitalize()
            else:
                return 'Uninhabited'
        elif data.drawMode == 6:
            if self.polity:
                direct = printWord(self.polity.name).capitalize()
                superLiege = printWord(self.polity.superLiege().
                                       name).capitalize()
                if direct != superLiege:
                    return '{} - under {}'.format(direct, superLiege)
                else:
                    return direct
            else:
                return 'No Polity'
        elif data.drawMode == 7:
            return str(int(self.population))

    def drawDecorations(self, canvas, data):
        if self.cityLevel > 0:
            sprite = data.cityIcons[self.cityLevel - 1]
            canvas.create_image(scale(self.center, data),
                                image=sprite, tag='map')
        if self.cityLevel > 1:
            pos = [self.center[0], self.center[1] + 8]
            canvas.create_text(scale(pos, data),
                               font=HUD_FONT_SMALL, fill='white',
                               text=printWord(self.name).capitalize(),
                               tag='map')

        n = len(self.armies) + 1
        i = 0
        for army in self.armies:
            i += 1
            radius = log(army.size + 1) / 3
            shift = [-10 + 20 / n * i, 5]
            armyPts = [[self.center[0] + shift[0] - radius,
                        self.center[1] + shift[1] - radius],
                       [self.center[0] + shift[0] + radius,
                        self.center[1] + shift[1] + radius]]
            armyPts = [scale(pt, data) for pt in armyPts]
            canvas.create_rectangle(armyPts,
                                    outline='white',
                                    fill=rgbToColor(army.owner.color),
                                    tag='map')

        # --- Hurricane ---

        if 'Fire' in self.disasters:
            frame = self.disasters['Fire'] % len(data.fireIcons)
            canvas.create_image(scale(self.center, data),
                                image=data.fireIcons[frame],
                                tag='map')

        if 'Hurricane' in self.disasters:
            frame = self.disasters['Hurricane'] % len(data.hurricaneIcons)
            canvas.create_image(scale(self.center, data),
                                image=data.hurricaneIcons[frame],
                                tag='map')
