# # --- Terrain ---
# #
# # - Terrain-generating functions
# #
# # --- --- --- ---

from City import *
from Culture import *
from Graphics import *
from Geometry import *
from random import *
from math import sin, cos


def getRelief(origin, dest):
    # Gets the slope between two cities
    return (dest.altitude - origin.altitude) / \
        dist(origin.center, dest.center)


def landDump(source, size, check, altitude, falloff, jaggedness):
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
            city.biome = 'Grassland'
            filled.add(city)
            expands = [(factor + 1, neigh) for neigh in city.neighbors
                       if neigh not in filled and check(neigh)]
            # Insert one earlier for some variation
            if random() < jaggedness:
                if expands:
                    frontier.insert(0, expands.pop())

            frontier += expands


def generateLake(source, size):
    # Similar to landDump, but makes lakes instead
    frontier = [(0, source)]
    filled = set()
    while len(filled) < size and len(frontier) > 0:
        factor, city = frontier.pop(0)
        # Check if city got filled in twice
        if city not in filled:
            city.altitude = 0
            city.biome = 'Lake'
            filled.add(city)
            expands = [(factor + 1, neigh) for neigh in city.neighbors
                       if neigh not in filled and not neigh.isSea() and
                       not neigh.onRiver]

            frontier += expands


def averageAltitudes(map):
    # Average out all cities' altitudes
    altitudes = {}
    for coord in map.cities:
        city = map.cities[coord]
        total = sum([neigh.altitude for neigh in city.neighbors])
        average = total / len(city.neighbors)
        altitudes[coord] = average

    for coord in altitudes:
        map.cities[coord].altitude = altitudes[coord]
        if map.cities[coord].altitude > 0:
            map.cities[coord].biome = 'Grassland'


def spawnLand(map):
    # Randomly distribute some land

    # Large 'Continents'
    for i in range(3):
        landDump(map.randomCity(),
                 map.cityCount // 16.7,
                 lambda x: x.altitude <= 0,
                 0.1,
                 0.1,
                 0.1)

    # Midsize regions
    for i in range(10):
        landDump(map.randomCity(),
                 map.cityCount // 100,
                 lambda x: True,
                 0.15 + random() * 0.1,
                 0.15,
                 0.2)

    # Mountains
    for i in range(10):
        lands = [map.cities[coord] for coord in map.cities if
                 map.cities[coord].altitude > 0]
        if lands:
            target = choice(lands)
            landDump(target,
                     map.cityCount // 200,
                     lambda x: x.altitude > 0,
                     0.5 + random() * 0.2,
                     0.4,
                     0.6)
        else:
            break

    # Average
    averageAltitudes(map)

    # Tiny coastal jagged things
    for i in range(40):
        coastals = [map.cities[coord] for coord in map.cities if
                    map.cities[coord].isCoastal()]
        if coastals:
            target = choice(coastals)
            landDump(target,
                     map.cityCount // 305,
                     lambda x: x.altitude <= 0,
                     0.1,
                     0.2,
                     0)
        else:
            break


