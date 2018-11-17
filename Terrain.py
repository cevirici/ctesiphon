# # --- Terrain ---
# #
# # - Terrain-generating functions
# #
# # --- --- --- ---

from City import *
from Culture import *
from Graphics import *
from Geometry import dist
from random import *
from math import atan2, pi, sin, cos


def getRelief(origin, dest):
    # Gets the slope between two cities
    return (dest.altitude - origin.altitude) / \
        dist(origin.center, dest.center)


def getHeading(origin, dest):
    # Gets the heading between two cities
    return atan2(dest.center[1] - origin.center[1],
                 dest.center[0] - origin.center[0])


def headingDiff(heading_a, heading_b):
    # Returns the absolute value of the difference between
    # two headings
    raw = abs(heading_a - heading_b)
    if raw > pi:
        raw = 2 * pi - raw
    return raw


class Map:
    def __init__(self, source, data):
        # Imports the geometry from a Mapmaker object
        self.cities = {}
        self.cityCount = len(source.pointSet)

        self.centerCity = None
        closestDist = float('inf')
        center = [data.viewPos[i] + data.viewSize[i] / data.zoom / 2
                  for i in range(2)]

        for point in source.pointSet:
            self.cities[point] = City(point, source.vertices[point])
            if dist(point, center) < closestDist:
                closestDist = dist(point, center)
                self.centerCity = self.cities[point]

        # Populate adjacency dictionary
        for edge in source.edges:
            if edge[0] != edge[1] and len(source.edges[edge]) > 0:
                self.cities[edge[0]].neighbors.add(self.cities[edge[1]])
                self.cities[edge[1]].neighbors.add(self.cities[edge[0]])

        self.rivers = []

        self.width = source.width
        self.height = source.height

    def randomCity(self):
        # Returns a random city
        return choice(tuple(self.cities.values()))

    def findClosestCity(self, point, data):
        # Returns the closest city from a point on screen
        toCheck = [self.centerCity]
        checked = set()
        bestDistance = float('inf')
        closest = None
        while len(toCheck) > 0:
            city = toCheck.pop(0)
            if city not in checked:
                if dist(city.center, point) < bestDistance:
                    bestDistance = dist(city.center, point)
                    closest = city
                checked.add(city)
                for neigh in city.neighbors:
                    if neigh not in checked and neigh.visible(data):
                        toCheck.append(neigh)
        return closest

    def landDump(self, source, size, check, altitude, falloff, jaggedness):
        # Starting from a 'source' city, raise it to a certain altitude and
        # raise its neighbors to a proportion of it, until some number of
        # cities have been filled

        frontier = [(0, source)]
        filled = set()
        while len(filled) < size and len(frontier) > 0:
            factor, city = frontier.pop(0)
            # Check if city got filled in twice
            if city not in filled:
                city.altitude += altitude * (1 - falloff) ** factor
                city.altitude = min(1, max(-1, altitude))
                filled.add(city)
                expands = [(factor + 1, neigh) for neigh in city.neighbors
                           if neigh not in filled and check(neigh)]
                # Insert one earlier for some variation
                if random() < jaggedness:
                    if expands:
                        frontier.insert(0, expands.pop())

                frontier += expands

    def generateLake(self, source, size):
        # Similar to landDump, but makes lakes instead
        frontier = [(0, source)]
        filled = set()
        while len(filled) < size and len(frontier) > 0:
            factor, city = frontier.pop(0)
            # Check if city got filled in twice
            if city not in filled:
                city.altitude = 0
                filled.add(city)
                expands = [(factor + 1, neigh) for neigh in city.neighbors
                           if neigh not in filled and not neigh.isSea() and
                           not neigh.onRiver]

                frontier += expands

    def averageAltitudes(self):
        # Average out all cities' altitudes
        altitudes = {}
        for coord in self.cities:
            city = self.cities[coord]
            total = sum([neigh.altitude for neigh in city.neighbors])
            average = total / len(city.neighbors)
            altitudes[coord] = average

        for coord in altitudes:
            self.cities[coord].altitude = altitudes[coord]

    def spawnLand(self):
        # Randomly distribute some land

        # Large 'Continents'
        for i in range(3):
            self.landDump(self.randomCity(),
                          self.cityCount // 16.7,
                          lambda x: x.altitude <= 0,
                          0.1,
                          0.1,
                          0.1)

        # Midsize regions
        for i in range(10):
            self.landDump(self.randomCity(),
                          self.cityCount // 100,
                          lambda x: True,
                          0.15 + random() * 0.1,
                          0.15,
                          0.2)

        # Mountains
        for i in range(10):
            lands = [self.cities[coord] for coord in self.cities if
                     self.cities[coord].altitude > 0]
            if lands:
                target = choice(lands)
                self.landDump(target,
                              self.cityCount // 200,
                              lambda x: x.altitude > 0,
                              0.5 + random() * 0.2,
                              0.4,
                              0.6)
            else:
                break

        # Average
        self.averageAltitudes()

        # Tiny coastal jagged things
        for i in range(40):
            coastals = [self.cities[coord] for coord in self.cities if
                        self.cities[coord].isCoastal()]
            if coastals:
                target = choice(coastals)
                self.landDump(target,
                              self.cityCount // 305,
                              lambda x: x.altitude <= 0,
                              0.1,
                              0.2,
                              0)
            else:
                break

    def getStraightestCity(self, origin, heading, candidates):
        # Returns a city among the candidates that's keeps to the course
        # as closely as possible
        def straightness(city):
            return headingDiff(getHeading(origin, city), heading)
        return sorted(candidates, key=straightness)[0]

    def generateRiver(self, source, sources):
        # Generate a single river from a given source
        SLOPE_THRESHOLD = 0.001

        river = [source]
        head = source
        while not head.onRiver and head.altitude > 0:
            head.onRiver = True
            sources.discard(head)
            # Check for direct sea neighbors
            seaNeighbors = [city for city in head.neighbors if
                            city.altitude <= 0]
            if seaNeighbors:
                if len(river) > 1:
                    heading = getHeading(river[-2], head)
                    nextCity = self.getStraightestCity(head, heading,
                                                       seaNeighbors)
                else:
                    seaNeighbors.sort(key=lambda city: getRelief(head, city))
                    nextCity = seaNeighbors[0]
            else:
                # Remove everyone who's too steep, or already in the river
                choices = [city for city in head.neighbors if
                           city not in river and
                           getRelief(head, city) < SLOPE_THRESHOLD]
                if choices:
                    # Try the straightest
                    if len(river) > 1:
                        heading = getHeading(river[-2], head)
                        nextCity = self.getStraightestCity(head, heading,
                                                           choices)
                    else:
                        choices.sort(key=lambda city: getRelief(head, city))
                        nextCity = choices[0]
                else:
                    # Make it a 'lake'
                    self.generateLake(head, randint(2, 5))
                    break
            river.append(nextCity)
            head.downstream = nextCity
            head = nextCity

        # Follow connected rivers
        if head.onRiver:
            while head.downstream:
                river.append(head.downstream)
                head = head.downstream

        if len(river) > 1:
            return river

    def generateRivers(self):
        MIN_ALTITUDE = 0.15

        for i in range(self.cityCount // 100):
            sources = set(self.cities[coord] for coord in self.cities if
                          self.cities[coord].altitude >= MIN_ALTITUDE)
            if sources:
                newSource = choice(tuple(sources))
                newRiver = self.generateRiver(newSource, sources)
                if newRiver:
                    self.rivers.append(newRiver)
            else:
                break

    def setWetness(self):
        # Cities are wetter if they're near rivers or oceans, or equatorial
        # Assign proximity to water
        queue = [(city, 0) for city in self.cities.values() if city.isSea() or
                 city.onRiver]
        checked = set()
        avgR = (self.width * self.height / self.cityCount) ** 0.5
        while len(queue) > 0:
            city, distance = queue.pop(0)
            if city not in checked:
                city.coastal = city.isCoastal()
                checked.add(city)

                distFactor = 1 / (distance * avgR / 50 + 1)
                # Magic rain function
                latitude = city.center[1] / self.height
                rainFactor = (0.6 - sin(4 * pi * (latitude - 0.15)) *
                              sin(4 * pi * (latitude - 0.15) / 3)) / 1.8
                city.wetness = (distFactor * 3 + rainFactor) / 4
                for neigh in city.neighbors:
                    queue.append((neigh, distance + 1))

    def setTemperature(self):
        # Cities are colder if they're higher up, or near a pole. This effect
        # is dampened by wetness
        for city in self.cities.values():
            latitudeFactor = 0.7 * (1 - cos(2 * pi * city.center[1] /
                                            self.height)) / 2
            altitudeFactor = 1.3 * (1 - city.altitude)
            waterFactor = 1 - city.wetness / 2
            city.temp = (latitudeFactor + altitudeFactor - 1) * waterFactor

    def setFertility(self):
        # Cities are more fertile if they're wetter, and a temperate climate.
        # Hotness is less bad than coldness
        for city in self.cities.values():
            tempFactor = (sin(pi / 2 * city.temp ** 2) +
                          sin(3 * pi / 2 * city.temp ** 2) / 2) * 0.8
            waterFactor = city.wetness * 1.2
            city.fertility = (tempFactor + 3 * waterFactor) / 4
            city.capacity = city.fertility * (1 + city.infrastructure) * 250

    def setVegetation(self):
        # Vegetation is just a random factor + fertility, + forests
        MIN_FERTILITY = 0.4

        def generateForest(source, size):
            # Similar to landDump, but makes forests instead
            frontier = [source]
            filled = set()
            while len(filled) < size and len(frontier) > 0:
                city = frontier.pop(0)
                # Check if city got filled in twice
                if city not in filled:
                    city.vegetation += 0.4
                    filled.add(city)
                    expands = [neigh for neigh in city.neighbors
                               if neigh not in filled and
                               neigh.vegetation < 0.6 and
                               neigh.fertility > MIN_FERTILITY and
                               neigh.altitude > 0]

                    frontier += expands

        minSize = self.cityCount // 300
        maxSize = self.cityCount // 150

        for city in self.cities.values():
            city.vegetation = city.fertility * 0.6

        for i in range(self.cityCount // 100):
            sources = set(self.cities[coord] for coord in self.cities if
                          self.cities[coord].fertility >= MIN_FERTILITY and
                          self.cities[coord].vegetation < 0.6 and
                          self.cities[coord].altitude > 0)
            if sources:
                newSource = choice(tuple(sources))
                generateForest(newSource, randint(minSize, maxSize))
            else:
                break

    def initializeTerrain(self):
        # Call all the terrain initializing functions
        self.spawnLand()
        self.generateRivers()
        self.setWetness()
        self.setTemperature()
        self.setFertility()
        self.setVegetation()

    def spawnCultures(self):
        # Spawn some cultures
        for i in range(10):
            sources = [city for city in self.cities.values()
                       if city.altitude > 0]

            origin = choice(sources)
            newCulture = Culture(origin)
            origin.emigrate(newCulture, -50)

    def update(self):
        # Call tick events
        for city in self.cities.values():
            city.tick()

        # Enact transfers
        for city in self.cities.values():
            city.midTick()

        # After redistribution is done, rescale
        for city in self.cities.values():
            city.postTick()

    # --- Drawing ---

    def drawCitiesBG(self, canvas, data):
        # Draw cities, starting from the center, and spreading out until
        # the cities are no longer visible
        toDraw = [self.centerCity]
        drawn = set()
        while len(toDraw) > 0:
            city = toDraw.pop(0)
            if city not in drawn:
                city.draw(canvas, data)
                drawn.add(city)
                for neigh in city.neighbors:
                    if neigh not in drawn and neigh.visible(data):
                        toDraw.append(neigh)

    def drawCities(self, canvas, data):
        # Draw cities, starting from the center, and spreading out until
        # the cities are no longer visible
        toDraw = [self.centerCity]
        drawn = set()
        while len(toDraw) > 0:
            city = toDraw.pop(0)
            if city not in drawn:
                city.drawDecorations(canvas, data)
                drawn.add(city)
                for neigh in city.neighbors:
                    if neigh not in drawn and neigh.visible(data):
                        toDraw.append(neigh)

    def drawCulture(self, origin, searched, canvas, data):
        culture = origin.maxCulture
        if culture is not None:
            A, B = culture.origin, culture.origin
            lastA, lastB = None, None
            while A != lastA or B != lastB:
                lastA, lastB = A, B
                aCand = [n for n in A.neighbors
                         if A.maxCulture == n.maxCulture]
                if aCand:
                    A = sorted(aCand,
                               key=lambda x: dist(x.center, B.center))[-1]
                    if dist(A.center, B.center) < dist(lastA.center, B.center):
                        A = lastA
                        break
                else:
                    break
                bCand = [n for n in B.neighbors
                         if B.maxCulture == n.maxCulture]
                if bCand:
                    B = sorted(bCand,
                               key=lambda x: dist(x.center, A.center))[-1]
                    if dist(A.center, B.center) < dist(lastB.center, A.center):
                        B = lastB
                        break
                else:
                    break

            scaleA = scale(A.center, data)
            scaleB = scale(B.center, data)
            midPt = [(scaleA[i] + scaleB[i]) / 2 for i in range(2)]
            name = printWord(culture.name).capitalize()
            fSize = int(dist(scaleA, scaleB) / len(name)) + 16
            font = ('Times New Roman', fSize)
            canvas.create_text(midPt,
                               font=font,
                               text=name)

    def drawCultures(self, canvas, data):
        # Draw the culture name over the geographical centers
        queue = [self.centerCity]
        painted = set()
        searched = set()
        while len(queue) > 0:
            target = queue.pop()
            if target not in searched:
                searched.add(target)
                if target not in painted:
                    self.drawCulture(target, searched, canvas, data)
                for n in target.neighbors:
                    if n not in searched:
                        queue.append(n)
                    if n.maxCulture == target.maxCulture:
                        painted.add(n)

    def draw(self, canvas, data):
        self.drawCitiesBG(canvas, data)

        for river in self.rivers:
            sRiver = []
            for city in river:
                sRiver.append(scale(city.center, data))

            canvas.create_line(sRiver,
                               fill=rgbToColor(DARK_OCEAN),
                               smooth=True,
                               width=2 * data.zoom)

        # Highlighting active province
        if data.activeCity:
            sVertices = [scale(vertex, data) for vertex in
                         data.activeCity.vertices]
            canvas.create_polygon(sVertices,
                                  fill='',
                                  outline=rgbToColor(HIGHLIGHT),
                                  width=1.5 * data.zoom)

        self.drawCities(canvas, data)

        # if data.drawMode == 5:
        #     self.drawCultures(canvas, data)
