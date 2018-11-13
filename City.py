# # --- City ---
# #
# # - Contains the City class, and helper functions
# #
# # --- --- --- ---

from Graphics import *
from Geometry import dist

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

    def __hash__(self):
        return hash(self.center)

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

    def draw(self, canvas, data):
        sVertices = [scale(vertex, data) for vertex in self.vertices]
        if data.drawMode == 0:
            if self.altitude > 0:
                color = mixColors(DARK_GRASS, GRASS_COLOR, self.altitude)
            else:
                color = mixColors(DARK_OCEAN, OCEAN_COLOR, -self.altitude)
        elif data.drawMode == 1:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.wetness)
        elif data.drawMode == 2:
            color = mixColors(COLD_COLOR, HOT_COLOR, (self.temp + 1) / 2)
        elif data.drawMode == 3:
            color = mixColors(DRY_COLOR, GRASS_COLOR, self.fertility)
        canvas.create_polygon(sVertices,
                              fill=color,
                              outline='')
