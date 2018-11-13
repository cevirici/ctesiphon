# # --- Terrain ---
# #
# # - Terrain-generating functions
# #
# # --- --- --- ---

from City import *
from Graphics import *
from Geometry import dist
from random import *
from math import atan2, pi


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
                           if neigh not in filled and neigh.altitude > 0]

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
                    head = self.getStraightestCity(head, heading, seaNeighbors)
                else:
                    seaNeighbors.sort(key=lambda city: getRelief(head, city))
                    head = seaNeighbors[0]
                river.append(head)
            else:
                # Remove everyone who's too steep, or already in the river
                choices = [city for city in head.neighbors if
                           city not in river and
                           getRelief(head, city) < SLOPE_THRESHOLD]
                if choices:
                    # Try the straightest
                    if len(river) > 1:
                        heading = getHeading(river[-2], head)
                        head = self.getStraightestCity(head, heading, choices)
                    else:
                        choices.sort(key=lambda city: getRelief(head, city))
                        head = choices[0]
                    river.append(head)
                else:
                    # Make it a 'lake'
                    self.generateLake(head, randint(1, 5))
                    break
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

    def drawCities(self, canvas, data):
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

    def draw(self, canvas, data):
        self.drawCities(canvas, data)

        for river in self.rivers:
            sRiver = []
            for city in river:
                sRiver.append(scale(city.center, data))

            canvas.create_line(sRiver,
                               fill=rgbToColor(DARK_OCEAN),
                               smooth=True,
                               width=2 * data.zoom)
