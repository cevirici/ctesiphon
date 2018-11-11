# # --- Terrain ---
# #
# # - Terrain-generating functions
# #
# # --- --- --- ---

from Graphics import *
from random import *


class City:
    def __init__(self, center, vertices):
        self.center = center
        self.vertices = vertices
        self.neighbors = set()

        self.altitude = -1

    def __hash__(self):
        return hash(self.center)

    def isCoastal(self):
        if self.altitude > 0:
            for neighbor in self.neighbors:
                if neighbor.altitude < 0:
                    return True
        return False

    def draw(self, canvas, data):
        sVertices = [scale(vertex, data) for vertex in self.vertices]
        canvas.create_polygon(sVertices,
                              fill='green' if self.altitude > 0 else 'blue',
                              outline='black')


class Map:
    def __init__(self, source):
        # Imports the geometry from a Mapmaker object
        self.cities = {}

        for point in source.pointSet:
            self.cities[point] = City(point, source.vertices[point])

        # Populate adjacency dictionary
        for edge in source.edges:
            if edge[0] != edge[1] and len(source.edges[edge]) > 0:
                self.cities[edge[0]].neighbors.add(self.cities[edge[1]])
                self.cities[edge[1]].neighbors.add(self.cities[edge[0]])

        self.width = source.width
        self.height = source.height

    def randomCity(self):
        # Returns a random city
        return choice(tuple(self.cities.values()))

    def landDump(self, source, size):
        # Uses a BFS floodfill to populate some land provinces
        JAGGEDNESS = 0.25  # The closer to 1 the more jagged

        frontier = [source]
        filled = set()
        while len(filled) < size and len(frontier) > 0:
            city = frontier.pop(0)
            city.altitude = 1
            filled.add(city)
            expands = [neigh for neigh in city.neighbors
                       if neigh not in filled and neigh.altitude < 0]
            # Insert one earlier for some variation
            if random() < JAGGEDNESS:
                if expands:
                    frontier.insert(0, expands.pop())

            frontier += expands

    def spawnLand(self):
        # Randomly distribute some land
        for i in range(3):
            self.landDump(self.randomCity(), 240)
        for i in range(10):
            self.landDump(self.randomCity(), 40)
        for i in range(40):
            target = self.randomCity()
            while not target.isCoastal():
                target = self.randomCity()
            self.landDump(target, 13)

    def draw(self, canvas, data):
        for city in self.cities.values():
            city.draw(canvas, data)
