# # --- Terrain ---
# #
# # - Terrain-generating functions
# #
# # --- --- --- ---

from Graphics import *


class Map:
    def __init__(self, source):
        # Imports the geometry from a Mapmaker object
        self.cities = source.pointSet
        self.vertices = source.vertices
        self.width = source.width
        self.height = source.height

        # Populate adjacency dictionary
        self.neighbors = {city: set() for city in self.cities}
        for edge in source.edges:
            if edge[0] != edge[1] and len(source.edges[edge]) > 0:
                for i in range(2):
                    self.neighbors[edge[i]].add(edge[1 - i])

    def draw(self, canvas, data):
        for city in self.cities:
            sVertices = [scale(vertex, data) for vertex
                         in self.vertices[city]]
            canvas.create_polygon(sVertices,
                                  fill='',
                                  outline='black')

            for neighbor in self.neighbors[city]:
                canvas.create_line(scale(city, data), scale(neighbor, data),
                                   fill='red')