def generateRiver(map, source, sources):
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
                nextCity = map.getStraightestCity(head, heading,
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
                    nextCity = map.getStraightestCity(head, heading,
                                                      choices)
                else:
                    choices.sort(key=lambda city: getRelief(head, city))
                    nextCity = choices[0]
            else:
                # Make it a 'lake'
                generateLake(head, randint(2, 5))
                break
        river.append(nextCity)
        head.downstream = nextCity
        if nextCity.biome == 'Grassland':
            nextCity.biome = 'Flood Plain'
        head = nextCity

    # Follow connected rivers
    if head.onRiver:
        while head.downstream:
            river.append(head.downstream)
            head = head.downstream

    if len(river) > 1:
        return river


def generateRivers(map):
    MIN_ALTITUDE = 0.15

    for i in range(map.cityCount // 100):
        sources = set(map.cities[coord] for coord in map.cities if
                      map.cities[coord].altitude >= MIN_ALTITUDE)
        if sources:
            newSource = choice(tuple(sources))
            newRiver = generateRiver(map, newSource, sources)
            if newRiver:
                map.rivers.append(newRiver)
        else:
            break


def findLakes(map):
    # If water is on the edge of the map, it's the ocean, else it's
    # a lake
    frontier = [c for c in map.borderCities if c.isSea()]
    checked = set()
    while len(frontier) > 0:
        city = frontier.pop(0)
        if city not in checked:
            city.biome = 'Ocean'
            checked.add(city)
            expands = [neigh for neigh in city.neighbors
                       if neigh.isSea()]

            frontier += expands


def setWetness(map):
    # Cities are wetter if they're near rivers or oceans, or equatorial
    # Assign proximity to water
    queue = [(city, 0) for city in map.cities.values() if
             city.biome in ['Lake', 'Flood Plain', 'Ocean']]
    checked = set()
    avgR = (map.width * map.height / map.cityCount) ** 0.5
    while len(queue) > 0:
        city, distance = queue.pop(0)
        if city not in checked:
            city.coastal = city.isCoastal()
            checked.add(city)

            distFactor = 1 / (distance * avgR / 50 + 1)
            # Magic rain function
            latitude = city.center[1] / map.height
            rainFactor = (0.6 - sin(4 * pi * (latitude - 0.15)) *
                          sin(4 * pi * (latitude - 0.15) / 3)) / 1.8
            city.wetness = (distFactor * 3 + rainFactor) / 4
            for neigh in city.neighbors:
                queue.append((neigh, distance + 1))


def setHydration(map):
    # Cities are wetter if they're near rivers or lakes, or equatorial
    # Assign proximity to water
    queue = [(city, 0) for city in map.cities.values() if
             city.biome in ['Lake', 'Flood Plain']]
    checked = set()
    avgR = (map.width * map.height / map.cityCount) ** 0.5
    while len(queue) > 0:
        city, distance = queue.pop(0)
        if city not in checked:
            city.coastal = city.isCoastal()
            checked.add(city)

            distFactor = 1 / (distance * avgR / 50 + 1)
            # Magic rain function
            latitude = city.center[1] / map.height
            rainFactor = (0.6 - sin(4 * pi * (latitude - 0.15)) *
                          sin(4 * pi * (latitude - 0.15) / 3)) / 1.8
            city.hydration = (distFactor * 3 + rainFactor) / 4
            for neigh in city.neighbors:
                queue.append((neigh, distance + 1))


def setTemperature(map):
    # Cities are colder if they're higher up, or near a pole. This effect
    # is dampened by wetness
    for city in map.cities.values():
        latitudeFactor = 0.7 * (1 - cos(2 * pi * city.center[1] /
                                        map.height)) / 2
        altitudeFactor = 1.3 * (1 - city.altitude)
        waterFactor = 1 - city.wetness / 2
        city.temp = (latitudeFactor + altitudeFactor - 1) * waterFactor


def setFertility(map):
    # Cities are more fertile if they're hydrated, and a temperate climate.
    # Hotness is less bad than coldness
    for city in map.cities.values():
        tempFactor = (sin(pi / 2 * city.temp ** 2) +
                      sin(3 * pi / 2 * city.temp ** 2) / 2) * 0.8
        waterFactor = city.hydration * 1.2
        city.fertility = (tempFactor + 3 * waterFactor) / 4
        city.capacity = city.fertility * (1 + city.infrastructure) * 250


def setVegetation(map):
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
                city.biome = 'Forest'
                filled.add(city)
                expands = [neigh for neigh in city.neighbors
                           if neigh not in filled and
                           neigh.vegetation < 0.6 and
                           neigh.fertility > MIN_FERTILITY and
                           neigh.altitude > 0]

                frontier += expands

    minSize = map.cityCount // 300
    maxSize = map.cityCount // 150

    for city in map.cities.values():
        city.vegetation = city.fertility * 0.6

    for i in range(map.cityCount // 100):
        sources = set(map.cities[coord] for coord in map.cities if
                      map.cities[coord].fertility >= MIN_FERTILITY and
                      map.cities[coord].vegetation < 0.6 and
                      map.cities[coord].altitude > 0)
        if sources:
            newSource = choice(tuple(sources))
            generateForest(newSource, randint(minSize, maxSize))
        else:
            break


def setBiomes(map):
    # Sets remaining biomes
    for coords in map.cities:
        c = map.cities[coords]
        if c.biome in ['Ocean', 'Lake']:
            continue
        elif c.hydration < 0.3 and c.temp > 0.5:
            c.biome = 'Desert'
            c.fertility /= 5
            c.vegetation /= 5
        elif c.temp < 0.05:
            c.biome = 'Icy'
            c.fertility /= 5
            c.vegetation /= 5
        elif c.temp < 0.1:
            c.biome = 'Tundra'
            c.fertility /= 3
            c.vegetation /= 3
        elif c.altitude > 0.7:
            c.biome = 'Mountains'
            c.fertility *= 0.6
        elif c.altitude > 0.4:
            c.biome = 'Highlands'
            c.fertility *= 0.8


def initializeTerrain(map):
    # Call all the terrain initializing functions
    spawnLand(map)
    generateRivers(map)
    findLakes(map)
    setWetness(map)
    setHydration(map)
    setTemperature(map)
    setFertility(map)
    setVegetation(map)
    setBiomes(map)
